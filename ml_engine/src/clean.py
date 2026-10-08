"""FR-ML-03: CleanTransformer — xử lý 6 nhóm lỗi trong docs/07-data-dictionary.md mục 3.

1. Missing values  → cờ is_missing_<col> cho 5 cột > 8%, rồi median impute (fit trên train)
2. Age vô lý       → < 13 hoặc > 100 gán NaN rồi impute
3. Total_Purchases → clip ≥ 0, giữ số lẻ
4. Tỷ lệ > 100%    → clip [0, 100]
5. Outlier AOV     → winsorize ở p99 của train
6. LTV = 0         → giữ nguyên (không đụng Lifetime_Value)
"""
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

NUMERIC_COLS = [
    "Age", "Membership_Years", "Login_Frequency", "Session_Duration_Avg",
    "Pages_Per_Session", "Cart_Abandonment_Rate", "Wishlist_Items",
    "Total_Purchases", "Average_Order_Value", "Days_Since_Last_Purchase",
    "Discount_Usage_Rate", "Returns_Rate", "Email_Open_Rate",
    "Customer_Service_Calls", "Product_Reviews_Written",
    "Social_Media_Engagement_Score", "Mobile_App_Usage",
    "Payment_Method_Diversity", "Credit_Balance",
]
RATE_COLS = ["Cart_Abandonment_Rate", "Discount_Usage_Rate", "Returns_Rate", "Email_Open_Rate"]
MISSING_FLAG_COLS = [
    "Social_Media_Engagement_Score", "Credit_Balance", "Mobile_App_Usage",
    "Returns_Rate", "Wishlist_Items",
]
AGE_RANGE = (13, 100)


class CleanTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, aov_quantile=0.99):
        self.aov_quantile = aov_quantile

    def _fix_values(self, X):
        X = X.copy()
        X["Age"] = X["Age"].where(X["Age"].between(*AGE_RANGE))
        X["Total_Purchases"] = X["Total_Purchases"].clip(lower=0)
        X[RATE_COLS] = X[RATE_COLS].clip(0, 100)
        return X

    def fit(self, X, y=None):
        X = self._fix_values(X)
        self.aov_cap_ = float(X["Average_Order_Value"].quantile(self.aov_quantile))
        self.medians_ = X[NUMERIC_COLS].median().to_dict()
        return self

    def transform(self, X):
        X = self._fix_values(X)
        X["Average_Order_Value"] = X["Average_Order_Value"].clip(upper=self.aov_cap_)
        for col in MISSING_FLAG_COLS:
            X[f"is_missing_{col}"] = X[col].isna().astype(int)
        X[NUMERIC_COLS] = X[NUMERIC_COLS].fillna(self.medians_)
        return X
