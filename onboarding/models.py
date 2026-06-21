"""
Onboarding intake: invitations, submissions, and the normalized answers.

Answers are stored as option *codes* (language-agnostic, queryable) and resolved
to EN/AR labels via the catalog. Each submission also keeps the exact raw payload
JSON for audit, and free-text answers are stored verbatim.
"""
import secrets

from django.db import models

from catalog.models import FormVersion
from partners.models import Partner


def generate_reference():
    return f"BNP-{secrets.token_hex(4).upper()}"


class Invitation(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        OPENED = "opened", "Opened"
        SUBMITTED = "submitted", "Submitted"
        EXPIRED = "expired", "Expired"

    token = models.CharField(max_length=128, unique=True, db_index=True)
    email = models.EmailField(blank=True)       # optional prefill
    full_name = models.CharField(max_length=255, blank=True)
    invited_by = models.CharField(max_length=255, blank=True)  # nomination source
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    locale = models.CharField(max_length=5, default="en")
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.token} ({self.status})"

    def is_open(self):
        from django.utils import timezone
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return self.status != self.Status.EXPIRED


class Submission(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        IN_REVIEW = "in_review", "In review"
        SHORTLISTED = "shortlisted", "Shortlisted"
        ON_HOLD = "on_hold", "On hold"
        DECLINED = "declined", "Declined"

    reference = models.CharField(max_length=24, unique=True, default=generate_reference, editable=False)
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="submissions")
    invitation = models.ForeignKey(Invitation, on_delete=models.SET_NULL, null=True, blank=True, related_name="submissions")
    form_version = models.ForeignKey(FormVersion, on_delete=models.SET_NULL, null=True, blank=True, related_name="submissions")

    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SUBMITTED, db_index=True)
    locale = models.CharField(max_length=5, default="en")

    # Consent acknowledgments (kept as columns for compliance queries).
    ack_intro = models.BooleanField(default=False)
    ack_consent = models.BooleanField(default=False)

    # Exact payload as submitted (immutable audit; survives catalog changes).
    raw_payload = models.JSONField(default=dict, blank=True)

    submitted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.reference} — {self.partner.full_name}"


class Answer(models.Model):
    """One row per selection. single/select/country -> one row (option_code);
    multi -> N rows; ordered -> N rows with rank; text -> text_value; an "Other"
    selection carries the typed value in other_text."""
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="answers")
    question_code = models.CharField(max_length=64, db_index=True)
    option_code = models.CharField(max_length=64, blank=True, db_index=True)
    text_value = models.TextField(blank=True)
    rank = models.PositiveIntegerField(null=True, blank=True)
    other_text = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["question_code", "option_code"]),
        ]
        ordering = ["submission", "question_code", "rank", "id"]

    def __str__(self):
        return f"{self.question_code}={self.option_code or self.text_value[:20]}"
