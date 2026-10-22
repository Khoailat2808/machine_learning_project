import json

import joblib
import numpy as np
import pandas as pd
import pytest

from ml_engine.src.segment import SEGMENTS, channel, clv_tier, risk_label, score, segment
from ml_engine.src.train import ARTIFACTS_DIR, RAW

CONFIG = ARTIFACTS_DIR / "clv_config.json"
OPTIONAL = [  # 14 trường tùy chọn, docs/02 mục 9
    "Age", "Session_Duration_Avg", "Pages_Per_Session", "Wishlist_Items", "Days_Since_Last_Purchase",
    "Discount_Usage_Rate", "Returns_Rate", "Email_Open_Rate", "Customer_Service_Calls",
    "Product_Reviews_Written", "Social_Media_Engagement_Score", "Mobile_App_Usage",
    "Payment_Method_Diversity", "Credit_Balance",
]


def test_boundaries_belong_to_upper_class():
    assert risk_label([0.2, 0.2 - 1e-9], 0.2).tolist() == ["High", "Low"]
    assert clv_tier([99.99, 100, 199.99, 200], 100, 200).tolist() == ["Low", "Mid", "Mid", "High"]


def test_six_segments_br04():
    risk, tier = zip(*SEGMENTS)
    assert segment(risk, tier).tolist() == ["S1", "S2", "S3", "S4", "S5", "S6"]


def test_channel_br06():
    seg = ["S1", "S2", "S2", "S6"]
    assert channel(seg, [90, 20, 19.9, 50], 20).tolist() == ["Phone", "Email", "Push app / SMS", "Email"]


@pytest.fixture(scope="module")
def scored():
    if not (RAW.exists() and CONFIG.exists()):
        pytest.skip("chưa có CSV gốc hoặc artifact")
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    bundle = joblib.load(ARTIFACTS_DIR / f"{config['version']}.joblib")
    df = pd.read_csv(RAW).sample(500, random_state=1)
    return df, bundle, config, score(df, bundle, config)


def test_score_columns_and_ranges(scored):
    df, _, _, out = scored
    assert out.index.equals(df.index)
    assert set(out.columns) == {"p_churn", "risk_label", "clv_pred", "clv_potential", "clv_tier",
                                "value_at_risk", "segment", "channel", "imputed_fields"}
    assert out["p_churn"].between(0, 1).all() and not out.drop(columns="imputed_fields").isna().any().any()
    assert (out.loc[out.segment == "S1", "channel"] == "Phone").all()


def test_single_row_matches_batch(scored):
    """FR-PRED-01: /predict (1 dòng) và batch cho cùng kết quả."""
    df, bundle, config, out = scored
    one = score(df.iloc[[7]], bundle, config)
    assert one["p_churn"].iloc[0] == pytest.approx(out["p_churn"].iloc[7], abs=1e-3)
    assert one.drop(columns="p_churn").iloc[0].tolist() == out.drop(columns="p_churn").iloc[7].tolist()


def test_all_optional_missing_still_scores(scored):
    """FR-PRED acceptance: bỏ trống mọi trường tùy chọn → vẫn chấm, báo 14 trường được ước lượng."""
    df, bundle, config, _ = scored
    row = df.iloc[[0]].copy()
    row[OPTIONAL] = np.nan
    out = score(row, bundle, config)
    assert sorted(out["imputed_fields"].iloc[0]) == sorted(OPTIONAL)
    assert 0 <= out["p_churn"].iloc[0] <= 1


def test_explain_adds_top_reasons_for_predict(scored):
    df, bundle, config, _ = scored
    out = score(df.iloc[[0]], bundle, config, explain=True)
    assert 1 <= len(out["top_reasons"].iloc[0]) <= 3


def test_invalid_age_is_reported_as_imputed(scored):
    df, bundle, config, _ = scored
    row = df.iloc[[0]].copy()
    row[OPTIONAL] = row[OPTIONAL].fillna(1)
    row["Age"] = 200
    assert score(row, bundle, config)["imputed_fields"].iloc[0] == ["Age"]
