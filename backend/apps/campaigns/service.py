"""BR-08 → BR-10: chọn khách và tính kết quả kỳ vọng của một chiến dịch. Dùng chung cho preview và export."""
from itertools import accumulate

from rest_framework import serializers

from apps.customers.models import COUNTRY_CITIES
from apps.customers.views import filtered

SEGMENTS = ["S1", "S2", "S3", "S4", "S5", "S6"]


def number(minimum, maximum=None, **kwargs):
    """FloatField báo lỗi tiếng Việt (bản dịch vi của DRF chưa đủ)."""
    message = f"Phải từ {minimum} đến {maximum}." if maximum is not None else f"Phải lớn hơn hoặc bằng {minimum}."
    return serializers.FloatField(min_value=minimum, max_value=maximum, required=False, **kwargs,
                                  error_messages={"min_value": message, "max_value": message, "invalid": "Phải là số."})


class CampaignParams(serializers.Serializer):
    """FR-CAMP-01: budget null = không giới hạn; spend_pct null = k của từng phân khúc (BR-08)."""
    segments = serializers.ListField(child=serializers.ChoiceField(SEGMENTS), default=["S1", "S2"],
                                     allow_empty=False, error_messages={"empty": "Chọn ít nhất một phân khúc."})
    country = serializers.ChoiceField(list(COUNTRY_CITIES), allow_null=True, required=False, default=None,
                                      error_messages={"invalid_choice": "Quốc gia không hợp lệ."})
    city = serializers.CharField(allow_null=True, required=False, default=None)
    budget = number(0.01, allow_null=True, default=None)
    spend_pct = number(0.001, 1, allow_null=True, default=None)
    success_rate = number(0.01, 1, default=0.20)

    def validate(self, data):
        if data["city"] and data["city"] not in COUNTRY_CITIES.get(data["country"], ()):
            raise serializers.ValidationError({"city": "Thành phố không thuộc quốc gia đã chọn."})
        return data


def eligible(params):
    """Khách khớp bộ lọc, VaR giảm dần (cùng thứ tự với /customers để export cắt đúng phần đầu)."""
    return filtered({"segment": ",".join(params["segments"]), "country": params["country"],
                     "city": params["city"]})


def plan(params):
    """BR-09: lấy lần lượt theo VaR giảm dần; có ngân sách B thì dừng ở khách đầu tiên làm tổng chi phí vượt B.

    Trả (queryset đủ điều kiện, danh sách (segment, VaR, chi phí) của khách được chọn theo đúng thứ tự).
    """
    qs = eligible(params)
    k = params["spend_pct"]
    rows = [(seg, var, (k if k is not None else (seg_k or 0)) * clv)
            for seg, var, clv, seg_k in qs.values_list("segment", "value_at_risk", "clv_potential",
                                                        "journey__max_spend_pct")]
    if params["budget"] is not None:
        n = sum(1 for total in accumulate(cost for *_, cost in rows) if total <= params["budget"] + 1e-9)
        rows = rows[:n]  # tổng tích lũy tăng dần nên đếm được = độ dài phần đầu thỏa ngân sách
    return qs, rows


def preview(params):
    """BR-10: VaR giữ lại = s × Σ VaR; ROI = (giữ lại − chi phí) / chi phí; hòa vốn = chi phí / Σ VaR."""
    qs, rows = plan(params)
    cost = sum(c for *_, c in rows)
    var = sum(v for _, v, _ in rows)
    saved = params["success_rate"] * var
    by_segment = {seg: {"segment": seg, "selected": 0, "cost": 0.0, "value_at_risk": 0.0} for seg in params["segments"]}
    for seg, v, c in rows:
        s = by_segment[seg]
        s["selected"] += 1
        s["cost"] += c
        s["value_at_risk"] += v
    for s in by_segment.values():
        s["cost"], s["value_at_risk"] = round(s["cost"], 2), round(s["value_at_risk"], 2)
    return {
        "eligible": qs.count(), "selected": len(rows),
        "total_cost": round(cost, 2), "total_value_at_risk": round(var, 2), "expected_saved": round(saved, 2),
        "roi": (saved - cost) / cost if cost else None,  # không chia cho 0 khi không có khách / chi phí 0
        "break_even_rate": cost / var if var else None,
        "by_segment": list(by_segment.values()),
        "is_estimate": True,
    }
