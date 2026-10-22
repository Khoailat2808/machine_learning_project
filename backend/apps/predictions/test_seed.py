"""scripts/seed_db.py: upsert không trùng, giữ nội dung lộ trình đã sửa, dữ liệu ghi vào hợp lệ với model."""

import sys
from pathlib import Path
from unittest import skipUnless

import pandas as pd
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase

from apps.customers.models import Customer
from .models import Journey, Prediction

REPO = Path(settings.REPO_DIR)
ARTIFACTS = Path(settings.ARTIFACT_DIR)
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.seed_db import load_artifacts, seed  # noqa: E402  (cần REPO trong sys.path)

USERS = [("admin", "test-only-password", True), ("marketer", "test-only-password", False)]


@skipUnless(Path(settings.DATASET_PATH).exists() and (ARTIFACTS / "top_reasons.json.gz").exists(),
            "cần CSV gốc và artifact (python -m ml_engine.src.train)")
class SeedTests(TestCase):
    N = 300

    @classmethod
    def setUpTestData(cls) -> None:
        cls.df = pd.read_csv(settings.DATASET_PATH, nrows=cls.N)
        cls.config, _, cls.reasons = load_artifacts(ARTIFACTS)
        seed(cls.df, ARTIFACTS, USERS)

    def test_counts_and_rerun_is_idempotent(self) -> None:
        Journey.objects.filter(pk="J1").update(name="Đã sửa trong Admin")
        seed(self.df, ARTIFACTS, [(u, "other-password", a) for u, _, a in USERS])
        self.assertEqual(Customer.objects.count(), self.N)
        self.assertEqual(Prediction.objects.count(), self.N)
        self.assertEqual(Journey.objects.count(), 6)
        self.assertEqual(Journey.objects.get(pk="J1").name, "Đã sửa trong Admin")
        self.assertTrue(User.objects.get(username="admin").check_password("test-only-password"))
        self.assertTrue(User.objects.get(username="admin").is_superuser)
        self.assertFalse(User.objects.get(username="marketer").is_staff)

    def test_rows_are_valid_and_linked(self) -> None:
        for customer in Customer.objects.all():
            customer.full_clean()
        for i, prediction in enumerate(Prediction.objects.select_related("journey").order_by("customer_id")):
            prediction.full_clean()
            self.assertEqual(prediction.customer_id, f"CUS{i + 1:05d}")
            self.assertEqual(prediction.model_version, self.config["version"])
            self.assertEqual(prediction.journey.segment, prediction.segment)
            self.assertEqual(prediction.top_reasons, self.reasons[i])
        for journey in Journey.objects.all():
            journey.full_clean()

    def test_out_of_domain_inputs_are_fixed_like_clean_transformer(self) -> None:
        bad = self.df.head(1).copy()
        bad[["Age", "Total_Purchases", "Discount_Usage_Rate"]] = [200, -3, 116.6]
        seed(bad, ARTIFACTS, USERS)
        c = Customer.objects.get(pk="CUS00001")
        self.assertEqual((c.age, c.total_purchases, c.discount_usage_rate), (None, 0, 100))
        c.full_clean()
