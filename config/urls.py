from django.contrib import admin
from django.urls import path, include
from exhibition import views as exhibition_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", exhibition_views.redirect_after_login, name="home"),
    path("leader/dashboard/", exhibition_views.leader_dashboard, name="leader_dashboard"),
    path(
        "leader/api/status/",
        exhibition_views.leader_status_api,
        name="leader_status_api",
    ),
    path(
        "leader/api/all-booths-status/",
        exhibition_views.all_booths_status_api,
        name="all_booths_status_api",
    ),
    path("exhibition-admin/dashboard/", exhibition_views.admin_dashboard, name="admin_dashboard"),
    path(
        "exhibition-admin/api/booth-status/",
        exhibition_views.admin_booth_status_api,
        name="admin_booth_status_api",
    ),
    path(
        "booths/<int:booth_id>/enter/",
        exhibition_views.enter_booth,
        name="enter_booth",
    ),
    path(
        "booths/<int:booth_id>/exit/",
        exhibition_views.exit_booth,
        name="exit_booth",
    ),
    path(
        "exhibition-admin/booths/<int:booth_id>/kick/<int:user_id>/",
        exhibition_views.admin_force_exit,
        name="admin_force_exit",
    ),
    # CRUD لیدرها
    path(
        "exhibition-admin/leaders/",
        exhibition_views.leader_list,
        name="leader_list",
    ),
    path(
        "exhibition-admin/leaders/create/",
        exhibition_views.leader_create,
        name="leader_create",
    ),
    path(
        "exhibition-admin/leaders/<int:user_id>/edit/",
        exhibition_views.leader_edit,
        name="leader_edit",
    ),
    path(
        "exhibition-admin/leaders/<int:user_id>/delete/",
        exhibition_views.leader_delete,
        name="leader_delete",
    ),
    path(
        "exhibition-admin/leaders/<int:user_id>/reset-password/",
        exhibition_views.leader_reset_password,
        name="leader_reset_password",
    ),
]