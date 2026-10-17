"""FR-ML-08 / docs/05-clv-methodology.md: Ước tính CLV và phân tích độ nhạy d.

Mô hình CLV 3 năm trên lợi nhuận ròng sau trả hàng, chiết khấu d = 10%/năm:
- CLV kỳ vọng: m_i * sum_{t=1}^3 (r_i^t / (1+d)^t) với r_i = 1 - p_churn_i
- CLV tiềm năng: m_i * sum_{t=1}^3 (r_bar^t / (1+d)^t) (dùng r_bar toàn tệp để chia tier không bị lệch do churn)
- Value at Risk (VaR): p_churn_i * CLV_tiềm_năng_i
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

DEFAULT_G = 0.33
DEFAULT_D = 0.10
DEFAULT_HORIZON = 3
DEFAULT_R_BAR = 0.711


def calculate_margin(
    df: pd.DataFrame,
    *,
    g: float = DEFAULT_G,
    freq_cap: float | None = None,
) -> pd.Series:
    """Tính lợi nhuận ròng hàng năm m_i = AOV * (1 - Returns_Rate) * freq * g."""
    tp = df["Total_Purchases"].clip(lower=0)
    years = df["Membership_Years"].clip(lower=0.5)
    freq = tp / years
    if freq_cap is not None:
        freq = freq.clip(upper=freq_cap)

    returns = (df["Returns_Rate"].clip(0, 100) / 100.0).fillna(0)
    aov = df["Average_Order_Value"].clip(lower=0)
    m = aov * (1.0 - returns) * freq * g
    return m.fillna(0).clip(lower=0)


def clv_components(
    df: pd.DataFrame,
    p_churn: np.ndarray | pd.Series | list,
    *,
    g: float = DEFAULT_G,
    d: float = DEFAULT_D,
    horizon: int = DEFAULT_HORIZON,
    r_bar: float | None = None,
    freq_cap: float | None = None,
) -> pd.DataFrame:
    """Tính toán bộ 3 chỉ số: clv_pred (kỳ vọng), clv_potential (tiềm năng), value_at_risk.

    Parameters
    ----------
    df : pd.DataFrame
        Chứa Total_Purchases, Membership_Years, Returns_Rate, Average_Order_Value.
    p_churn : array-like
        Xác suất churn trong [0, 1] từ model churn đã calibrate.
    g : float, default 0.33
        Biên lợi nhuận gộp (Retail Mỹ 33.18%, Damodaran 2026).
    d : float, default 0.10
        Lãi suất chiết khấu hàng năm.
    horizon : int, default 3
        Khoảng thời gian dự phóng (năm).
    r_bar : float, optional
        Tỷ lệ giữ chân trung bình toàn tệp. Mặc định tính từ trung bình của (1 - p_churn).
    freq_cap : float, optional
        Giới hạn trần tần suất mua (thường là p99 của tập train).

    Returns
    -------
    pd.DataFrame
        DataFrame cùng index với df gồm các cột:
        - clv_pred: CLV kỳ vọng (USD)
        - clv_potential: CLV tiềm năng (USD)
        - value_at_risk: Giá trị rủi ro mất đi nếu churn (USD)
    """
    p = np.asarray(p_churn, dtype=float)
    p = np.clip(p, 0.0, 1.0)

    m = calculate_margin(df, g=g, freq_cap=freq_cap).to_numpy()

    r = 1.0 - p
    if r_bar is None:
        r_bar = float(np.mean(r)) if len(r) > 0 else DEFAULT_R_BAR

    t = np.arange(1, horizon + 1)
    disc = (1.0 + d) ** t

    # mult_expected: từng khách có r_i riêng
    mult_expected = (r[:, None] ** t / disc).sum(axis=1)
    # mult_potential: hằng số chung cho toàn tệp theo r_bar
    mult_potential = float((r_bar ** t / disc).sum())

    out = pd.DataFrame(index=df.index)
    out["clv_pred"] = np.round(m * mult_expected, 2)
    out["clv_potential"] = np.round(m * mult_potential, 2)
    out["value_at_risk"] = np.round(p * out["clv_potential"], 2)

    return out


def build_clv_config(
    df: pd.DataFrame,
    p_churn: np.ndarray | pd.Series | list,
    *,
    g: float = DEFAULT_G,
    d: float = DEFAULT_D,
    horizon: int = DEFAULT_HORIZON,
    freq_cap: float | None = None,
    save_path: str | Path | None = None,
) -> dict:
    """Xây dựng dict cấu hình CLV (bao gồm ngưỡng phân vị P33, P67 của clv_potential)."""
    p = np.asarray(p_churn, dtype=float)
    r_bar = float(np.mean(1.0 - np.clip(p, 0.0, 1.0)))

    if freq_cap is None and "Total_Purchases" in df and "Membership_Years" in df:
        years = df["Membership_Years"].clip(lower=0.5)
        raw_freq = df["Total_Purchases"].clip(lower=0) / years
        freq_cap = float(raw_freq.quantile(0.99))

    res = clv_components(df, p, g=g, d=d, horizon=horizon, r_bar=r_bar, freq_cap=freq_cap)
    p33 = float(res["clv_potential"].quantile(0.3333))
    p67 = float(res["clv_potential"].quantile(0.6667))

    config = {
        "g": float(g),
        "d": float(d),
        "horizon": int(horizon),
        "r_bar": round(r_bar, 4),
        "freq_cap": round(freq_cap, 2) if freq_cap is not None else None,
        "P33": round(p33, 2),
        "P67": round(p67, 2),
    }

    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    return config


def sensitivity_analysis_d(
    df: pd.DataFrame,
    p_churn: np.ndarray | pd.Series | list,
    d_values: tuple[float, ...] = (0.08, 0.10, 0.12),
    *,
    g: float = DEFAULT_G,
    horizon: int = DEFAULT_HORIZON,
    freq_cap: float | None = None,
) -> pd.DataFrame:
    """Phân tích độ nhạy của tỷ lệ chiết khấu d đối với CLV và thứ hạng khách hàng.

    Trả về bảng tổng hợp với các chỉ số:
    - mean / median của clv_potential và clv_pred
    - Spearman correlation so với mốc d = 0.10
    - Tỷ lệ khách hàng thay đổi tier (Low/Mid/High) so với mốc d = 0.10
    """
    base_d = 0.10
    base_res = clv_components(df, p_churn, g=g, d=base_d, horizon=horizon, freq_cap=freq_cap)
    base_p33 = base_res["clv_potential"].quantile(0.3333)
    base_p67 = base_res["clv_potential"].quantile(0.6667)

    base_tiers = pd.cut(
        base_res["clv_potential"],
        bins=[-np.inf, base_p33, base_p67, np.inf],
        labels=["Low", "Mid", "High"],
    )

    rows = []
    for d in d_values:
        res = clv_components(df, p_churn, g=g, d=d, horizon=horizon, freq_cap=freq_cap)
        p33 = res["clv_potential"].quantile(0.3333)
        p67 = res["clv_potential"].quantile(0.6667)
        tiers = pd.cut(
            res["clv_potential"],
            bins=[-np.inf, p33, p67, np.inf],
            labels=["Low", "Mid", "High"],
        )

        spearman_potential, _ = spearmanr(base_res["clv_potential"], res["clv_potential"])
        spearman_expected, _ = spearmanr(base_res["clv_pred"], res["clv_pred"])
        tier_swaps = int((tiers != base_tiers).sum())
        tier_swap_pct = float(tier_swaps / len(df) * 100) if len(df) > 0 else 0.0

        rows.append({
            "d": d,
            "mean_clv_potential": round(float(res["clv_potential"].mean()), 2),
            "median_clv_potential": round(float(res["clv_potential"].median()), 2),
            "mean_clv_expected": round(float(res["clv_pred"].mean()), 2),
            "median_clv_expected": round(float(res["clv_pred"].median()), 2),
            "P33": round(float(p33), 2),
            "P67": round(float(p67), 2),
            "spearman_vs_base_potential": round(float(spearman_potential), 4),
            "spearman_vs_base_expected": round(float(spearman_expected), 4),
            "tier_swap_count": tier_swaps,
            "tier_swap_pct": round(tier_swap_pct, 4),
        })

    return pd.DataFrame(rows)
