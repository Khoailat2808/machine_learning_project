"""FR-ML-03, BR-05: SHAP → top 3 lý do mỗi khách + global importance (FR-DASH-06).

SHAP tính trên raw_pipe (model chưa hiệu chỉnh): CalibratedClassifierCV gồm 5 pipeline nên không
giải thích trực tiếp được; isotonic đơn điệu nên không đổi thứ tự lý do. Đơn vị SHAP: log-odds.

Chi phí: model 900 cây sâu tới 31 tầng → ~7 ms/khách dù shap đã dùng nhiều lõi, 50.000 khách ~6–9 phút.
Vì vậy lý do của cả tệp tính một lần lúc build (train.py → artifacts/top_reasons.json.gz), seed chỉ đọc;
/predict tính 1 khách (~80 ms nhờ cache explainer).
"""
from functools import lru_cache

import numpy as np
import pandas as pd
import shap

from ml_engine.src.features import ONEHOT_COLS

LABELS = {
    "Age": "Tuổi", "Gender": "Giới tính", "Country": "Quốc gia", "City": "Thành phố",
    "Signup_Quarter": "Quý đăng ký", "Membership_Years": "Số năm là thành viên",
    "Login_Frequency": "Số lần đăng nhập", "Session_Duration_Avg": "Thời lượng phiên (phút)",
    "Pages_Per_Session": "Số trang mỗi phiên", "Cart_Abandonment_Rate": "Tỷ lệ bỏ giỏ hàng",
    "Wishlist_Items": "Số món trong wishlist", "Total_Purchases": "Tổng số lần mua",
    "Average_Order_Value": "Giá trị đơn trung bình (USD)",
    "Days_Since_Last_Purchase": "Số ngày từ lần mua cuối", "Discount_Usage_Rate": "Tỷ lệ dùng mã giảm giá",
    "Returns_Rate": "Tỷ lệ trả hàng", "Email_Open_Rate": "Tỷ lệ mở email",
    "Customer_Service_Calls": "Số lần gọi CSKH", "Product_Reviews_Written": "Số đánh giá sản phẩm",
    "Social_Media_Engagement_Score": "Mức tương tác mạng xã hội", "Mobile_App_Usage": "Mức dùng app",
    "Payment_Method_Diversity": "Số phương thức thanh toán", "Credit_Balance": "Số dư tín dụng (USD)",
    "purchase_per_year": "Số lần mua mỗi năm", "engagement_score": "Điểm tương tác tổng hợp",
    "recency_bucket": "Nhóm thời gian từ lần mua cuối", "service_friction": "Số lần gọi CSKH trên mỗi đơn",
    "email_responsive": "Có hay mở email",
}


def source_of(col):
    """Cột sau encode → cột gốc: Country_USA → Country, is_missing_X → X."""
    for c in ONEHOT_COLS:
        if col.startswith(c + "_"):
            return c
    return col.removeprefix("is_missing_")


@lru_cache(maxsize=2)
def _explainer(model):
    """Dựng TreeExplainer mất vài giây với model này → giữ lại cho các lần /predict sau."""
    return shap.TreeExplainer(model)


def shap_by_source(raw_pipe, X):
    """SHAP (log-odds) mỗi khách, cộng gộp theo cột gốc. DataFrame cùng index với X."""
    pre, model = raw_pipe.named_steps["pre"], raw_pipe.named_steps["model"]
    Xe = pre.transform(X)
    sv = np.asarray(_explainer(model).shap_values(Xe))
    if sv.ndim == 3:  # RandomForest trả cả 2 lớp → lấy lớp churn
        sv = sv[..., 1]
    sv = pd.DataFrame(sv, index=X.index, columns=Xe.columns)
    return sv.T.groupby(source_of, sort=False).sum().T


def feature_frame(raw_pipe, X):
    """Giá trị sau clean + 5 feature mới (trước encode) — nguồn cho value/avg của feature mới."""
    return raw_pipe.named_steps["pre"][:-1].transform(X)


def feature_means(raw_pipe, X):
    """Trung bình toàn tệp của các cột số (BR-05 'trung bình'), lưu vào clv_config."""
    feat = feature_frame(raw_pipe, X)
    cols = [c for c in LABELS if c in feat and pd.api.types.is_numeric_dtype(feat[c])]
    return feat[cols].mean().round(2).to_dict()


def _plain(v):
    if pd.isna(v):
        return None
    return round(float(v), 2) if isinstance(v, (int, float, np.number)) else v


def top_reasons(raw_pipe, X, means, k=3, sv=None):
    """BR-05: k cột gốc có SHAP dương lớn nhất (có thể < k nếu không đủ cột dương).

    value = giá trị khách nhập (feature mới: giá trị tính ra); avg = trung bình toàn tệp, None với cột phân loại.
    sv: kết quả shap_by_source đã tính sẵn, để không tính SHAP hai lần.
    """
    if sv is None:
        sv = shap_by_source(raw_pipe, X)
    feat = feature_frame(raw_pipe, X)
    values = pd.DataFrame({c: X[c] if c in X else feat[c] for c in sv.columns}, index=X.index)
    arr, cols = sv.to_numpy(), sv.columns.to_numpy()
    order = np.argsort(-arr, axis=1)[:, :k]
    out = [
        [{"feature": cols[j], "label": LABELS.get(cols[j], cols[j]), "value": _plain(values.iat[i, j]),
          "avg": means.get(cols[j]), "shap": round(float(arr[i, j]), 4)}
         for j in idx if arr[i, j] > 0]
        for i, idx in enumerate(order)
    ]
    return pd.Series(out, index=X.index)


def global_importance(sv, k=10):
    """FR-DASH-06: top k cột gốc theo mean |SHAP| (sv = shap_by_source của cả tệp)."""
    imp = sv.abs().mean().nlargest(k)
    return [{"feature": c, "label": LABELS.get(c, c), "mean_abs_shap": round(float(v), 4)} for c, v in imp.items()]
