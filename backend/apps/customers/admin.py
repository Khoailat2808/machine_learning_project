"""Customer administration."""

from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("customer_id", "country", "city", "source", "created_at")
    search_fields = ("customer_id", "country", "city")
    list_filter = ("country", "source", "signup_quarter")
    readonly_fields = ("created_at",)
