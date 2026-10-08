from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ml_engine.src.features import FeatureBuilder, build_preprocessor

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "ecommerce_customer_dataset.csv"


def test_feature_formulas():
    X = pd.DataFrame({
        "Total_Purchases": [10.0, 0.0, 20.0],
        "Membership_Years": [2.0, 0.1, 4.0],
        "Session_Duration_Avg": [1.0, 3.0, 5.0],
        "Pages_Per_Session": [1.0, 3.0, 5.0],
        "Mobile_App_Usage": [1.0, 3.0, 5.0],
        "Email_Open_Rate": [10.0, 20.0, 30.0],
        "Login_Frequency": [1.0, 3.0, 5.0],
        "Days_Since_Last_Purchase": [7.0, 30.0, 91.0],
        "Customer_Service_Calls": [11.0, 2.0, 0.0],
        "Lifetime_Value": [1.0, 2.0, 3.0],
    })
    fb = FeatureBuilder(freq_quantile=1.0).fit(X)
    out = fb.transform(X)
    assert out["purchase_per_year"].tolist() == [5.0, 0.0, 5.0]  # Membership_Years ≥ 0.5
    assert out["engagement_score"].tolist() == [0.0, 0.5, 1.0]
    assert out["recency_bucket"].tolist() == [0, 1, 3]
    assert out["service_friction"].tolist() == [1.0, 2.0, 0.0]
    assert out["email_responsive"].tolist() == [0, 1, 1]
    assert "Lifetime_Value" not in out


@pytest.mark.skipif(not RAW.exists(), reason="thiếu CSV gốc")
def test_preprocessor_on_raw_data():
    df = pd.read_csv(RAW)
    y = df.pop("Churned")
    pre = build_preprocessor().fit(df, y)
    out = pre.transform(df)
    assert len(out) == len(df)
    assert not out.isna().any().any()
    assert "Lifetime_Value" not in out.columns
    rates = ["Cart_Abandonment_Rate", "Discount_Usage_Rate", "Returns_Rate", "Email_Open_Rate"]
    assert out[rates].min().min() >= 0 and out[rates].max().max() <= 100
    assert out["engagement_score"].between(0, 1).all()

    # /predict: 1 khách mới, bỏ trống các trường tùy chọn, không có Lifetime_Value
    one = df.drop(columns="Lifetime_Value").head(1).copy()
    one[["Social_Media_Engagement_Score", "Credit_Balance", "Returns_Rate"]] = np.nan
    row = pre.transform(one)
    assert list(row.columns) == list(out.columns)
    assert not row.isna().any().any()
    assert row["is_missing_Credit_Balance"].iloc[0] == 1
