from datetime import date

from django.conf import settings
from django.db import models


class Application(models.Model):
    class Status(models.TextChoices):
        APPLIED = "Applied"
        SCREENING = "Screening"
        INTERVIEW = "Interview"
        OFFER = "Offer"
        ACCEPTED = "Accepted"
        REJECTED = "Rejected"

    # Deleting a user deletes their applications (cascade, like FastAPI)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="applications",
    )
    company = models.CharField(max_length=150)
    role_title = models.CharField(max_length=150)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.APPLIED)
    applied_date = models.DateField(default=date.today, null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    source = models.CharField(max_length=50, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    job_description = models.TextField(null=True, blank=True)
    match_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]                      # newest first
        indexes = [models.Index(fields=["user", "status"])]    # fast filter per user + stage

    def __str__(self):
        return f"{self.company} - {self.role_title}"

class FollowUp(models.Model):
    # Deleting an application deletes its follow-ups (cascade)
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="followups",
    )
    followup_date = models.DateField()
    note = models.CharField(max_length=255, null=True, blank=True)
    is_done = models.BooleanField(default=False)
    reminder_sent = models.BooleanField(default=False)   # used by email reminders later

    class Meta:
        ordering = ["followup_date", "id"]
        indexes = [models.Index(fields=["is_done", "followup_date"])]   # fast "due soon" query

    def __str__(self):
        return f"{self.application.company} - {self.followup_date}"