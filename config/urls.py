from django.contrib import admin
from django.urls import path, include
from exhibition import views  # همه viewها از اینجا import می‌شن

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", views.redirect_after_login, name="home"),
    path("leader/dashboard/", views.leader_dashboard, name="leader_dashboard"),
    path(
        "leader/api/status/",
        views.leader_status_api,
        name="leader_status_api",
    ),
    path(
        "leader/api/all-booths-status/",
        views.all_booths_status_api,
        name="all_booths_status_api",
    ),
    path("exhibition-admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path(
        "exhibition-admin/api/booth-status/",
        views.admin_booth_status_api,
        name="admin_booth_status_api",
    ),
    path(
        "booths/<int:booth_id>/enter/",
        views.enter_booth,
        name="enter_booth",
    ),
    path(
        "booths/<int:booth_id>/exit/",
        views.exit_booth,
        name="exit_booth",
    ),
    path(
        "exhibition-admin/booths/<int:booth_id>/kick/<int:user_id>/",
        views.admin_force_exit,
        name="admin_force_exit",
    ),
    # CRUD لیدرها
    path(
        "exhibition-admin/leaders/",
        views.leader_list,
        name="leader_list",
    ),
    path(
        "exhibition-admin/leaders/create/",
        views.leader_create,
        name="leader_create",
    ),
    path(
        "exhibition-admin/leaders/<int:user_id>/edit/",
        views.leader_edit,
        name="leader_edit",
    ),
    path(
        "exhibition-admin/leaders/<int:user_id>/delete/",
        views.leader_delete,
        name="leader_delete",
    ),
    path(
        "exhibition-admin/leaders/<int:user_id>/reset-password/",
        views.leader_reset_password,
        name="leader_reset_password",
    ),

    # مسیرهای تیک‌باکس (قبلی)
    path('leader/toggle-check/<int:booth_id>/', views.toggle_booth_check, name='toggle_booth_check'),
    path('leader/checked-booths/', views.get_checked_booths, name='get_checked_booths'),
    path('leader/reset-all-checks/', views.reset_all_booth_checks, name='reset_all_booth_checks'),

    
]