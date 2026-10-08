import numpy as np
import pandas as pd
import pytest

from ml_engine.src.clean import MISSING_FLAG_COLS, NUMERIC_COLS, RATE_COLS, CleanTransformer


@pytest.fixture
def df():
    n = 200
    rng = np.random.default_rng(42)
    d = pd.DataFrame({c: rng.uniform(1, 50, n) for c in NUMERIC_COLS})
    d["Age"] = 40.0
    d["Average_Order_Value"] = np.arange(1, n + 1, dtype=float)
    d["Lifetime_Value"] = 100.0
    d.loc[0, "Age"] = 5
    d.loc[1, "Age"] = 200
    d.loc[2, "Age"] = np.nan
    d.loc[3, "Total_Purchases"] = -13
    d.loc[4, "Total_Purchases"] = 7.5
    d.loc[5, RATE_COLS] = 143.7
    d.loc[6, RATE_COLS] = -1
    d.loc[7, MISSING_FLAG_COLS] = np.nan
    d.loc[8, "Lifetime_Value"] = 0
    return d


def test_six_error_groups(df):
    out = CleanTransformer().fit(df).transform(df)
    assert out.loc[[0, 1, 2], "Age"].tolist() == [40, 40, 40]  # vô lý/NaN → median
    assert out.loc[3, "Total_Purchases"] == 0
    assert out.loc[4, "Total_Purchases"] == 7.5
    assert (out.loc[5, RATE_COLS] == 100).all() and (out.loc[6, RATE_COLS] == 0).all()
    assert out["Average_Order_Value"].max() == pytest.approx(df["Average_Order_Value"].quantile(0.99))
    assert all(out.loc[7, f"is_missing_{c}"] == 1 for c in MISSING_FLAG_COLS)
    assert out[[f"is_missing_{c}" for c in MISSING_FLAG_COLS]].sum().sum() == len(MISSING_FLAG_COLS)
    assert out.loc[8, "Lifetime_Value"] == 0
    assert not out[NUMERIC_COLS].isna().any().any()
    assert df.loc[0, "Age"] == 5  # không sửa input


def test_thresholds_come_from_train(df):
    ct = CleanTransformer().fit(df)
    new = df.head(1).copy()
    new[["Average_Order_Value", "Credit_Balance"]] = [9666.38, np.nan]
    out = ct.transform(new)
    assert out["Average_Order_Value"].iloc[0] == ct.aov_cap_
    assert out["Credit_Balance"].iloc[0] == ct.medians_["Credit_Balance"]
