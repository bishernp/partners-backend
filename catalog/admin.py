from django.contrib import admin

from .models import FormVersion, Option, Question


class OptionInline(admin.TabularInline):
    model = Option
    extra = 0


@admin.register(FormVersion)
class FormVersionAdmin(admin.ModelAdmin):
    list_display = ("version", "is_active", "created_at")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("code", "type", "screen", "order", "required", "max_select", "form_version")
    list_filter = ("form_version", "screen", "type", "required")
    search_fields = ("code", "label_en", "label_ar")
    inlines = [OptionInline]
