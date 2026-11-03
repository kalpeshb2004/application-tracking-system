from django.contrib import admin

from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("company", "role_title", "status", "user", "applied_date")
    list_filter = ("status",)
    search_fields = ("company", "role_title", "user__email")