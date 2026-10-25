"""Model và clv_config.json đang active: nạp một lần mỗi process, dùng chung cho mọi view (NFR-01).

Ngưỡng (τ, P33, P67) và tham số CLV chỉ đọc từ đây, không hard-code (FRD mục 3).
Train lại xong phải khởi động lại Django để nạp version mới.
"""
import json
from functools import cache
from pathlib import Path

import joblib
from django.conf import settings

from .models import Prediction


@cache
def config() -> dict:
    return json.loads((Path(settings.ARTIFACT_DIR) / "clv_config.json").read_text(encoding="utf-8"))


@cache
def bundle() -> dict:
    """Dict trong churn_vX.joblib (raw_pipe, model) cho ml_engine.src.segment.score()."""
    return joblib.load(Path(settings.ARTIFACT_DIR) / f"{config()['version']}.joblib")


def active_predictions():
    """Prediction của version đang dùng; bảng còn giữ lịch sử version cũ (unique customer + version)."""
    return Prediction.objects.filter(model_version=config()["version"])
