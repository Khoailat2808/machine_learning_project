import gzip
import json

import joblib
import pandas as pd
import pytest

from ml_engine.src.explain import LABELS, shap_by_source, source_of, top_reasons
from ml_engine.src.train import ARTIFACTS_DIR, RAW, TOP_REASONS


def test_source_of_groups_encoded_columns():
    assert source_of("Country_USA") == "Country"
    assert source_of("Signup_Quarter_Q1") == "Signup_Quarter"
    assert source_of("is_missing_Returns_Rate") == "Returns_Rate"
    assert source_of("service_friction") == "service_friction"


@pytest.fixture(scope="module")
def artifacts():
    if not (RAW.exists() and TOP_REASONS.exists()):
        pytest.skip("chưa có CSV gốc hoặc artifact")
    config = json.loads((ARTIFACTS_DIR / "clv_config.json").read_text(encoding="utf-8"))
    bundle = joblib.load(ARTIFACTS_DIR / f"{config['version']}.joblib")
    X = pd.read_csv(RAW, nrows=50).drop(columns="Churned")
    return X, bundle, config


def test_reasons_are_positive_sorted_and_labelled(artifacts):
    X, bundle, config = artifacts
    sv = shap_by_source(bundle["raw_pipe"], X)
    assert set(sv.columns) <= set(LABELS)  # mọi cột gốc đều có tên tiếng Việt
    for reasons in top_reasons(bundle["raw_pipe"], X, config["feature_means"], sv=sv):
        shaps = [r["shap"] for r in reasons]
        assert 1 <= len(reasons) <= 3 and all(s > 0 for s in shaps) and shaps == sorted(shaps, reverse=True)
        for r in reasons:
            assert r["label"] == LABELS[r["feature"]]
            assert (r["avg"] is None) == (r["feature"] in {"Gender", "Country", "City", "Signup_Quarter"})


def test_precomputed_reasons_match_on_demand(artifacts):
    """Seed (đọc file) và /predict (tính tại chỗ) phải ra cùng lý do cho cùng khách."""
    X, bundle, config = artifacts
    with gzip.open(TOP_REASONS, "rt", encoding="utf-8") as f:
        stored = json.load(f)
    assert stored["version"] == config["version"]
    fresh = top_reasons(bundle["raw_pipe"], X.iloc[[0, 17, 42]], config["feature_means"])
    for i, reasons in zip([0, 17, 42], fresh):
        assert [r["feature"] for r in reasons] == [r["feature"] for r in stored["reasons"][i]]
