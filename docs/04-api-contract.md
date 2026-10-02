# 04 – API contract

> Trạng thái: **bản nháp v0** · Hạn chốt: **09/10/2026** (Huy, Tiến) · Sau khi chốt, mọi thay đổi phải qua PR có reviewer của cả FE và BE.

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
| 403 | Sai vai trò | `{"detail": "Bạn không có quyền thực hiện thao tác này."}` |
| 404 | Không tìm thấy | `{"detail": "Không tìm thấy khách hàng."}` |
| 409 | Đang có training job | `{"detail": "Đang có job chạy.", "job_id": "…"}` |

## Danh sách endpoint

| Method | Endpoint | Vai trò | FR | Ưu tiên |
| --- | --- | --- | --- | --- |
| POST | `/auth/login` | All | FR-AUTH-01 | P0 |
| POST | `/auth/refresh` | All | FR-AUTH-02 | P0 |
| GET | `/dashboard/summary?country=` | All | FR-DASH-01–04, 06 | P0 |
| GET | `/customers?segment=&risk=&tier=&country=&city=&q=&sort=&page=` | All | FR-CUS-01–04 | P0 |
| GET | `/customers/{id}` | All | FR-CUS-05, 06 | P0 |
| GET | `/customers/export?<cùng bộ lọc>` | All | FR-CUS-07 | P0 |
| POST | `/predict?save=&dry_run=` | All | FR-PRED-01–03, FR-CUS-08 | P0 |
| POST | `/predict/batch` | All | FR-PRED-04 | P1 |
| GET | `/jobs/{job_id}` | All (job của mình) / Admin | FR-MDL-04 | P0 |
| GET | `/jobs/{job_id}/result` | All | FR-PRED-05 | P1 |
| GET | `/journeys` | All | FR-SEG-01 | P0 |
| PATCH | `/journeys/{journey_id}` | Admin | FR-SEG-04 | P1 |
| GET | `/models` | Admin | FR-MDL-01 | P0 |
| GET | `/models/active/importance` | All | FR-DASH-05 | P1 |
| GET | `/models/active/thresholds` | All (Marketer chỉ đọc) | FR-SEG-03 | P0 |
| PATCH | `/models/active/thresholds` | **Admin** | FR-SEG-03 | P1 |
| GET | `/models/compare?a=&b=` | Admin | FR-MDL-05 | P1 |
| POST | `/models/retrain` | Admin | FR-MDL-03 | P0 |
| PATCH | `/models/{version}/activate` | Admin | FR-MDL-06 | P0 |
| POST | `/datasets` | Admin | FR-MDL-02 | P1 |

## Mẫu request / response

### POST `/auth/login`

```json
// request
{ "username": "marketer", "password": "demo123" }

// 200
{ "access": "eyJ...", "refresh": "eyJ...", "user": { "username": "marketer", "role": "marketer" } }
```

### GET `/dashboard/summary`

```json
{
  "total_customers": 50000,
  "high_risk_rate": 0.247,
  "total_clv_expected": 21820000.00,
  "total_value_at_risk": 4970000.00,
  "model": { "version": "churn_v1", "scored_at": "2026-10-29T10:15:00+07:00" },
  "thresholds": { "tau": 0.5, "clv_p33": 143.0, "clv_p67": 342.0 },
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
    "value_at_risk": 968.22, "segment": "S1",
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
  "value_at_risk": 115.46, "segment": "S2",
  "journey": { "journey_id": "J2", "name": "Tiềm năng dễ mất" },
  "top_reasons": [ { "feature": "Customer_Service_Calls", "label": "Số lần gọi CSKH", "value": 8, "avg": 5.7, "shap": 0.11 } ],
  "imputed_fields": ["Session_Duration_Avg", "Social_Media_Engagement_Score"],
  "saved": false,
  "customer_id": null
}

// 400
{ "errors": { "City": "London không thuộc Country = USA" } }
```

### POST `/models/retrain` (Admin)

```json
// request
{ "dataset": "ml_engine/data/raw/ecommerce_customer_dataset.csv" }

// 202
{ "job_id": "8f1c…", "status": "queued" }
```

### GET `/jobs/{job_id}`

```json
{ "job_id": "8f1c…", "status": "running", "current_step": "train", "progress": 0.6, "log": ["validate ok", "clean ok"], "result_version": null }
```

### GET / PATCH `/models/active/thresholds`

```json
// GET (mọi vai trò)
{ "tau": 0.5, "clv_p33": 143.0, "clv_p67": 342.0, "g": 0.33, "d": 0.10, "horizon_years": 3, "editable": false }

// PATCH (chỉ Admin) — có thể gửi một phần
{ "tau": 0.6, "preview": true }

// 200 khi preview = true: chưa lưu, trả số khách mỗi segment theo ngưỡng mới
{ "preview": { "S1": 3100, "S2": 2950, "S3": 3800, "S4": 13400, "S5": 14000, "S6": 12750 } }
```

`editable` = `true` khi người gọi là Admin, để FE quyết định hiển thị ô nhập hay chỉ đọc.
