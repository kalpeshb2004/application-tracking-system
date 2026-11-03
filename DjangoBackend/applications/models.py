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