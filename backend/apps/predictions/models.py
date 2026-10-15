"""Stored scoring results and marketing journeys; no scoring service here."""

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models


class Segment(models.TextChoices):
    S1 = "S1"
    S2 = "S2"
    S3 = "S3"
    S4 = "S4"
    S5 = "S5"
    S6 = "S6"


class Journey(models.Model):
    """Journey content; prediction references protect it from deletion."""

    journey_id = models.CharField(primary_key=True, max_length=2,
                                 validators=[RegexValidator(r"^J[1-6]$")])
    segment = models.CharField(max_length=2, choices=Segment, unique=True)
    name = models.CharField(max_length=200)
    steps = models.JSONField(default=list, blank=True)
    kpi = models.TextField()

    class Meta:
        db_table = "journeys"

    def __str__(self) -> str:
        return f"{self.journey_id}: {self.name}"

    def clean(self) -> None:
        """Require a list of steps with the API's four named fields."""
        super().clean()
        if not isinstance(self.steps, list) or any(
            not isinstance(step, dict) or not {"day", "channel", "action", "offer"} <= step.keys()
            for step in self.steps
        ):
            raise ValidationError({"steps": "Mỗi bước cần day, channel, action, offer."})


class Prediction(models.Model):
    """Customer deletion cascades; protect version/journey to preserve history."""

    class Risk(models.TextChoices):
        HIGH = "High"
        LOW = "Low"

    class Tier(models.TextChoices):
        LOW = "Low"
        MID = "Mid"
        HIGH = "High"

    customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE, related_name="predictions")
    model_version = models.ForeignKey("models_mgmt.ModelVersion", on_delete=models.PROTECT,
                                      related_name="predictions")
    p_churn = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(1)])
    risk_label = models.CharField(max_length=4, choices=Risk)
    clv_pred = models.FloatField(validators=[MinValueValidator(0)])
    clv_potential = models.FloatField(validators=[MinValueValidator(0)])
    clv_tier = models.CharField(max_length=4, choices=Tier)
    value_at_risk = models.FloatField(validators=[MinValueValidator(0)])
    segment = models.CharField(max_length=2, choices=Segment)
    journey = models.ForeignKey("predictions.Journey", on_delete=models.PROTECT,
                               null=True, blank=True, related_name="predictions")
    top_reasons = models.JSONField(null=True, blank=True)
    scored_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "predictions"
        unique_together = [("customer", "model_version")]
        indexes = [models.Index(fields=["segment"], name="predictions_segment_idx"),
                   models.Index(fields=["value_at_risk"], name="predictions_var_idx"),
                   models.Index(fields=["risk_label"], name="predictions_risk_idx")]

    def __str__(self) -> str:
        return f"{self.customer_id} / {self.model_version_id}"
