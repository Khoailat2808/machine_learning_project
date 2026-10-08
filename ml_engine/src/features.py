"""FR-ML-04: 5 feature mới + encoding, chung một Pipeline cho train và /predict.

purchase_per_year = Total_Purchases / max(Membership_Years, 0.5), cắt ở p99 train (khớp docs/05)
engagement_score  = trung bình min-max (fit train) của ENGAGEMENT_COLS, trong [0, 1]
recency_bucket    = Days_Since_Last_Purchase: 0–7 → 0, 8–30 → 1, 31–90 → 2, > 90 → 3
service_friction  = Customer_Service_Calls / (Total_Purchases + 1)
email_responsive  = 1 nếu Email_Open_Rate ≥ median train
"""
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, TargetEncoder

from ml_engine.src.clean import CleanTransformer

ENGAGEMENT_COLS = [
    "Session_Duration_Avg", "Pages_Per_Session", "Mobile_App_Usage",
    "Email_Open_Rate", "Login_Frequency",
]
RECENCY_BINS = [-np.inf, 7, 30, 90, np.inf]
ONEHOT_COLS = ["Gender", "Country", "Signup_Quarter"]
TARGET_ENC_COLS = ["City"]
DROP_COLS = ["Lifetime_Value", "Churned", "customer_id"]  # leakage / nhãn / ID


def _purchase_per_year(X):
    return X["Total_Purchases"] / X["Membership_Years"].clip(lower=0.5)


class FeatureBuilder(BaseEstimator, TransformerMixin):
    """Chạy sau CleanTransformer (giả định không còn NaN ở cột số)."""

    def __init__(self, freq_quantile=0.99):
        self.freq_quantile = freq_quantile

    def fit(self, X, y=None):
        self.freq_cap_ = float(_purchase_per_year(X).quantile(self.freq_quantile))
        self.eng_min_ = X[ENGAGEMENT_COLS].min()
        self.eng_range_ = (X[ENGAGEMENT_COLS].max() - self.eng_min_).replace(0, 1)
        self.email_median_ = float(X["Email_Open_Rate"].median())
        return self

    def transform(self, X):
        X = X.drop(columns=DROP_COLS, errors="ignore")
        X["purchase_per_year"] = _purchase_per_year(X).clip(upper=self.freq_cap_)
        scaled = ((X[ENGAGEMENT_COLS] - self.eng_min_) / self.eng_range_).clip(0, 1)
        X["engagement_score"] = scaled.mean(axis=1)
        X["recency_bucket"] = pd.cut(X["Days_Since_Last_Purchase"], RECENCY_BINS, labels=False).astype(int)
        X["service_friction"] = X["Customer_Service_Calls"] / (X["Total_Purchases"] + 1)
        X["email_responsive"] = (X["Email_Open_Rate"] >= self.email_median_).astype(int)
        return X


def build_preprocessor():
    """clean → features → encode. Gọi .fit(X_train, y_train) vì TargetEncoder cần y."""
    encode = ColumnTransformer(
        [
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ONEHOT_COLS),
            ("city", TargetEncoder(random_state=42), TARGET_ENC_COLS),
        ],
        remainder="passthrough",
        verbose_feature_names_out=False,
    ).set_output(transform="pandas")
    return Pipeline([
        ("clean", CleanTransformer()),
        ("features", FeatureBuilder()),
        ("encode", encode),
    ])
