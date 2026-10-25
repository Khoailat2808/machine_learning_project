"""FR-DASH: /dashboard/summary và /model/info."""
from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from apps.customers.models import Customer
from apps.customers.tests import customer_data
from . import service
from .models import Prediction

# (country, city, p_churn, segment, clv_pred, value_at_risk)
ROWS = [("USA", "Houston", 0.82, "S1", 500.0, 400.0),
        ("USA", "Chicago", 1.0, "S2", 100.0, 150.5),
        ("UK", "London", 0.05, "S6", 50.0, 2.25)]


def make_predictions(rows=ROWS, version=None):
    version = version or service.config()["version"]
    for i, (country, city, p, seg, clv, var) in enumerate(rows, 1):
        customer = Customer.objects.create(**{**customer_data(), "customer_id": f"CUS{i:05d}",
                                              "country": country, "city": city})
        risk = "High" if seg in ("S1", "S2", "S3") else "Low"
        Prediction.objects.create(customer=customer, model_version=version, p_churn=p, risk_label=risk,
                                  clv_pred=clv, clv_potential=clv * 2, clv_tier="High", value_at_risk=var,
                                  segment=seg, channel="Email")


class DashboardTests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(User.objects.create_user("marketer"))

    def test_requires_token(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/v1/dashboard/summary").status_code, 401)
        self.assertEqual(self.client.get("/api/v1/model/info").status_code, 401)

    def test_summary_totals_match_matrix_and_histogram(self):
        make_predictions()
        Prediction.objects.create(**{**Prediction.objects.values().first(), "id": None,
                                     "model_version": "churn_v0"})  # version cũ không được tính
        body = self.client.get("/api/v1/dashboard/summary").json()

        self.assertEqual(body["total_customers"], 3)
        self.assertAlmostEqual(body["high_risk_rate"], 2 / 3)
        self.assertEqual(body["total_clv_expected"], 650.0)
        self.assertEqual(body["total_value_at_risk"], 552.75)
        self.assertEqual([s["segment"] for s in body["segments"]], ["S1", "S2", "S3", "S4", "S5", "S6"])
        self.assertEqual(sum(s["count"] for s in body["segments"]), body["total_customers"])
        self.assertAlmostEqual(sum(s["value_at_risk"] for s in body["segments"]), body["total_value_at_risk"])
        self.assertEqual(body["segments"][0]["risk"], "High")
        self.assertEqual(body["segments"][0]["tier"], "High")

        histogram = [b["count"] for b in body["p_churn_histogram"]]
        self.assertEqual(histogram, [1, 0, 0, 0, 0, 0, 0, 0, 1, 1])  # 0.05, 0.82, 1.0 → bin cuối
        self.assertEqual(body["by_country"][0], {"country": "USA", "count": 2, "value_at_risk": 550.5})
        self.assertEqual(body["thresholds"]["tau"], service.config()["tau"])

    def test_country_filter(self):
        make_predictions()
        body = self.client.get("/api/v1/dashboard/summary?country=UK").json()
        self.assertEqual(body["total_customers"], 1)
        self.assertEqual(body["total_value_at_risk"], 2.25)

    def test_empty_db_no_division_error(self):
        body = self.client.get("/api/v1/dashboard/summary").json()
        self.assertEqual(body["total_customers"], 0)
        self.assertEqual(body["high_risk_rate"], 0)
        self.assertTrue(all(s["share"] == 0 for s in body["segments"]))

    def test_model_info_plain_text(self):
        body = self.client.get("/api/v1/model/info").json()
        recall = round(service.config()["metrics"]["recall"] * 100)
        self.assertIn(f"phát hiện {recall}.", body["plain_text"][0])
        self.assertEqual(body["algorithm"], "LightGBM (isotonic)")
        self.assertEqual(len(body["global_importance"]), 10)
