"""Prediction history and journey administration."""

from django.contrib import admin
from django.http import HttpRequest

from .models import Journey, Prediction


@admin.register(Journey)
class JourneyAdmin(admin.ModelAdmin):
    list_display = ("journey_id", "segment", "name", "max_spend_pct")
    search_fields = ("journey_id", "name")
    list_filter = ("segment",)

    def has_delete_permission(self, request: HttpRequest, obj: Journey | None = None) -> bool:
        """FR-SEG-04: journeys may be edited, never deleted in Admin."""
        return False


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ("customer", "model_version", "p_churn", "risk_label", "clv_tier",
                    "value_at_risk", "segment", "channel", "scored_at")
    search_fields = ("customer__customer_id", "model_version")
    list_filter = ("risk_label", "clv_tier", "segment", "channel", "model_version")
    list_select_related = ("customer", "journey")
    raw_id_fields = ("customer",)
    readonly_fields = ("scored_at",)
