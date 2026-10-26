"""FR-CUS: danh sách, lọc, xuất CSV và hồ sơ khách. Chỉ đọc prediction của version đang dùng."""
import csv
from datetime import date

from django.db.models import F
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from apps.predictions import service
from .models import Customer

SORTS = {"p_churn", "clv_potential", "value_at_risk"}
FILTERS = {"risk": "risk_label", "tier": "clv_tier", "country": "customer__country", "city": "customer__city"}

# FR-CUS-03: 23 thuộc tính theo nhóm, khóa là tên cột gốc (docs/07)
GROUPS = {
    "profile": ["Age", "Gender", "Country", "City", "Signup_Quarter", "Membership_Years"],
    "behavior": ["Login_Frequency", "Session_Duration_Avg", "Pages_Per_Session", "Mobile_App_Usage",
                 "Wishlist_Items", "Cart_Abandonment_Rate"],
    "purchase": ["Total_Purchases", "Average_Order_Value", "Days_Since_Last_Purchase", "Discount_Usage_Rate",
                 "Returns_Rate", "Payment_Method_Diversity", "Credit_Balance"],
    "engagement": ["Email_Open_Rate", "Customer_Service_Calls", "Product_Reviews_Written",
                   "Social_Media_Engagement_Score"],
}
FIELD_OF = {f.db_column: f.name for f in Customer._meta.fields if f.db_column}

# FR-CAMP-03: cột CSV dùng chung cho xuất khách hàng và xuất chiến dịch
CSV_COLUMNS = ["customer_id", "country", "city", "segment", "journey", "channel", "p_churn",
               "clv_potential", "value_at_risk", "expected_cost", "top_reason"]


def filtered(params):
    """FR-CUS-02: lọc AND, segment nhiều giá trị dạng S1,S2; sort ngoài danh sách cho phép → mặc định VaR giảm dần."""
    qs = service.active_predictions()
    if segments := params.get("segment"):
        qs = qs.filter(segment__in=segments.split(","))
    for param, field in FILTERS.items():
        if value := params.get(param):
            qs = qs.filter(**{field: value})
    if q := params.get("q", "").strip():
        qs = qs.filter(customer__pk__icontains=q)
    sort = params.get("sort", "-value_at_risk")
    if sort.lstrip("-") not in SORTS:
        sort = "-value_at_risk"
    return qs.order_by(sort, "customer_id")


def csv_response(predictions, filename, spend_pct=None):
    """UTF-8 có BOM để Excel đọc đúng tiếng Việt. Chi phí dự kiến = k × CLV tiềm năng (BR-08);
    k của phân khúc, hoặc spend_pct nếu chiến dịch ghi đè."""
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("﻿")
    writer = csv.writer(response)
    writer.writerow(CSV_COLUMNS)
    rows = predictions.values_list("customer_id", "customer__country", "customer__city", "segment", "journey__name",
                                   "channel", "p_churn", "clv_potential", "value_at_risk", "journey__max_spend_pct",
                                   "top_reasons")
    for *head, p, clv, var, k, reasons in rows.iterator(chunk_size=2000):
        writer.writerow([*head, round(p, 4), round(clv, 2), round(var, 2), round((spend_pct if spend_pct is not None else k or 0) * clv, 2),
                         reasons[0]["label"] if reasons else ""])
    return response


@api_view(["GET"])
def customer_list(request):
    rows = filtered(request.query_params).values(
        "customer_id", "p_churn", "risk_label", "clv_pred", "clv_potential", "clv_tier", "value_at_risk", "segment",
        country=F("customer__country"), city=F("customer__city"))
    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(rows, request)
    for r in page:
        r["p_churn"] = round(r["p_churn"], 4)
        for key in ("clv_pred", "clv_potential", "value_at_risk"):
            r[key] = round(r[key], 2)
    return paginator.get_paginated_response(page)


@api_view(["GET"])
def customer_export(request):
    return csv_response(filtered(request.query_params), f"khach_hang_{date.today():%Y%m%d}.csv")


@api_view(["GET"])
def customer_detail(request, customer_id):
    p = service.active_predictions().select_related("customer", "journey").filter(customer_id=customer_id).first()
    if p is None:
        raise NotFound("Không tìm thấy khách hàng.")
    c, j = p.customer, p.journey
    return Response({
        "customer_id": c.customer_id,
        "attributes": {group: {col: getattr(c, FIELD_OF[col]) for col in cols} for group, cols in GROUPS.items()},
        "prediction": {
            "p_churn": round(p.p_churn, 4), "risk_label": p.risk_label,
            "clv_pred": round(p.clv_pred, 2), "clv_potential": round(p.clv_potential, 2), "clv_tier": p.clv_tier,
            "value_at_risk": round(p.value_at_risk, 2), "segment": p.segment, "channel": p.channel,
            "top_reasons": p.top_reasons or [], "model_version": p.model_version, "scored_at": p.scored_at,
        },
        "journey": j and {"journey_id": j.journey_id, "name": j.name, "goal": j.goal, "steps": j.steps,
                          "kpi": j.kpi, "max_spend_pct": j.max_spend_pct},
    })
