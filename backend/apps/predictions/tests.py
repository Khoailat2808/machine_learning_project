"""Linked model persistence, prediction history and Admin access."""

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.urls import reverse

from apps.customers.models import Customer
from apps.customers.tests import customer_data
from .models import Journey, Prediction


class PredictionTests(TestCase):
    def setUp(self) -> None:
        self.customer = Customer.objects.create(**customer_data())
        self.version = "churn_v1"
        self.journey = Journey.objects.create(journey_id="J1", segment="S1", name="VIP nguy cơ", goal="Giữ lại",
                                             steps=[{"day": 0, "channel": "Phone", "action": "Call", "offer": None}],
                                             kpi="Mua lại 30 ngày", max_spend_pct=0.1)
        self.prediction_data = dict(customer=self.customer, model_version=self.version,
                                    p_churn=0.8, risk_label="High", clv_pred=100,
                                    clv_potential=500, clv_tier="High", value_at_risk=400,
                                    segment="S1", channel="Phone", journey=self.journey)

    def test_models_link_and_preserve_history(self) -> None:
        prediction = Prediction(**self.prediction_data)
        prediction.full_clean()
        prediction.save()
        self.journey.full_clean()
        for instance in (self.customer, self.journey, prediction):
            instance.refresh_from_db()
            self.assertTrue(str(instance))
        self.assertEqual(prediction.customer, self.customer)
        self.assertEqual(prediction.journey, self.journey)
        self.assertIsNone(prediction.top_reasons)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Prediction.objects.create(**self.prediction_data)
        Prediction.objects.create(**(self.prediction_data | {"model_version": "churn_v2"}))
        self.assertEqual(self.customer.predictions.count(), 2)
        with self.assertRaises(ProtectedError):
            self.journey.delete()
        self.customer.delete()
        self.assertEqual(Prediction.objects.count(), 0)

    def test_choices_nulls_and_journey_unique_segment(self) -> None:
        Prediction(**(self.prediction_data | {"journey": None})).full_clean()
        for changes in ({"risk_label": "high"}, {"clv_tier": "Medium"}, {"segment": "S7"},
                        {"p_churn": -0.1}, {"p_churn": 1.1}, {"channel": "Fax"}):
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                Prediction(**(self.prediction_data | changes)).full_clean()
        journey = dict(journey_id="J2", segment="S2", name="Test", goal="Giữ lại", kpi="KPI", max_spend_pct=0.05)
        Journey(**journey).full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Journey.objects.create(**(journey | {"segment": "S1"}))
        for changes in ({"journey_id": "J7"}, {"segment": "S7"}, {"steps": [{}]}, {"max_spend_pct": 1.5}):
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                Journey(**(journey | changes)).full_clean()

    def test_admin_lists_and_forms_for_all_models(self) -> None:
        Prediction.objects.create(**self.prediction_data)
        admin = User.objects.create_superuser("admin_test", password="test-only-password")
        self.client.force_login(admin)
        models = (("customers", Customer), ("predictions", Journey), ("predictions", Prediction))
        for app, model in models:
            prefix = f"admin:{app}_{model._meta.model_name}"
            with self.subTest(model=model.__name__):
                self.assertEqual(self.client.get(reverse(f"{prefix}_changelist")).status_code, 200)
                self.assertEqual(self.client.get(reverse(f"{prefix}_add")).status_code, 200)
                obj = model.objects.first()
                self.assertEqual(self.client.get(reverse(f"{prefix}_change", args=[obj.pk])).status_code, 200)

    def test_active_predictions_only_current_version(self) -> None:
        from . import service

        Prediction.objects.create(**self.prediction_data)
        Prediction.objects.create(**{**self.prediction_data, "model_version": "churn_v0"})
        self.assertEqual(service.config()["version"], self.version)
        self.assertEqual(list(service.active_predictions().values_list("model_version", flat=True)), [self.version])
