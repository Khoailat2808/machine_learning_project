# 04 – API contract

> Trạng thái: **v1 – cập nhật theo FRD v2 (19/10/2026)** · Phụ trách: Huy, Tiến · Sau khi chốt, mọi thay đổi phải qua PR có reviewer của cả FE và BE.

## Quy ước chung

- Base URL: `http://localhost:8000/api/v1`
- Header: `Authorization: Bearer <access_token>` (mọi endpoint trừ `/auth/login`)
- Định dạng: JSON, UTF-8; số thực trả về dạng number, tiền là USD làm tròn 2 chữ số.
- Phân trang: `?page=1` (50 dòng/trang), response có `count`, `next`, `previous`, `results`.
- Lỗi:

| Mã | Khi nào | Body |
| --- | --- | --- |
| 400 | Dữ liệu sai | `{"errors": {"Age": "Phải trong khoảng 13–100"}}` |
| 401 | Thiếu/hết hạn token | `{"detail": "Authentication credentials were not provided."}` |
| 404 | Không tìm thấy | `{"detail": "Không tìm thấy khách hàng."}` |

## Danh sách endpoint

Mọi endpoint chỉ cần đăng nhập (một vai trò Marketer, xem [02-FRD.md](02-FRD.md) mục 2).

| Method | Endpoint | FR | Ưu tiên |
| --- | --- | --- | --- |
| POST | `/auth/login` | FR-AUTH-01 | P0 |
| POST | `/auth/refresh` | FR-AUTH-02 | P0 |
| GET | `/dashboard/summary?country=` | FR-DASH-01–04, 07 | P0 |
| GET | `/model/info` | FR-DASH-05, 06 | P0 |
| GET | `/customers?segment=&risk=&tier=&country=&city=&q=&sort=&page=` | FR-CUS-01, 02 | P0 |
| GET | `/customers/{id}` | FR-CUS-03, 04; FR-SEG-03 | P0 |
| GET | `/customers/export?<cùng bộ lọc>` | FR-CUS-05 | P0 |
| GET | `/journeys` | FR-SEG-01 | P0 |
| POST | `/campaigns/preview` | FR-CAMP-02 | P0 |
| POST | `/campaigns/export` | FR-CAMP-03 | P0 |
| POST / GET | `/campaigns` | FR-CAMP-04 | P1 |
| GET | `/campaigns/{id}/export` | FR-CAMP-04 | P1 |
| POST | `/predict?save=` | FR-PRED-01–03, FR-CUS-06 | P0 |
| POST | `/predict/batch` (multipart CSV → CSV) | FR-PRED-04 | P1 |

## Mẫu request / response

### POST `/auth/login`

```json
// request
{ "username": "marketer", "password": "demo123" }

// 200
{ "access": "eyJ...", "refresh": "eyJ...", "user": { "username": "marketer" } }
```

### GET `/dashboard/summary`

```json
{
  "total_customers": 50000,
  "high_risk_rate": 0.343,
  "total_clv_expected": 21820000.00,
  "total_value_at_risk": 4970000.00,
  "model": { "version": "churn_v1", "scored_at": "2026-10-29T10:15:00+07:00" },
  "thresholds": { "tau": 0.186, "clv_p33": 143.0, "clv_p67": 342.0 },
  "segments": [
    { "segment": "S1", "name": "VIP nguy cơ", "risk": "High", "tier": "High", "count": 3837, "share": 0.077, "value_at_risk": 2100000.00 },
    { "segment": "S2", "name": "Tiềm năng dễ mất", "risk": "High", "tier": "Mid", "count": 3697, "share": 0.074, "value_at_risk": 1260000.00 }
  ],
  "p_churn_histogram": [ { "bin": "0.0-0.1", "count": 21000 } ],
  "by_country": [ { "country": "USA", "count": 17384, "value_at_risk": 1730000.00 } ]
}
```

> Số trong mẫu chỉ để minh họa định dạng.

### GET `/customers?segment=S1&country=USA&sort=-value_at_risk&page=1`

```json
{
  "count": 1325,
  "next": "/api/v1/customers?segment=S1&country=USA&sort=-value_at_risk&page=2",
  "previous": null,
  "results": [
    {
      "customer_id": "CUS01234",
      "country": "USA",
      "city": "Houston",
      "p_churn": 0.82,
      "risk_label": "High",
      "clv_pred": 512.40,
      "clv_potential": 1180.75,
      "clv_tier": "High",
      "value_at_risk": 968.22,
      "segment": "S1"
    }
  ]
}
```

### GET `/customers/{id}`

