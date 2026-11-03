from datetime import date

from rest_framework import serializers

from .models import Application


class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = (
            "id", "user", "company", "role_title", "status",
            "applied_date", "deadline", "source", "notes",
            "job_description", "match_score", "created_at",
        )
        # Client can never send these. user comes from the JWT.
        read_only_fields = ("id", "user", "match_score", "created_at")

    def create(self, validated_data):
        # Client sent null or nothing → use today
        if validated_data.get("applied_date") is None:
            validated_data["applied_date"] = date.today()
        return super().create(validated_data)


class ApplicationStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Application.Status.choices)