"""FR-DASH: tổng quan tệp khách và độ tin cậy mô hình. Mọi số aggregate ở DB (< 2 giây với 50.000 khách)."""
from django.db.models import Count, F, IntegerField, Max, Q, Sum, Value
from django.db.models.functions import Floor, Least
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ml_engine.src.segment import SEGMENTS
from . import service
from .models import Journey

ALGORITHMS = {"lightgbm": "LightGBM", "random_forest": "Random Forest", "logreg": "Logistic Regression"}
LIMITATIONS = [
    "Dữ liệu tổng hợp, chưa kiểm chứng trên khách thật.",
    "Giả định nhãn Churned ứng với chu kỳ 1 năm.",
    "CLV chưa trừ chi phí phục vụ từng khách (CSKH, vận chuyển).",
    "Khách trong tập train có p_churn hơi lạc quan vì mô hình đã thấy dữ liệu này.",
]


def thresholds(config):
    return {"tau": config["tau"], "clv_p33": config["P33"], "clv_p67": config["P67"]}


@api_view(["GET"])
def dashboard_summary(request):
    config = service.config()
    qs = service.active_predictions()
    if country := request.query_params.get("country"):
        qs = qs.filter(customer__country=country)

    totals = qs.aggregate(n=Count("id"), high=Count("id", filter=Q(risk_label="High")),
                          clv=Sum("clv_pred"), var=Sum("value_at_risk"), scored_at=Max("scored_at"))
    n, var = totals["n"], totals["var"] or 0
    by_segment = {r["segment"]: r for r in qs.values("segment").annotate(count=Count("id"), var=Sum("value_at_risk"))}
    names = dict(Journey.objects.values_list("segment", "name"))
    segments = [
        {"segment": seg, "name": names.get(seg, seg), "risk": risk, "tier": tier,
         "count": by_segment.get(seg, {}).get("count", 0),
         "share": by_segment.get(seg, {}).get("count", 0) / n if n else 0,
         "value_at_risk": round(by_segment.get(seg, {}).get("var") or 0, 2)}
        for (risk, tier), seg in sorted(SEGMENTS.items(), key=lambda kv: kv[1])
    ]
    # bin 0..9; p_churn = 1.0 rơi vào bin cuối
    bins = dict(qs.annotate(bin=Least(Floor(F("p_churn") * 10), Value(9), output_field=IntegerField())).values("bin")
                .annotate(count=Count("id")).values_list("bin", "count"))
    histogram = [{"bin": f"{i / 10:.1f}-{(i + 1) / 10:.1f}", "count": bins.get(i, 0)} for i in range(10)]
    by_country = [{"country": r["customer__country"], "count": r["count"], "value_at_risk": round(r["var"], 2)}
                  for r in qs.values("customer__country").annotate(count=Count("id"), var=Sum("value_at_risk"))
                  .order_by("-var")]

    return Response({
        "total_customers": n,
        "high_risk_rate": totals["high"] / n if n else 0,
        "total_clv_expected": round(totals["clv"] or 0, 2),
        "total_value_at_risk": round(var, 2),
        "model": {"version": config["version"], "scored_at": totals["scored_at"]},
        "thresholds": thresholds(config),
        "segments": segments,
        "p_churn_histogram": histogram,
        "by_country": by_country,
    })


@api_view(["GET"])
def model_info(request):
    config = service.config()
    m = config["metrics"]
    return Response({
        "version": config["version"],
        "algorithm": f"{ALGORITHMS.get(service.bundle()['algo'], service.bundle()['algo'])} (isotonic)",
        "trained_at": config["trained_at"][:10],
        "metrics": {"roc_auc": m["roc_auc"], "recall": m["recall"], "precision": m["precision"]},
        "plain_text": [
            f"Trong 100 khách thực sự rời đi, mô hình phát hiện {round(m['recall'] * 100)}.",
            f"Trong 100 khách bị gắn rủi ro cao, {round(m['precision'] * 100)} thực sự rời đi.",
        ],
        "thresholds": thresholds(config),
        "global_importance": config["global_importance"],
        "limitations": LIMITATIONS,
    })


# FR-SEG-01: nguồn nghiên cứu theo docs/06 mục 2 (nội dung tĩnh, không sửa qua Admin)
RESEARCH = {
    "S1": ["Lemmens & Gupta 2020", "Knox & van Oest 2014", "Thomas et al. 2004"],
    "S2": ["Baymard 2025", "Anderson & Simester 2004"],
    "S3": ["Reinartz & Kumar 2002", "Kumar et al. 2015"],
    "S4": ["Drèze & Nunes 2009", "Schmitt et al. 2011"],
    "S5": ["Shah et al. 2012", "Drèze & Nunes 2009"],
    "S6": ["Reinartz & Kumar 2002"],
}


@api_view(["GET"])
def journeys(request):
    """FR-SEG-01: 6 lộ trình kèm điều kiện (BR-04), số khách, tổng VaR; ngưỡng chỉ đọc."""
    stats = {r["segment"]: r for r in service.active_predictions().values("segment")
             .annotate(count=Count("id"), var=Sum("value_at_risk"))}
    condition = {seg: {"risk": risk, "tier": tier} for (risk, tier), seg in SEGMENTS.items()}
    return Response({
        "thresholds": thresholds(service.config()),
        "journeys": [
            {"journey_id": j.journey_id, "segment": j.segment, "name": j.name, **condition[j.segment],
             "count": stats.get(j.segment, {}).get("count", 0),
             "value_at_risk": round(stats.get(j.segment, {}).get("var") or 0, 2),
             "goal": j.goal, "steps": j.steps, "kpi": j.kpi, "max_spend_pct": j.max_spend_pct,
             "research": RESEARCH.get(j.segment, [])}
            for j in Journey.objects.order_by("segment")
        ],
    })
