from django.contrib import admin

from .models import Booth, BoothVisit


@admin.register(Booth)
class BoothAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "max_groups")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(BoothVisit)
class BoothVisitAdmin(admin.ModelAdmin):
    list_display = ("booth", "leader", "is_active", "entered_at", "exited_at")
    list_filter = ("booth", "is_active")
    search_fields = ("leader__username",)

