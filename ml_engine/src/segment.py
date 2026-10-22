"""BR-01, 02, 04, 06, 07: risk, tier, segment, kênh và hàm score() dùng chung cho seed_db và /predict.

Một chỗ duy nhất cho luật nghiệp vụ → batch và /predict không thể lệch nhau (FR-PRED-01 acceptance).
"""
import numpy as np
import pandas as pd

from ml_engine.src.clean import AGE_RANGE, NUMERIC_COLS
from ml_engine.src.clv import clv_components
from ml_engine.src.explain import top_reasons

# BR-04: (risk_label, clv_tier) → segment
SEGMENTS = {
    ("High", "High"): "S1", ("High", "Mid"): "S2", ("High", "Low"): "S3",
    ("Low", "High"): "S4", ("Low", "Mid"): "S5", ("Low", "Low"): "S6",
}


def risk_label(p_churn, tau):
    """BR-01: High nếu p_churn ≥ τ."""
    return np.where(np.asarray(p_churn) >= tau, "High", "Low")


def clv_tier(clv_potential, p33, p67):
    """BR-02: Low < P33 ≤ Mid < P67 ≤ High."""
    clv = np.asarray(clv_potential)
    return np.select([clv >= p67, clv >= p33], ["High", "Mid"], "Low")


def segment(risk, tier):
    return np.array([SEGMENTS[k] for k in zip(risk, tier)])


def channel(seg, email_open_rate, email_median):
    """BR-06: S1 → Phone; còn lại Email nếu Email_Open_Rate ≥ median train, ngược lại Push app / SMS."""
    email = np.where(np.asarray(email_open_rate) >= email_median, "Email", "Push app / SMS")
    return np.where(np.asarray(seg) == "S1", "Phone", email)


def imputed_fields(X):
    """BR-07: tên các cột số mà CleanTransformer sẽ điền median (trống hoặc Age ngoài miền)."""
    na = X[NUMERIC_COLS].isna()
    na["Age"] |= X["Age"].notna() & ~X["Age"].between(*AGE_RANGE)
    cols = np.array(NUMERIC_COLS)
    return [cols[row].tolist() for row in na.to_numpy()]


def score(df, bundle, config, explain=False):
    """Chấm điểm đủ các cột của bảng predictions. Giữ nguyên index của df.

    bundle: dict trong churn_vX.joblib; config: clv_config.json. r_bar lấy từ config để khách mới
    và batch dùng cùng một hệ số CLV tiềm năng.
    explain=True thêm cột top_reasons (~7 ms/khách): bật cho /predict; seed đọc artifacts/top_reasons.json.gz.
    """
    X = df.drop(columns="Churned", errors="ignore")
    clean = bundle["raw_pipe"].named_steps["pre"].named_steps["clean"].transform(X)
    p = bundle["model"].predict_proba(X)[:, 1]

    out = clv_components(clean, p, g=config["g"], d=config["d"], horizon=config["horizon"],
                         r_bar=config["r_bar"], freq_cap=config["freq_cap"])
    out.insert(0, "p_churn", p)
    out["risk_label"] = risk_label(p, config["tau"])
    out["clv_tier"] = clv_tier(out["clv_potential"], config["P33"], config["P67"])
    out["segment"] = segment(out["risk_label"], out["clv_tier"])
    out["channel"] = channel(out["segment"], clean["Email_Open_Rate"], config["email_median"])
    out["imputed_fields"] = pd.Series(imputed_fields(X), index=X.index)
    if explain:
        out["top_reasons"] = top_reasons(bundle["raw_pipe"], X, config["feature_means"])
    return out
