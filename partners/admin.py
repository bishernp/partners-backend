from django.contrib import admin

from .models import Partner


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "nationality", "based_in", "created_at")
    search_fields = ("full_name", "email", "mobile")
    list_filter = ("nationality", "locale")
    readonly_fields = ("created_at", "updated_at")
