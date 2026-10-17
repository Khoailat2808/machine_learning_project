import numpy as np
import pandas as pd
import pytest
from scipy.stats import spearmanr

from ml_engine.src.clv import (
    build_clv_config,
    calculate_margin,
    clv_components,
    sensitivity_analysis_d,
)


@pytest.fixture
def sample_customer_df():
    """Tạo tệp dữ liệu kiểm thử giả lập với đủ các trường và trường hợp biên."""
    n = 300
    rng = np.random.default_rng(42)
    # Total_Purchases * AOV có tương quan cao với Lifetime_Value
    purchases = rng.integers(1, 40, size=n).astype(float)
    aov = rng.uniform(30.0, 300.0, size=n)
    years = rng.uniform(0.5, 8.0, size=n)
    returns = rng.uniform(0.0, 15.0, size=n)

    # Lifetime_Value thực tế tương quan mạnh với purchases * aov
    ltv = purchases * aov * rng.uniform(0.8, 1.2, size=n)

    df = pd.DataFrame({
        "Total_Purchases": purchases,
        "Average_Order_Value": aov,
        "Membership_Years": years,
        "Returns_Rate": returns,
        "Lifetime_Value": ltv,
    })

    # Cài các trường hợp biên
    df.loc[0, "Total_Purchases"] = -5.0       # âm -> clip về 0
    df.loc[1, "Membership_Years"] = 0.1       # nhỏ hơn 0.5 -> clip về 0.5
    df.loc[2, "Returns_Rate"] = np.nan        # NaN -> fillna 0
    df.loc[3, "Returns_Rate"] = 150.0        # > 100% -> clip về 100%
    df.loc[4, "Average_Order_Value"] = -10.0  # âm -> clip về 0

    p_churn = rng.uniform(0.05, 0.95, size=n)
    p_churn[0] = -0.2  # test clip
    p_churn[1] = 1.4   # test clip

    return df, p_churn


def test_clv_no_negative_or_nan(sample_customer_df):
    """Tiêu chí nghiệm thu: không giá trị âm hoặc NaN."""
    df, p_churn = sample_customer_df
    res = clv_components(df, p_churn)

    assert not res.isna().any().any(), "CLV kết quả không được chứa NaN"
    assert (res["clv_pred"] >= 0).all(), "clv_pred không được có giá trị âm"
    assert (res["clv_potential"] >= 0).all(), "clv_potential không được có giá trị âm"
    assert (res["value_at_risk"] >= 0).all(), "value_at_risk không được có giá trị âm"


def test_spearman_with_lifetime_value(sample_customer_df):
    """Tiêu chí nghiệm thu: Spearman với Lifetime_Value >= 0.5."""
    df, p_churn = sample_customer_df
    res = clv_components(df, p_churn)

    corr_potential, _ = spearmanr(res["clv_potential"], df["Lifetime_Value"])
    assert corr_potential >= 0.5, f"Spearman ({corr_potential:.2f}) phải >= 0.5"


def test_value_at_risk_bounds(sample_customer_df):
    """VaR = p_churn * CLV_tiem_nang nên luôn <= CLV_tiem_nang."""
    df, p_churn = sample_customer_df
    res = clv_components(df, p_churn)
    diff = res["value_at_risk"] - res["clv_potential"]
    assert (diff <= 1e-2).all(), "VaR không thể vượt quá CLV tiềm năng"


def test_sensitivity_analysis_d_invariance(sample_customer_df):
    """Phân tích độ nhạy d: trong khoảng 8%-12%, thứ tự xếp hạng không đổi và 0 khách đổi tier."""
    df, p_churn = sample_customer_df
    sens = sensitivity_analysis_d(df, p_churn, d_values=(0.08, 0.10, 0.12))

    assert len(sens) == 3
    # Thứ tự xếp hạng Spearman của clv_potential luôn là 1.0 vì mult_potential là hệ số nhân vô hướng dương
    assert (sens["spearman_vs_base_potential"] == 1.0).all()
    # 0 khách đổi tier CLV tiềm năng khi d thay đổi
    assert (sens["tier_swap_count"] == 0).all()
    assert (sens["tier_swap_pct"] == 0.0).all()


def test_build_clv_config_schema(sample_customer_df, tmp_path):
    """Đảm bảo cấu hình sinh ra đủ 5 trường Django models_mgmt yêu cầu: g, d, horizon, P33, P67."""
    df, p_churn = sample_customer_df
    cfg_file = tmp_path / "clv_config.json"
    config = build_clv_config(df, p_churn, save_path=cfg_file)

    required_keys = {"g", "d", "horizon", "P33", "P67"}
    assert required_keys <= config.keys(), f"Thiếu khóa trong {required_keys}"
    assert cfg_file.exists()
    assert config["P33"] > 0
    assert config["P67"] >= config["P33"]
