"""FR-PRED-01–03: chấm 1 khách mới bằng cùng score() với seed (BR-01–07), lưu khi ?save=true."""
import pandas as pd
from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.customers.models import Customer
from ml_engine.src.segment import score
from . import service
from .models import Journey, Prediction

FIELD_OF = {f.db_column: f.name for f in Customer._meta.fields if f.db_column}  # tên cột gốc → field
SCORE_FIELDS = ("risk_label", "clv_tier", "segment", "channel")
MONEY_FIELDS = ("clv_pred", "clv_potential", "value_at_risk")


def validate(data):
    """Validate bằng chính model Customer (miền FR-PRED, City thuộc Country); lỗi trả theo tên cột gốc."""
    customer = Customer(source=Customer.Source.FORM, **{f: data.get(col) for col, f in FIELD_OF.items()})
    try:
        customer.full_clean(exclude=["customer_id"])
    except ValidationError as e:
        column = {f: col for col, f in FIELD_OF.items()}
        errors = {column.get(f, f): " ".join(msgs) for f, msgs in e.message_dict.items()}
        return None, errors
    return customer, None


def next_customer_id():
    # ponytail: max theo thứ tự chuỗi, đúng tới CUS99999; quá 5 chữ số thì đổi sang sequence
    last = Customer.objects.order_by("-customer_id").values_list("customer_id", flat=True).first()
    return f"CUS{int(last[3:]) + 1 if last else 1:05d}"


@api_view(["POST"])
def predict(request):
    if not isinstance(request.data, dict):
        return Response({"errors": {"body": "Cần một object JSON với 23 trường."}}, status=400)
    customer, errors = validate(request.data)
    if errors:
        return Response({"errors": errors}, status=400)

    config = service.config()
    df = pd.DataFrame([{col: getattr(customer, f) for col, f in FIELD_OF.items()}])
    df = df.astype({col: float for col in df.columns if col not in ("Gender", "Country", "City", "Signup_Quarter")})
    row = score(df, service.bundle(), config, explain=True).iloc[0]
    journey = Journey.objects.filter(segment=row["segment"]).first()

    result = {
        "p_churn": round(float(row["p_churn"]), 4),
        **{k: round(float(row[k]), 2) for k in MONEY_FIELDS},
        **{k: row[k] for k in SCORE_FIELDS},
        "journey": journey and {"journey_id": journey.journey_id, "name": journey.name, "goal": journey.goal,
                                "steps": journey.steps, "kpi": journey.kpi, "max_spend_pct": journey.max_spend_pct},
        "top_reasons": row["top_reasons"],
        "imputed_fields": row["imputed_fields"],
        "model_version": config["version"],
        "saved": False,
        "customer_id": None,
    }
    if request.query_params.get("save") == "true":
        with transaction.atomic():
            customer.customer_id = next_customer_id()
            customer.save()
            Prediction.objects.create(customer=customer, model_version=config["version"], journey=journey,
                                      p_churn=result["p_churn"], top_reasons=result["top_reasons"],
                                      **{k: result[k] for k in (*MONEY_FIELDS, *SCORE_FIELDS)})
        result.update(saved=True, customer_id=customer.customer_id)
    return Response(result, status=201 if result["saved"] else 200)
