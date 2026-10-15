"""Database constraints for version activation and concurrent training jobs."""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from .models import ModelVersion, TrainingJob


def version_data(version: str = "churn_v1") -> dict[str, object]:
    """Explicit fixture parameters; production models supply no threshold default."""
    return dict(version=version, model_type="churn", algo="LightGBM", params={}, metrics={},
                threshold=0.186, clv_config={"g": 0.33, "d": 0.1, "horizon": 3, "P33": 143, "P67": 342},
                artifact_path="artifacts/test.joblib", trained_at=timezone.now())


class RegistryTests(TestCase):
    def test_only_one_active_version_and_multiple_inactive(self) -> None:
        ModelVersion.objects.create(**version_data(), is_active=True)
        second = ModelVersion.objects.create(**version_data("churn_v2"))
        ModelVersion.objects.create(**version_data("churn_v3"))
        with self.assertRaises(IntegrityError), transaction.atomic():
            ModelVersion.objects.filter(pk=second.pk).update(is_active=True)
        ModelVersion.objects.filter(pk="churn_v1").update(is_active=False)
        second.is_active = True
        second.save()

    def test_model_type_threshold_and_config(self) -> None:
        ModelVersion(**version_data()).full_clean()
        for changes in ({"model_type": "clv"}, {"threshold": 0.01}, {"threshold": 0.96},
                        {"clv_config": {"g": 0.33}}):
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                ModelVersion(**(version_data() | changes)).full_clean()


class TrainingJobTests(TestCase):
    def test_br07_blocks_every_pair_of_live_statuses(self) -> None:
        for first_status in ("queued", "running"):
            for second_status in ("queued", "running"):
                with self.subTest(first=first_status, second=second_status):
                    first = TrainingJob.objects.create(dataset_path="test.csv", status=first_status)
                    with self.assertRaises(IntegrityError), transaction.atomic():
                        TrainingJob.objects.create(dataset_path="other.csv", status=second_status)
                    first.status = "done"
                    first.save()
        TrainingJob.objects.create(dataset_path="failed.csv", status="failed")
        live = TrainingJob.objects.create(dataset_path="live.csv")
        live.status = "running"
        live.save()
        completed = TrainingJob.objects.filter(status="done").first()
        with self.assertRaises(IntegrityError), transaction.atomic():
            TrainingJob.objects.filter(pk=completed.pk).update(status="queued")

    def test_nullable_fields_choices_progress_and_log(self) -> None:
        job = TrainingJob(dataset_path="test.csv")
        job.full_clean()
        job.save()
        for field in ("started_at", "finished_at", "result_version", "created_by"):
            self.assertIsNone(getattr(job, field))
        for changes in ({"status": "invalid"}, {"progress": -0.1}, {"progress": 1.1}, {"log": {"bad": 1}}):
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                TrainingJob(dataset_path="test.csv", **changes).full_clean(validate_constraints=False)
        other = TrainingJob(dataset_path="other.csv")
        job.log.append("started")
        self.assertEqual(other.log, [])
