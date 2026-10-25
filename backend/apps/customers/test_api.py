"""FR-CUS: /customers, /customers/export, /customers/{id}."""
import csv
import io

from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from apps.predictions import service
from apps.predictions.models import Journey, Prediction
from .models import Customer
from .tests import customer_data

REASON = [{"feature": "Customer_Service_Calls", "label": "Số lần gọi CSKH", "value": 12, "avg": 5.7, "shap": 0.2}]
# (country, city, segment, p_churn, clv_potential, value_at_risk)
ROWS = [("USA", "Houston", "S1", 0.9, 1000.0, 900.0),
        ("USA", "Chicago", "S1", 0.5, 800.0, 400.0),
        ("USA", "Houston", "S2", 0.7, 200.0, 140.0),
        ("UK", "London", "S1", 0.8, 900.0, 720.0),
        ("UK", "Leeds", "S6", 0.1, 50.0, 5.0)]


class CustomerApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        version = service.config()["version"]
        journeys = {s: Journey.objects.create(journey_id=f"J{s[1]}", segment=s, name=f"Lộ trình {s}", goal="g",
                                              kpi="k", max_spend_pct=0.1 if s == "S1" else 0.05)
                    for s in ("S1", "S2", "S6")}
        for i, (country, city, seg, p, clv, var) in enumerate(ROWS, 1):
            c = Customer.objects.create(**{**customer_data(), "customer_id": f"CUS{i:05d}",
                                           "country": country, "city": city, "customer_service_calls": 12})
            Prediction.objects.create(customer=c, model_version=version, p_churn=p,
                                      risk_label="High" if p >= 0.5 else "Low", clv_pred=clv / 2, clv_potential=clv,
                                      clv_tier="High", value_at_risk=var, segment=seg, channel="Email",
                                      journey=journeys[seg], top_reasons=REASON)
        Prediction.objects.create(customer_id="CUS00005", model_version="churn_v0", p_churn=0.99, risk_label="High",
                                  clv_pred=1, clv_potential=1, clv_tier="Low", value_at_risk=1, segment="S3",
                                  channel="Email")  # version cũ: không bao giờ xuất hiện

    def setUp(self):
        self.client.force_authenticate(User.objects.create_user("marketer"))

    def ids(self, query=""):
        return [r["customer_id"] for r in self.client.get(f"/api/v1/customers{query}").json()["results"]]

    def test_requires_token(self):
        self.client.force_authenticate(None)
        for url in ("/api/v1/customers", "/api/v1/customers/export", "/api/v1/customers/CUS00001"):
            self.assertEqual(self.client.get(url).status_code, 401)

    def test_default_sort_var_desc_and_row_shape(self):
        body = self.client.get("/api/v1/customers").json()
        self.assertEqual(body["count"], 5)
        self.assertEqual([r["customer_id"] for r in body["results"]],
                         ["CUS00001", "CUS00004", "CUS00002", "CUS00003", "CUS00005"])
        self.assertEqual(set(body["results"][0]), {"customer_id", "country", "city", "p_churn", "risk_label",
                                                   "clv_pred", "clv_potential", "clv_tier", "value_at_risk",
                                                   "segment"})

    def test_filters_combine_with_and(self):
        expected = Prediction.objects.filter(model_version=service.config()["version"], segment="S1",
                                             customer__country="USA").count()
        self.assertEqual(len(self.ids("?segment=S1&country=USA")), expected)
        self.assertEqual(self.ids("?segment=S1,S2&city=Houston"), ["CUS00001", "CUS00003"])
        self.assertEqual(self.ids("?risk=Low"), ["CUS00005"])
        self.assertEqual(self.ids("?q=00004"), ["CUS00004"])
        self.assertEqual(self.ids("?segment=S4"), [])

    def test_sort(self):
        self.assertEqual(self.ids("?sort=p_churn")[0], "CUS00005")
        self.assertEqual(self.ids("?sort=-clv_potential")[0], "CUS00001")
        self.assertEqual(self.ids("?sort=Age")[0], "CUS00001")  # không cho sort tùy ý → mặc định

    def test_export_csv_matches_filter(self):
        res = self.client.get("/api/v1/customers/export?segment=S1")
        self.assertEqual(res.status_code, 200)
        self.assertIn("attachment;", res["Content-Disposition"])
        text = res.content.decode("utf-8")
        self.assertTrue(text.startswith("﻿"))
        rows = list(csv.DictReader(io.StringIO(text.lstrip("﻿"))))
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["customer_id"], "CUS00001")
        self.assertEqual(rows[0]["journey"], "Lộ trình S1")
        self.assertEqual(float(rows[0]["expected_cost"]), 100.0)  # 10% × 1000
        self.assertEqual(rows[0]["top_reason"], "Số lần gọi CSKH")

    def test_detail(self):
        body = self.client.get("/api/v1/customers/CUS00001").json()
        self.assertEqual(sum(len(g) for g in body["attributes"].values()), 23)
        self.assertEqual(body["attributes"]["engagement"]["Customer_Service_Calls"], 12)
        self.assertIsNone(body["attributes"]["profile"]["Age"])  # trường tùy chọn để trống
        self.assertEqual(body["prediction"]["segment"], "S1")
        self.assertEqual(body["prediction"]["top_reasons"], REASON)
        self.assertEqual(body["journey"]["name"], "Lộ trình S1")

    def test_detail_404(self):
        res = self.client.get("/api/v1/customers/CUS99999")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["detail"], "Không tìm thấy khách hàng.")
