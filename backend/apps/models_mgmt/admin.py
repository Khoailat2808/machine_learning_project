"""Registry and training job administration."""

from django.contrib import admin

from .models import ModelVersion, TrainingJob


@admin.register(ModelVersion)
class ModelVersionAdmin(admin.ModelAdmin):
    list_display = ("version", "model_type", "algo", "threshold", "is_active", "trained_at")
    search_fields = ("version", "algo")
    list_filter = ("model_type", "is_active", "algo")


@admin.register(TrainingJob)
class TrainingJobAdmin(admin.ModelAdmin):
    list_display = ("job_id", "status", "current_step", "progress", "started_at", "result_version")
    search_fields = ("job_id", "dataset_path", "result_version__version", "created_by__username")
    list_filter = ("status",)
    list_select_related = ("result_version", "created_by")
    readonly_fields = ("job_id",)