```json
{
  "customer_id": "CUS01234",
  "attributes": {
    "behavior": { "Login_Frequency": 6, "Session_Duration_Avg": 18.2, "Pages_Per_Session": 4.1, "Mobile_App_Usage": 9.5 },
    "purchase": { "Total_Purchases": 22, "Average_Order_Value": 182.3, "Days_Since_Last_Purchase": 64, "Returns_Rate": 4.2 },
    "engagement": { "Email_Open_Rate": 8.1, "Customer_Service_Calls": 12, "Product_Reviews_Written": 1 }
  },
  "prediction": {
    "p_churn": 0.82, "risk_label": "High",
    "clv_pred": 512.40, "clv_potential": 1180.75, "clv_tier": "High",
    "value_at_risk": 968.22, "segment": "S1", "channel": "Phone",
    "top_reasons": [
      { "feature": "Customer_Service_Calls", "label": "Số lần gọi CSKH", "value": 12, "avg": 5.7, "shap": 0.21 },
      { "feature": "Cart_Abandonment_Rate", "label": "Tỷ lệ bỏ giỏ hàng", "value": 78.0, "avg": 57.1, "shap": 0.14 },
      { "feature": "Email_Open_Rate", "label": "Tỷ lệ mở email", "value": 8.1, "avg": 20.9, "shap": 0.09 }
    ],
    "model_version": "churn_v1",
    "scored_at": "2026-10-29T10:15:00+07:00"
  },
  "journey": { "journey_id": "J1", "name": "VIP nguy cơ", "steps": [ { "day": 0, "channel": "Phone", "action": "CSKH liên hệ cá nhân", "offer": null } ] }
}
```

### POST `/predict`

```json
// request — 23 trường, trường tùy chọn có thể bỏ trống (null)
{
  "Age": 34, "Gender": "Female", "Country": "UK", "City": "London", "Signup_Quarter": "Q2",
  "Membership_Years": 1.5, "Login_Frequency": 8, "Session_Duration_Avg": null, "Pages_Per_Session": 6.2,
  "Cart_Abandonment_Rate": 65.0, "Wishlist_Items": 3, "Total_Purchases": 7, "Average_Order_Value": 95.5,
  "Days_Since_Last_Purchase": 40, "Discount_Usage_Rate": 55.0, "Returns_Rate": 6.0, "Email_Open_Rate": 12.0,
  "Customer_Service_Calls": 8, "Product_Reviews_Written": 1, "Social_Media_Engagement_Score": null,
  "Mobile_App_Usage": 14.0, "Payment_Method_Diversity": 2, "Credit_Balance": 1500
}

// 200
{
  "p_churn": 0.64, "risk_label": "High",
  "clv_pred": 98.10, "clv_potential": 180.40, "clv_tier": "Mid",
  "value_at_risk": 115.46, "segment": "S2", "channel": "Push app / SMS",
  "journey": { "journey_id": "J2", "name": "Tiềm năng dễ mất" },
  "top_reasons": [ { "feature": "Customer_Service_Calls", "label": "Số lần gọi CSKH", "value": 8, "avg": 5.7, "shap": 0.11 } ],
  "imputed_fields": ["Session_Duration_Avg", "Social_Media_Engagement_Score"],
  "saved": false,
  "customer_id": null
}

// 400
{ "errors": { "City": "London không thuộc Country = USA" } }
```

### GET `/model/info`

```json
{
  "version": "churn_v1", "algorithm": "LightGBM (isotonic)", "trained_at": "2026-10-13",
  "metrics": { "roc_auc": 0.918, "recall": 0.858, "precision": 0.723 },
  "plain_text": [
    "Trong 100 khách thực sự rời đi, mô hình phát hiện 86.",
    "Trong 100 khách bị gắn rủi ro cao, 72 thực sự rời đi."
  ],
  "thresholds": { "tau": 0.186, "clv_p33": 143.0, "clv_p67": 342.0 },
  "global_importance": [ { "feature": "Customer_Service_Calls", "label": "Số lần gọi CSKH", "mean_abs_shap": 0.12 } ],
  "limitations": ["Dữ liệu tổng hợp", "Giả định nhãn Churned ứng với chu kỳ 1 năm"]
}
```

### POST `/campaigns/preview`

```json
// request — budget null = không giới hạn; spend_pct null = dùng mức của từng phân khúc (BR-08)
{
  "segments": ["S1", "S2"], "country": null, "city": null,
  "budget": 100000, "spend_pct": null, "success_rate": 0.20
}

// 200 — số chỉ để minh họa định dạng
{
  "eligible": 7534, "selected": 1630,
  "total_cost": 99870.50, "total_value_at_risk": 690000.00,
  "expected_saved": 138000.00, "roi": 0.38, "break_even_rate": 0.145,
  "by_segment": [
    { "segment": "S1", "selected": 1630, "cost": 99870.50, "value_at_risk": 690000.00 },
    { "segment": "S2", "selected": 0, "cost": 0, "value_at_risk": 0 }
  ],
  "is_estimate": true
}
```

`/campaigns/export` nhận cùng body, trả `text/csv` (UTF-8 BOM) với các cột trong FR-CAMP-03.
