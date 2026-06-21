"""
Bilingual question/option catalog.

This mirrors the hardcoded frontend schema (partners-frontend/src/data/partners.js)
and is the source of truth for EN/AR labels and for server-side validation of
submissions. It is seeded via `manage.py seed_catalog` from an exported JSON, so
the frontend stays the single place questions are authored; the backend just maps
to it. Versioned so old submissions remain readable when questions change.
"""
from django.db import models


class FormVersion(models.Model):
    version = models.CharField(max_length=40, unique=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.version}{' (active)' if self.is_active else ''}"

    @classmethod
    def active(cls):
        return cls.objects.filter(is_active=True).order_by("-created_at").first()


class Question(models.Model):
    class Type(models.TextChoices):
        SINGLE = "single", "Single choice"
        MULTI = "multi", "Multiple choice"
        ORDERED = "ordered", "Ordered (ranked)"
        TEXT = "text", "Text"
        EMAIL = "email", "Email"
        TEL = "tel", "Telephone"
        URL = "url", "URL"
        COUNTRY = "country", "Country"
        SELECT = "select", "Select"

    form_version = models.ForeignKey(FormVersion, on_delete=models.CASCADE, related_name="questions")
    code = models.CharField(max_length=64)
    type = models.CharField(max_length=16, choices=Type.choices)
    screen = models.CharField(max_length=64, blank=True)
    order = models.PositiveIntegerField(default=0)
    required = models.BooleanField(default=False)
    max_select = models.PositiveIntegerField(null=True, blank=True)
    has_other = models.BooleanField(default=False)
    label_en = models.CharField(max_length=512, blank=True)
    label_ar = models.CharField(max_length=512, blank=True)
    help_en = models.CharField(max_length=512, blank=True)
    help_ar = models.CharField(max_length=512, blank=True)

    class Meta:
        ordering = ["form_version", "order"]
        constraints = [
            models.UniqueConstraint(fields=["form_version", "code"], name="uniq_question_per_version"),
        ]

    def __str__(self):
        return f"{self.code} ({self.type})"

    @property
    def is_choice(self):
        return self.type in {self.Type.SINGLE, self.Type.MULTI, self.Type.ORDERED, self.Type.SELECT, self.Type.COUNTRY}


class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    code = models.CharField(max_length=64)
    order = models.PositiveIntegerField(default=0)
    label_en = models.CharField(max_length=512, blank=True)
    label_ar = models.CharField(max_length=512, blank=True)

    class Meta:
        ordering = ["question", "order"]
        constraints = [
            models.UniqueConstraint(fields=["question", "code"], name="uniq_option_per_question"),
        ]

    def __str__(self):
        return f"{self.question.code}:{self.code}"
