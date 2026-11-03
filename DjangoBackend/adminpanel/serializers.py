from rest_framework import serializers

from accounts.models import User
from applications.models import Application


class AdminUserSerializer(serializers.ModelSerializer):
    applications_count = serializers.IntegerField(read_only=True)   # comes from annotate()
    # Django calls it date_joined. We expose created_at so the frontend stays the same.
    created_at = serializers.DateTimeField(source="date_joined", read_only=True)

    class Meta:
        model = User
        fields = ("id", "name", "email", "role", "is_active", "created_at", "applications_count")
        # No password field. Never leak it, not even to admins.


class AdminUserStatusSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()


class AdminApplicationSerializer(serializers.ModelSerializer):
    # Summary only. No notes / job_description (user's private data)
    class Meta:
        model = Application
        fields = ("id", "user", "company", "role_title", "status", "applied_date", "source", "created_at")