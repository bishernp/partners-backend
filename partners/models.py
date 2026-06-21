"""
The Partner: the person being onboarded. This is the anchor the future portal
will hang off (accounts, engagements, activities), so identity/contact lives
here as typed columns. The questionnaire answers live in onboarding.Answer.
"""
from django.db import models


class Partner(models.Model):
    # "Your details" screen — identity & contact.
    full_name = models.CharField(max_length=255)
    honorific = models.CharField(max_length=32, blank=True)   # option code (e.g. "dr")
    email = models.EmailField(db_index=True)
    mobile = models.CharField(max_length=64, blank=True)
    based_in = models.CharField(max_length=255, blank=True)   # free text
    nationality = models.CharField(max_length=8, blank=True)  # ISO 3166-1 alpha-2 (e.g. "SA")
    linkedin = models.URLField(max_length=512, blank=True)
    locale = models.CharField(max_length=5, default="en")     # locale used at submission

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Future portal: user = models.OneToOneField(settings.AUTH_USER_MODEL, ...)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} <{self.email}>"
