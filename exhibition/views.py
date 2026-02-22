from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group, User
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Booth, BoothVisit


def _safe_broadcast_capacity_update(booth_id: int) -> None:
    """
    Broadcast capacity updates via Redis/WebSocket.

    Important: the enter/exit actions must NOT fail if Redis is down.
    """
    try:
        _broadcast_capacity_update(booth_id=booth_id)
    except Exception:
        # اگر Redis/Channels در دسترس نبود، عملیات ورود/خروج نباید fail شود.
        # (در محیط پروداکشن بهتر است اینجا logging اضافه شود.)
        return


def is_leader(user) -> bool:
    return user.groups.filter(name="leaders").exists()


def is_exhibition_admin(user) -> bool:
    return user.groups.filter(name="exhibition_admins").exists()


@login_required
def redirect_after_login(request: HttpRequest) -> HttpResponse:
    user = request.user
    
    # اولویت اول: اگر superuser باشد → همیشه به Django Admin کلاسیک برود
    if user.is_superuser:
        return redirect("/admin/")  # یا redirect("admin:index")
    
    # اگر در گروه exhibition_admins باشد → به داشبورد سفارشی
    if is_exhibition_admin(user):
        return redirect("admin_dashboard")
    
    # اگر leader باشد
    if is_leader(user):
        return redirect("leader_dashboard")
    
    # بقیه کاربرها → به صفحه لاگین
    return redirect("login")


@login_required
@user_passes_test(is_leader)
def leader_dashboard(request: HttpRequest) -> HttpResponse:
    booths = Booth.objects.all().order_by("id")
    active_visits = {
        v.booth_id
        for v in BoothVisit.objects.filter(leader=request.user, is_active=True)
    }

    booth_data: list[dict] = []
    for booth in booths:
        occupied = BoothVisit.objects.filter(booth=booth, is_active=True).count()
        remaining = max(booth.max_groups - occupied, 0)
        booth_data.append(
            {
                "id": booth.id,
                "name": booth.name,
                "max": booth.max_groups,
                "occupied": occupied,
                "remaining": remaining,
                "is_user_inside": booth.id in active_visits,
            }
        )

    context = {"booths": booth_data}
    return render(request, "exhibition/leader_dashboard.html", context)


@login_required
@user_passes_test(is_leader)
def leader_status_api(request: HttpRequest) -> JsonResponse:
    """
    API برای لیدر: وضعیت حضور خودش در غرفه‌ها را برمی‌گرداند.
    """
    active_visits = BoothVisit.objects.filter(
        leader=request.user, is_active=True
    ).values_list("booth_id", flat=True)
    
    return JsonResponse({"active_booth_ids": list(active_visits)})


@login_required
@user_passes_test(is_leader)
def all_booths_status_api(request: HttpRequest) -> JsonResponse:
    """
    API جدید برای polling: وضعیت فعلی همه غرفه‌ها را برای لیدرها برمی‌گرداند
    """
    booths = Booth.objects.all().order_by("id")
    result = []
    for booth in booths:
        occupied = BoothVisit.objects.filter(booth=booth, is_active=True).count()
        remaining = max(booth.max_groups - occupied, 0)
        result.append({
            "id": booth.id,
            "occupied": occupied,
            "remaining": remaining,
            "max": booth.max_groups,
        })
    return JsonResponse({"booths": result})


def _broadcast_capacity_update(booth_id: int) -> None:
    channel_layer = get_channel_layer()
    booth = Booth.objects.get(pk=booth_id)
    occupied = BoothVisit.objects.filter(booth=booth, is_active=True).count()
    remaining = max(booth.max_groups - occupied, 0)

    active_visits = (
        BoothVisit.objects.filter(booth=booth, is_active=True)
        .select_related("leader")
    )
    
    leaders = [
        {"username": v.leader.username, "id": v.leader.id}
        for v in active_visits
    ]

    async_to_sync(channel_layer.group_send)(
        "capacity_updates",
        {
            "type": "capacity.update",
            "booth_id": booth.id,
            "booth_name": booth.name,
            "occupied": occupied,
            "remaining": remaining,
            "leaders": leaders,
        },
    )


