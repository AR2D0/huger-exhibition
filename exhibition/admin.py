from django.contrib import admin
from .models import Booth, BoothVisit, LeaderBoothStatus


@admin.register(Booth)
class BoothAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "max_groups")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(BoothVisit)
class BoothVisitAdmin(admin.ModelAdmin):
    list_display = ("booth", "leader", "is_active", "entered_at", "exited_at")
    list_filter = ("booth", "is_active")
    search_fields = ("leader__username",)

@admin.register(LeaderBoothStatus)
class LeaderBoothStatusAdmin(admin.ModelAdmin):
    list_display = ('leader', 'booth', 'is_checked', 'checked_at')
    list_filter = ('is_checked', 'leader', 'booth')
    search_fields = ('leader__username', 'booth__name')
    ordering = ('-checked_at',)
