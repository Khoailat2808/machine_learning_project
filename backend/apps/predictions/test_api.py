"""FR-DASH: /dashboard/summary và /model/info."""
from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from apps.customers.models import Customer
from apps.customers.tests import customer_data
from . import service
from .models import Journey, Prediction

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


def make_journeys():
    from scripts.seed_db import JOURNEYS
    for j in JOURNEYS:
        Journey.objects.create(**j)


class JourneyTests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(User.objects.create_user("marketer"))
        make_journeys()

    def test_six_journeys_with_stats_and_thresholds(self):
        make_predictions()
        body = self.client.get("/api/v1/journeys").json()
        self.assertEqual([j["segment"] for j in body["journeys"]], ["S1", "S2", "S3", "S4", "S5", "S6"])
        s1 = body["journeys"][0]
        self.assertEqual((s1["risk"], s1["tier"], s1["count"], s1["value_at_risk"]), ("High", "High", 1, 400.0))
        self.assertEqual(s1["max_spend_pct"], 0.10)
        self.assertTrue(s1["research"])
        self.assertEqual(body["journeys"][3]["count"], 0)  # S4 không có khách
        self.assertEqual(body["thresholds"]["clv_p67"], service.config()["P67"])


# FR-PRED: 9 trường bắt buộc; 14 trường tùy chọn bỏ trống
REQUIRED = {"Gender": "Female", "Country": "UK", "City": "London", "Signup_Quarter": "Q2", "Membership_Years": 1.5,
            "Login_Frequency": 8, "Cart_Abandonment_Rate": 65.0, "Total_Purchases": 7, "Average_Order_Value": 95.5}


class PredictTests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(User.objects.create_user("marketer"))
        make_journeys()

    def test_optional_fields_empty_still_scores(self):
        r = self.client.post("/api/v1/predict", REQUIRED, format="json")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(len(body["imputed_fields"]), 14)
        self.assertEqual(body["journey"]["name"], Journey.objects.get(segment=body["segment"]).name)
        self.assertFalse(body["saved"])
        self.assertEqual(Customer.objects.count(), 0)  # không bấm lưu thì không ghi DB

    def test_same_p_churn_as_batch_score(self):
        import pandas as pd
        from ml_engine.src.segment import score
        from ml_engine.src.clean import NUMERIC_COLS
        row = {**REQUIRED, "Age": 34, "Customer_Service_Calls": 12, "Email_Open_Rate": 5.0}
        df = pd.DataFrame([{c: row.get(c) for c in [*NUMERIC_COLS, "Gender", "Country", "City", "Signup_Quarter"]}])
        df[NUMERIC_COLS] = df[NUMERIC_COLS].astype(float)
        expected = score(df, service.bundle(), service.config())["p_churn"].iloc[0]
        body = self.client.post("/api/v1/predict", row, format="json").json()
        self.assertAlmostEqual(body["p_churn"], expected, delta=0.001)
        self.assertLessEqual(len(body["top_reasons"]), 3)

    def test_invalid_fields_return_400_by_column(self):
        r = self.client.post("/api/v1/predict", {**REQUIRED, "Age": 200, "City": "Paris", "Gender": None},
                             format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(set(r.json()["errors"]), {"Age", "City", "Gender"})

    def test_save_creates_customer_and_prediction(self):
        make_predictions()  # CUS00001..3 đã có
        r = self.client.post("/api/v1/predict?save=true", REQUIRED, format="json")
        self.assertEqual(r.status_code, 201)
        body = r.json()
        self.assertEqual((body["saved"], body["customer_id"]), (True, "CUS00004"))
        p = Prediction.objects.get(customer_id="CUS00004")
        self.assertEqual((p.customer.source, p.segment, p.model_version),
                         ("form", body["segment"], service.config()["version"]))
        detail = self.client.get("/api/v1/customers/CUS00004")
        self.assertEqual(detail.status_code, 200)