@login_required
@user_passes_test(is_leader)
def enter_booth(request: HttpRequest, booth_id: int) -> JsonResponse:
    booth = get_object_or_404(Booth, pk=booth_id)

    if request.method != "POST":
        return JsonResponse({"error": "درخواست نامعتبر است."}, status=400)

    user = request.user

    with transaction.atomic():
        active_visits_for_user = (
            BoothVisit.objects.select_for_update()
            .filter(leader=user, is_active=True)
        )

        if active_visits_for_user.exists():
            return JsonResponse(
                {"error": "شما هم‌اکنون در یک غرفه‌ی دیگر حضور دارید."},
                status=400,
            )

        active_visits_for_booth = (
            BoothVisit.objects.select_for_update()
            .filter(booth=booth, is_active=True)
        )
        current_occupied = active_visits_for_booth.count()

        if current_occupied >= booth.max_groups:
            return JsonResponse(
                {"error": "این غرفه پر است."},
                status=400,
            )

        BoothVisit.objects.create(
            booth=booth,
            leader=user,
            is_active=True,
        )

    _safe_broadcast_capacity_update(booth_id=booth.id)

    return JsonResponse(
        {"success": True, "booth_id": booth.id},
        status=200,
    )


@login_required
@user_passes_test(is_leader)
def exit_booth(request: HttpRequest, booth_id: int) -> JsonResponse:
    booth = get_object_or_404(Booth, pk=booth_id)

    if request.method != "POST":
        return JsonResponse({"error": "درخواست نامعتبر است."}, status=400)

    user = request.user

    with transaction.atomic():
        try:
            visit = (
                BoothVisit.objects.select_for_update()
                .get(booth=booth, leader=user, is_active=True)
            )
        except BoothVisit.DoesNotExist:
            return JsonResponse(
                {"error": "شما در حال حاضر داخل این غرفه ثبت نشده‌اید."},
                status=400,
            )

        visit.is_active = False
        visit.exited_at = timezone.now()
        visit.save()

    _safe_broadcast_capacity_update(booth_id=booth.id)

    return JsonResponse(
        {"success": True, "booth_id": booth.id},
        status=200,
    )


@login_required
@user_passes_test(is_exhibition_admin)
def admin_dashboard(request: HttpRequest) -> HttpResponse:
    booths = Booth.objects.all().order_by("id")
    data: list[dict] = []
    for booth in booths:
        active_visits = (
            BoothVisit.objects.filter(booth=booth, is_active=True)
            .select_related("leader")
            .order_by("leader__username")
        )
        occupied = active_visits.count()
        remaining = max(booth.max_groups - occupied, 0)
        leaders = [v.leader for v in active_visits]
        data.append(
            {
                "booth": booth,
                "occupied": occupied,
                "remaining": remaining,
                "leaders": leaders,
            }
        )

    context = {"booth_status": data}
    return render(request, "exhibition/admin_dashboard.html", context)


@login_required
@user_passes_test(is_exhibition_admin)
def admin_booth_status_api(request: HttpRequest) -> JsonResponse:
    """
    API ساده برای داشبورد ادمین (polling fallback یا رفرش دوره‌ای).
    """
    booths = Booth.objects.all().order_by("id")
    result: list[dict] = []
    for booth in booths:
        active_visits = (
            BoothVisit.objects.filter(booth=booth, is_active=True)
            .select_related("leader")
            .order_by("leader__username")
        )
        occupied = active_visits.count()
        remaining = max(booth.max_groups - occupied, 0)
        leaders = [
            {"username": v.leader.username, "id": v.leader.id}
            for v in active_visits
        ]
        result.append(
            {
                "id": booth.id,
                "name": booth.name,
                "max_groups": booth.max_groups,
                "occupied": occupied,
                "remaining": remaining,
                "leaders": leaders,
            }
        )

    return JsonResponse({"booths": result})


@login_required
@user_passes_test(is_exhibition_admin)
def admin_force_exit(
    request: HttpRequest, booth_id: int, user_id: int
) -> HttpResponse:
    if request.method != "POST":
        return JsonResponse({"error": "درخواست نامعتبر است."}, status=400)

    booth = get_object_or_404(Booth, pk=booth_id)
    leader = get_object_or_404(Group.objects.get(name="leaders").user_set, pk=user_id)

    with transaction.atomic():
        visits = (
            BoothVisit.objects.select_for_update()
            .filter(booth=booth, leader=leader, is_active=True)
        )
        if not visits.exists():
            return JsonResponse(
                {"error": "این لیدر در حال حاضر داخل این غرفه ثبت نشده است."},
                status=400,
            )

        now = timezone.now()
        for v in visits:
            v.is_active = False
            v.exited_at = now
            v.save()

    _safe_broadcast_capacity_update(booth_id=booth.id)

    return JsonResponse({"success": True}, status=200)


