"""Model metadata and training job persistence, independent of job execution."""

import uuid

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class ModelVersion(models.Model):
    """DB owns thresholds; referenced versions are protected to retain history."""

    class ModelType(models.TextChoices):
        CHURN = "churn"

    version = models.CharField(primary_key=True, max_length=100)
    model_type = models.CharField(max_length=16, choices=ModelType)
    algo = models.CharField(max_length=100)
    params = models.JSONField(default=dict, blank=True)
    metrics = models.JSONField(default=dict, blank=True)
    threshold = models.FloatField(validators=[MinValueValidator(0.05), MaxValueValidator(0.95)])
    clv_config = models.JSONField()
    artifact_path = models.CharField(max_length=1024)
    is_active = models.BooleanField(default=False)
    trained_at = models.DateTimeField()

    class Meta:
        db_table = "model_registry"
        indexes = [models.Index(fields=["model_type", "is_active"], name="model_type_active_idx")]
        constraints = [models.UniqueConstraint(fields=["model_type"],
                       condition=models.Q(is_active=True), name="one_active_version_per_type")]

    def __str__(self) -> str:
        return self.version

    def clean(self) -> None:
        """Require the agreed CLV keys without supplying business defaults."""
        super().clean()
        if not isinstance(self.clv_config, dict) or not {"g", "d", "horizon", "P33", "P67"} <= self.clv_config.keys():
            raise ValidationError({"clv_config": "Cần các khóa g, d, horizon, P33, P67."})


class TrainingJob(models.Model):
    """BR-07: a partial unique index on constant 1 allows only one live job.

    Protect result versions for audit; deleting a user only clears ownership.
    """

    class Status(models.TextChoices):
        QUEUED = "queued"
        RUNNING = "running"
        DONE = "done"
        FAILED = "failed"

    job_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=7, choices=Status, default=Status.QUEUED)
    dataset_path = models.CharField(max_length=1024)
    current_step = models.CharField(max_length=100, blank=True)
    progress = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(1)])
    log = models.JSONField(default=list, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    result_version = models.ForeignKey("models_mgmt.ModelVersion", on_delete=models.PROTECT,
                                      null=True, blank=True, related_name="training_jobs")
    created_by = models.ForeignKey("auth.User", on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name="training_jobs")

    class Meta:
        db_table = "training_jobs"
        indexes = [models.Index(fields=["status"], name="training_jobs_status_idx")]
        constraints = [models.UniqueConstraint(models.Value(1),
                       condition=models.Q(status__in=["queued", "running"]),
                       name="one_unfinished_training_job")]

    def __str__(self) -> str:
        return f"{self.job_id} ({self.status})"

    def clean(self) -> None:
        """Job logs are ordered JSON lists, as specified by the API."""
        super().clean()
        if not isinstance(self.log, list):
            raise ValidationError({"log": "Phải là danh sách."})
