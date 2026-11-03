from django.contrib import admin

from .models import Application, FollowUp


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("company", "role_title", "status", "user", "applied_date")
    list_filter = ("status",)
    search_fields = ("company", "role_title", "user__email")


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ("application", "followup_date", "is_done", "reminder_sent")
    list_filter = ("is_done",)