# ========== CRUD برای لیدرها ==========


@login_required
@user_passes_test(is_exhibition_admin)
def leader_list(request: HttpRequest) -> HttpResponse:
    """لیست همه لیدرها"""
    leaders_group = Group.objects.get(name="leaders")
    leaders = leaders_group.user_set.all().order_by("username")
    
    leader_data = []
    for leader in leaders:
        active_visits = BoothVisit.objects.filter(leader=leader, is_active=True).count()
        leader_data.append({
            "id": leader.id,
            "username": leader.username,
            "is_active": leader.is_active,
            "active_visits": active_visits,
        })
    
    context = {"leaders": leader_data}
    return render(request, "exhibition/leader_list.html", context)


@login_required
@user_passes_test(is_exhibition_admin)
def leader_create(request: HttpRequest) -> HttpResponse | JsonResponse:
    """افزودن لیدر جدید"""
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        
        if not username or not password:
            return JsonResponse(
                {"error": "نام کاربری و رمز عبور الزامی است."},
                status=400,
            )
        
        if User.objects.filter(username=username).exists():
            return JsonResponse(
                {"error": "این نام کاربری قبلاً استفاده شده است."},
                status=400,
            )
        
        leaders_group = Group.objects.get(name="leaders")
        user = User.objects.create_user(username=username, password=password)
        user.groups.add(leaders_group)
        
        return JsonResponse({"success": True, "leader_id": user.id}, status=200)
    
    return render(request, "exhibition/leader_form.html", {"leader": None})


@login_required
@user_passes_test(is_exhibition_admin)
def leader_edit(request: HttpRequest, user_id: int) -> HttpResponse | JsonResponse:
    """ویرایش لیدر"""
    leader = get_object_or_404(User, pk=user_id)
    leaders_group = Group.objects.get(name="leaders")
    
    if leader not in leaders_group.user_set.all():
        return JsonResponse(
            {"error": "این کاربر یک لیدر نیست."},
            status=400,
        )
    
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        
        if not username:
            return JsonResponse(
                {"error": "نام کاربری الزامی است."},
                status=400,
            )
        
        if username != leader.username and User.objects.filter(username=username).exists():
            return JsonResponse(
                {"error": "این نام کاربری قبلاً استفاده شده است."},
                status=400,
            )
        
        leader.username = username
        if password:
            leader.set_password(password)
        leader.save()
        
        return JsonResponse({"success": True}, status=200)
    
    context = {"leader": leader}
    return render(request, "exhibition/leader_form.html", context)


@login_required
@user_passes_test(is_exhibition_admin)
def leader_delete(request: HttpRequest, user_id: int) -> JsonResponse:
    """حذف لیدر"""
    if request.method != "POST":
        return JsonResponse({"error": "درخواست نامعتبر است."}, status=400)
    
    leader = get_object_or_404(User, pk=user_id)
    leaders_group = Group.objects.get(name="leaders")
    
    if leader not in leaders_group.user_set.all():
        return JsonResponse(
            {"error": "این کاربر یک لیدر نیست."},
            status=400,
        )
    
    active_visits = BoothVisit.objects.filter(leader=leader, is_active=True)
    booth_ids_to_update = set()
    for visit in active_visits:
        booth_ids_to_update.add(visit.booth_id)
        visit.is_active = False
        visit.exited_at = timezone.now()
        visit.save()
    
    for booth_id in booth_ids_to_update:
        _safe_broadcast_capacity_update(booth_id=booth_id)
    
    leader.delete()
    
    return JsonResponse({"success": True}, status=200)


@login_required
@user_passes_test(is_exhibition_admin)
def leader_reset_password(request: HttpRequest, user_id: int) -> JsonResponse:
    """ریست رمز عبور لیدر"""
    if request.method != "POST":
        return JsonResponse({"error": "درخواست نامعتبر است."}, status=400)
    
    leader = get_object_or_404(User, pk=user_id)
    leaders_group = Group.objects.get(name="leaders")
    
    if leader not in leaders_group.user_set.all():
        return JsonResponse(
            {"error": "این کاربر یک لیدر نیست."},
            status=400,
        )
    
    new_password = request.POST.get("password", "").strip()
    if not new_password:
        return JsonResponse(
            {"error": "رمز عبور جدید الزامی است."},
            status=400,
        )
    
    leader.set_password(new_password)
    leader.save()
    
    return JsonResponse({"success": True}, status=200)