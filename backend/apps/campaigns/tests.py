"""FR-CAMP: preview khớp tính tay, ngân sách, CSV = selected, bộ lọc rỗng không chia cho 0."""
import csv
import io

from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from apps.predictions.models import Prediction
from apps.predictions.test_api import make_journeys, make_predictions

# (country, city, p_churn, segment, clv_pred, value_at_risk); clv_potential = 2 × clv_pred
ROWS = [("USA", "Houston", 0.9, "S1", 500.0, 400.0),  # chi phí 10% × 1000 = 100
        ("USA", "Chicago", 0.8, "S1", 300.0, 300.0),  # 60
        ("UK", "London", 0.7, "S2", 200.0, 350.0),    # 5% × 400 = 20
        ("UK", "Leeds", 0.1, "S6", 50.0, 5.0)]


class CampaignTests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(User.objects.create_user("marketer"))
        make_journeys()
        make_predictions(ROWS)
        for p in Prediction.objects.select_related("customer"):
            p.journey_id = f"J{p.segment[1]}"
            p.save()

    def post(self, url, **body):
        return self.client.post(f"/api/v1/campaigns/{url}", body, format="json")

    def test_requires_token(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.post("preview").status_code, 401)

    def test_preview_matches_hand_calculation(self):
        body = self.post("preview").json()  # mặc định S1 + S2, s = 20%
        self.assertEqual((body["eligible"], body["selected"]), (3, 3))
        self.assertEqual(body["total_cost"], 180.0)
        self.assertEqual(body["total_value_at_risk"], 1050.0)
        self.assertEqual(body["expected_saved"], 210.0)
        self.assertAlmostEqual(body["roi"], (210 - 180) / 180)
        self.assertAlmostEqual(body["break_even_rate"], 180 / 1050)
        self.assertEqual(body["by_segment"][1], {"segment": "S2", "selected": 1, "cost": 20.0, "value_at_risk": 350.0})
        self.assertTrue(body["is_estimate"])

    def test_budget_takes_highest_var_and_stays_under_budget(self):
        body = self.post("preview", budget=130).json()
        # VaR giảm dần: 400 (100) → 350 (20) → 300 (60, vượt 130 → dừng)
        self.assertEqual((body["selected"], body["total_cost"], body["total_value_at_risk"]), (2, 120.0, 750.0))

    def test_spend_pct_override_and_filters(self):
        body = self.post("preview", segments=["S1", "S2"], country="UK", spend_pct=0.5, success_rate=1).json()
        self.assertEqual((body["selected"], body["total_cost"]), (1, 200.0))

    def test_empty_selection_no_division_by_zero(self):
        body = self.post("preview", segments=["S3"]).json()
        self.assertEqual((body["selected"], body["roi"], body["break_even_rate"]), (0, None, None))

    def test_invalid_params(self):
        r = self.post("preview", segments=[], success_rate=2)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(set(r.json()["errors"]), {"segments", "success_rate"})
        r = self.post("preview", country="USA", city="London")
        self.assertEqual(r.json()["errors"], {"city": "Thành phố không thuộc quốc gia đã chọn."})

    def test_export_rows_equal_selected(self):
        r = self.post("export", budget=130, spend_pct=None)
        self.assertEqual(r["Content-Type"], "text/csv; charset=utf-8")
        rows = list(csv.DictReader(io.StringIO(r.content.decode("utf-8-sig"))))
        self.assertEqual([x["customer_id"] for x in rows], ["CUS00001", "CUS00003"])
        self.assertEqual([x["expected_cost"] for x in rows], ["100.0", "20.0"])
        r = self.post("export", segments=["S1"], spend_pct=0.5)
        self.assertEqual(r.content.decode("utf-8-sig").splitlines()[1].split(",")[9], "500.0")
