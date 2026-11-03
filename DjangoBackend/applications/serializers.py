from datetime import date

from rest_framework import serializers

from .models import Application, FollowUp


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


class FollowUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = FollowUp
        fields = ("id", "application", "followup_date", "note", "is_done", "reminder_sent")
        # application comes from the URL, reminder_sent is set by the system only
        read_only_fields = ("id", "application", "reminder_sent")

    def update(self, instance, validated_data):
        # Date moved → reminder email must fire again for the new date
        new_date = validated_data.get("followup_date")
        if new_date and new_date != instance.followup_date:
            validated_data["reminder_sent"] = False
        return super().update(instance, validated_data)


class UpcomingFollowUpSerializer(FollowUpSerializer):
    # Extra info so the dashboard shows "Acme Corp · Backend Developer"
    company = serializers.CharField(source="application.company", read_only=True)
    role_title = serializers.CharField(source="application.role_title", read_only=True)

    class Meta(FollowUpSerializer.Meta):
        fields = FollowUpSerializer.Meta.fields + ("company", "role_title")