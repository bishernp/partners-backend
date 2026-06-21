from django.contrib import admin

from .models import Answer, Invitation, Submission


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ("question_code", "option_code", "text_value", "rank", "other_text")
    can_delete = False


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("reference", "partner", "status", "locale", "submitted_at")
    list_filter = ("status", "locale", "form_version")
    search_fields = ("reference", "partner__full_name", "partner__email")
    readonly_fields = ("reference", "raw_payload", "submitted_at", "updated_at")
    inlines = [AnswerInline]


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("token", "email", "full_name", "status", "locale", "created_at")
    list_filter = ("status", "locale")
    search_fields = ("token", "email", "full_name")
