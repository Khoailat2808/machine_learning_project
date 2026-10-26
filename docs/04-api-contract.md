# 04 – API contract

> Trạng thái: **v0.3 – khớp code đã chạy (26/10/2026)**: các endpoint P0 đã có, mẫu response lấy từ DB seed 50.000 khách · Phụ trách: Huy, Tiến · Mọi thay đổi phải qua PR có reviewer của cả FE và BE.

## Quy ước chung

- Base URL: `http://localhost:8000/api/v1`
- Header: `Authorization: Bearer <access_token>` (mọi endpoint trừ `/auth/login`)
- Định dạng: JSON, UTF-8; số thực trả về dạng number, tiền là USD làm tròn 2 chữ số.
- Phân trang: `?page=1` (50 dòng/trang), response có `count`, `next`, `previous`, `results`.
- Lỗi:

| Mã | Khi nào | Body |
| --- | --- | --- |
| 400 | Dữ liệu sai (`/predict`, `/campaigns/*`) | `{"errors": {"<tên trường>": "<thông báo tiếng Việt>"}}`; một chuỗi cho mỗi trường |
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

23 thuộc tính chia 4 nhóm, khóa là tên cột gốc (docs/07); trường trống trả `null`. `journey` là lộ trình của phân khúc (null nếu chưa seed lộ trình). Không có khách → 404 `{"detail": "Không tìm thấy khách hàng."}`.

```json
{
  "customer_id": "CUS16791",
  "attributes": {
    "profile": { "Age": 41, "Gender": "Female", "Country": "USA", "City": "Chicago", "Signup_Quarter": "Q2", "Membership_Years": 0.3 },
    "behavior": { "Login_Frequency": 20, "Session_Duration_Avg": 35.6, "Pages_Per_Session": 12.5, "Mobile_App_Usage": 23.9, "Wishlist_Items": 8, "Cart_Abandonment_Rate": 53.1 },
    "purchase": { "Total_Purchases": 17.0, "Average_Order_Value": 133.03, "Days_Since_Last_Purchase": null, "Discount_Usage_Rate": 52.9, "Returns_Rate": null, "Payment_Method_Diversity": 1, "Credit_Balance": 1348.0 },
    "engagement": { "Email_Open_Rate": 25.9, "Customer_Service_Calls": 7, "Product_Reviews_Written": 7, "Social_Media_Engagement_Score": 54.2 }
  },
  "prediction": {
    "p_churn": 0.942, "risk_label": "High",
    "clv_pred": 51.2, "clv_potential": 1180.75, "clv_tier": "High",
    "value_at_risk": 1112.27, "segment": "S1", "channel": "Phone",
    "top_reasons": [
      { "feature": "Customer_Service_Calls", "label": "Số lần gọi CSKH", "value": 7, "avg": 5.68, "shap": 0.21 }
    ],
    "model_version": "churn_v1",
    "scored_at": "2026-10-23T10:15:00+07:00"
  },
  "journey": {
    "journey_id": "J1", "name": "VIP nguy cơ", "goal": "Giữ lại",
    "steps": [ { "day": 0, "channel": "Phone", "action": "CSKH liên hệ cá nhân trong 48h, xử lý vấn đề tồn đọng", "offer": null } ],
    "kpi": "Mua lại trong 30 ngày, VaR giữ được, số khiếu nại được đóng",
    "max_spend_pct": 0.1
  }
}
```

> Số trong `prediction` chỉ minh họa định dạng.

`top_reasons`: tối đa 3 phần tử (BR-05), có thể ít hơn nếu không đủ yếu tố đẩy p_churn lên; `avg` = null với cột phân loại.

### GET `/journeys`

6 lộ trình sắp theo phân khúc S1 → S6, kèm điều kiện (BR-04), số khách và tổng VaR của version model đang dùng, ngưỡng chỉ đọc. `research` là nguồn nghiên cứu ([06](06-marketing-journeys.md) mục 2), cố định trong code.

