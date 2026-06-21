from rest_framework import serializers

from onboarding.models import Submission


class SubmissionListSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="partner.full_name")
    email = serializers.CharField(source="partner.email")
    nationality = serializers.CharField(source="partner.nationality")

    class Meta:
        model = Submission
        fields = ["id", "reference", "full_name", "email", "nationality", "status", "locale", "submitted_at"]