```json
{
  "thresholds": { "tau": 0.18566, "clv_p33": 141.83, "clv_p67": 333.53 },
  "journeys": [
    {
      "journey_id": "J1", "segment": "S1", "name": "VIP nguy cơ", "risk": "High", "tier": "High",
      "count": 5330, "value_at_risk": 3106866.77, "goal": "Giữ lại",
      "steps": [ { "day": 0, "channel": "Phone", "action": "CSKH liên hệ cá nhân trong 48h, xử lý vấn đề tồn đọng", "offer": null } ],
      "kpi": "Mua lại trong 30 ngày, VaR giữ được, số khiếu nại được đóng",
      "max_spend_pct": 0.1,
      "research": ["Lemmens & Gupta 2020", "Knox & van Oest 2014", "Thomas et al. 2004"]
    }
  ]
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

// 200 (không lưu) · 201 (?save=true: tạo customer source = form + prediction, trả customer_id mới)
{
  "p_churn": 0.0587, "risk_label": "Low",
  "clv_pred": 306.14, "clv_potential": 181.61, "clv_tier": "Mid",
  "value_at_risk": 10.67, "segment": "S5", "channel": "Push app / SMS",
  "journey": {
    "journey_id": "J5", "name": "Ổn định cần nuôi", "goal": "Tăng giá trị",
    "steps": [ { "day": 0, "channel": "Email + App", "action": "Vào hạng Silver, hiển thị tiến độ lên Gold", "offer": null } ],
    "kpi": "AOV, số ngành hàng mỗi khách mua, tỷ lệ lên S4 sau 6 tháng",
    "max_spend_pct": 0.03
  },
  "top_reasons": [ { "feature": "Customer_Service_Calls", "label": "Số lần gọi CSKH", "value": 8.0, "avg": 5.68, "shap": 0.3938 } ],
  "imputed_fields": ["Session_Duration_Avg", "Social_Media_Engagement_Score"],
  "model_version": "churn_v1",
  "saved": false,
  "customer_id": null
}

// 400 — validate bằng model Customer: miền giá trị FR-PRED, City thuộc Country, trường bắt buộc
{ "errors": { "Age": "Đảm bảo giá trị này là nhỏ hơn hoặc bằng với 100 .", "City": "Thành phố không thuộc quốc gia đã chọn." } }
```

Chấm bằng cùng hàm `ml_engine.src.segment.score()` với `seed_db.py` → cùng input cho cùng p_churn. ~180 ms/lần; lần đầu sau khi khởi động backend ~5 giây (nạp model + SHAP).

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
// request — mọi trường tùy chọn; mặc định: segments ["S1","S2"], budget null (không giới hạn),
// spend_pct null (k của từng phân khúc, BR-08), success_rate 0.20
{
  "segments": ["S1", "S2"], "country": null, "city": null,
  "budget": 100000, "spend_pct": null, "success_rate": 0.20
}

// 200 — số thật trên DB seed
{
  "eligible": 10655, "selected": 548,
  "total_cost": 99937.73, "total_value_at_risk": 941670.71,
  "expected_saved": 188334.14, "roi": 0.8845, "break_even_rate": 0.1061,
  "by_segment": [
    { "segment": "S1", "selected": 548, "cost": 99937.73, "value_at_risk": 941670.71 },
    { "segment": "S2", "selected": 0, "cost": 0.0, "value_at_risk": 0.0 }
  ],
  "is_estimate": true
}

// 400
{ "errors": { "segments": "Chọn ít nhất một phân khúc.", "success_rate": "Phải từ 0.01 đến 1." } }
```

- BR-09: khách xếp VaR giảm dần (hòa thì theo customer_id); có `budget` thì dừng ở khách đầu tiên làm tổng chi phí vượt B → `total_cost ≤ budget`.
- `roi`, `break_even_rate` = `null` khi không chọn được khách (không chia cho 0).
- Miền: `budget > 0`, `spend_pct` 0,001–1, `success_rate` 0,01–1, `city` phải thuộc `country`.

### POST `/campaigns/export`

Cùng body với preview. Trả `text/csv` UTF-8 có BOM, file `chien_dich_<phân khúc>_YYYYMMDD.csv`; số dòng = `selected` của preview. Cột (dùng chung với `/customers/export`, file `khach_hang_YYYYMMDD.csv`):

`customer_id, country, city, segment, journey, channel, p_churn, clv_potential, value_at_risk, expected_cost, top_reason`

`expected_cost` = k × clv_potential (k của phân khúc hoặc `spend_pct` nếu ghi đè). Header `Content-Disposition` được expose qua CORS để FE đọc tên file.
