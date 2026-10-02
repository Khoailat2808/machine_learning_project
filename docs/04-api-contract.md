# 04 – API contract

## Mục lục

1. [Quy ước chung](#1-quy-ước-chung)
2. [Kiểu dữ liệu và enum](#2-kiểu-dữ-liệu-và-enum)
3. [Lỗi](#3-lỗi)
4. [Danh sách endpoint](#4-danh-sách-endpoint)
5. [Auth](#5-auth)
6. [Dashboard](#6-dashboard)
7. [Customers](#7-customers)
8. [Predict](#8-predict)
9. [Jobs](#9-jobs)
10. [Journeys](#10-journeys)
11. [Scoring settings](#11-scoring-settings)
12. [Models và datasets](#12-models-và-datasets)
13. [Cấu hình DRF tương ứng](#13-cấu-hình-drf-tương-ứng)
14. [Changelog](#14-changelog)

---

## 1. Quy ước chung

| Mục | Quy ước |
| --- | --- |
| Base URL | `http://localhost:8000/api/v1` (mọi path bên dưới tính từ đây) |
| Định dạng | `Content-Type: application/json; charset=utf-8`, trừ upload file (`multipart/form-data`) và export (`text/csv`) |
| Xác thực | `Authorization: Bearer <access_token>` cho mọi endpoint, **trừ** `POST /auth/login`, `POST /auth/refresh`, `GET /health` |
| Tên trường JSON | `snake_case`. 23 thuộc tính khách = tên cột trong CSV viết thường (`Average_Order_Value` → `average_order_value`) |
| Thời gian | ISO 8601 có múi giờ, ví dụ `2026-10-29T10:15:00+07:00` (`TIME_ZONE = "Asia/Ho_Chi_Minh"`, `USE_TZ = True`) |
| Tiền | USD, kiểu number, làm tròn 2 chữ số |
| Xác suất | number trong [0, 1], làm tròn 4 chữ số (`p_churn`, `tau`, `gross_margin`, `discount_rate`) |
| Tỷ lệ % của khách | number trong [0, 100], giữ như dataset (`cart_abandonment_rate`, `returns_rate`, …) |
| Giá trị thiếu | `null` (không bỏ key) |
| Phân trang | `?page=<int ≥ 1>&page_size=<int 1–200>`, mặc định `page_size=50`; response theo `PageNumberPagination` của DRF (mục 7.1) |
| Trailing slash | Không dùng (`APPEND_SLASH = False`, router `trailing_slash=False`) |
| CORS | Cho phép `http://localhost:4200` |
| Idempotency | `GET` không đổi dữ liệu. `PATCH` gửi một phần trường. Các thao tác chạy nền trả `202` kèm `job_id` |

## 2. Kiểu dữ liệu và enum

| Enum | Giá trị | Ghi chú |
| --- | --- | --- |
| `role` | `admin`, `marketer` | Map từ Django Group `Admin` / `Marketer` |
| `segment` | `S1` … `S6` | Theo BR-04 |
| `risk_label` | `High`, `Low` | `High` khi `p_churn ≥ tau` |
| `clv_tier` | `High`, `Mid`, `Low` | Theo `clv_potential` so với `clv_p33`, `clv_p67` |
| `source` | `seed`, `form`, `upload` | Nguồn tạo khách |
| `job.type` | `retrain`, `rescore`, `batch_predict` | |
| `job.status` | `queued`, `running`, `succeeded`, `failed` | |
| `model.status` | `active`, `inactive` | Tại một thời điểm chỉ 1 version `active` |
| `gender` | `Male`, `Female`, `Other` | |
| `country` | `USA`, `UK`, `Canada`, `Germany`, `Australia`, `France`, `India`, `Japan` | |
| `city` | 40 giá trị, 5 thành phố mỗi nước | Xem [07-data-dictionary.md](07-data-dictionary.md) mục 2 |
| `signup_quarter` | `Q1`, `Q2`, `Q3`, `Q4` | |

| Định danh | Định dạng | Ví dụ |
| --- | --- | --- |
| `customer_id` | `CUS` + 5 chữ số, tăng dần; khách mới tiếp nối số lớn nhất | `CUS00001`, `CUS50001` |
| `version` (model) | `v` + số nguyên | `v1`, `v2` |
| `journey_id` | `J1` … `J6`, ứng với `S1` … `S6` | `J1` |
| `job_id`, `dataset_id` | UUID4 | `8f1c2e5a-…` |

### 2.1 Object dùng chung

**`CustomerAttributes`** — 23 thuộc tính đầu vào. Miền giá trị và trường bắt buộc theo bảng validate trong [02-functional-requirements.md](02-functional-requirements.md) mục 6.

| Trường | Kiểu | Bắt buộc khi chấm điểm |
| --- | --- | --- |
| `age` | integer \| null | Không |
| `gender` | enum | Có |
| `country` | enum | Có |
| `city` | enum (phải thuộc `country`) | Có |
| `signup_quarter` | enum | Có |
| `membership_years` | number | Có |
| `login_frequency` | integer | Có |
| `session_duration_avg` | number \| null | Không |
| `pages_per_session` | number \| null | Không |
| `cart_abandonment_rate` | number | Có |
| `wishlist_items` | integer \| null | Không |
| `total_purchases` | number | Có |
| `average_order_value` | number | Có |
| `days_since_last_purchase` | integer \| null | Không |
| `discount_usage_rate` | number \| null | Không |
| `returns_rate` | number \| null | Không |
| `email_open_rate` | number \| null | Không |
| `customer_service_calls` | integer \| null | Không |
| `product_reviews_written` | integer \| null | Không |
| `social_media_engagement_score` | number \| null | Không |
| `mobile_app_usage` | number \| null | Không |
| `payment_method_diversity` | integer \| null | Không |
| `credit_balance` | number \| null | Không |

**`Prediction`**

| Trường | Kiểu | Mô tả |
| --- | --- | --- |
| `p_churn` | number [0, 1] | Xác suất churn đã hiệu chỉnh |
| `risk_label` | enum | |
| `clv_expected` | number (USD) | CLV kỳ vọng 3 năm (dùng r riêng của khách) |
| `clv_potential` | number (USD) | CLV tiềm năng 3 năm (dùng r̄) |
| `clv_tier` | enum | |
| `value_at_risk` | number (USD) | `p_churn × clv_potential` |
| `segment` | enum | |
| `top_reasons` | `Reason[3]` | 3 yếu tố đẩy churn lên nhiều nhất |
| `model_version` | string | |
| `scored_at` | datetime | |

**`Reason`**

| Trường | Kiểu | Ví dụ |
| --- | --- | --- |
| `feature` | string (tên trường snake_case) | `customer_service_calls` |
| `label` | string (tiếng Việt) | `Số lần gọi CSKH` |
| `value` | number \| null | `12` |
| `population_median` | number | `5` |
| `shap_value` | number (> 0) | `0.2134` |

**`JourneySummary`**: `{ "journey_id": "J1", "segment": "S1", "name": "VIP nguy cơ" }`

## 3. Lỗi

Theo định dạng mặc định của DRF, không bọc thêm lớp ngoài.

| HTTP | Khi nào | Body |
| --- | --- | --- |
| 400 | Dữ liệu không hợp lệ | `{"<field>": ["<thông điệp>"], "non_field_errors": ["…"]}` |
| 401 | Thiếu, sai hoặc hết hạn token | `{"detail": "…", "code": "token_not_valid"}` (khi token hết hạn) |
| 403 | Đúng token nhưng sai vai trò | `{"detail": "Bạn không có quyền thực hiện thao tác này."}` |
| 404 | Không tồn tại | `{"detail": "Không tìm thấy."}` |
| 409 | Xung đột trạng thái (đang có job chạy) | `{"detail": "Đang có job chạy.", "code": "job_in_progress", "job_id": "<uuid>"}` |
| 413 | File vượt giới hạn | `{"detail": "File vượt quá 5 MB."}` |
| 422 | Cần xác nhận thêm (model mới kém hơn) | `{"detail": "…", "code": "metrics_regression", "comparison": {…}}` |
| 500 | Lỗi không mong muốn | `{"detail": "Lỗi hệ thống."}` — chi tiết chỉ ghi log server |

Ví dụ 400 khi validate khách:

```json
{
  "age": ["Đảm bảo giá trị nhỏ hơn hoặc bằng 100."],
  "city": ["London không thuộc country = USA."]
}
```

FE hiển thị thông điệp ngay dưới ô tương ứng; `non_field_errors` hiển thị ở đầu form.

## 4. Danh sách endpoint

| # | Method | Path | Quyền | Thành công | FR | Ưu tiên |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | GET | `/health` | Công khai | 200 | — | P0 |
| 2 | POST | `/auth/login` | Công khai | 200 | FR-AUTH-01 | P0 |
| 3 | POST | `/auth/refresh` | Công khai | 200 | FR-AUTH-02 | P0 |
| 4 | GET | `/auth/me` | Đăng nhập | 200 | FR-AUTH-03 | P0 |
| 5 | GET | `/dashboard/summary` | Đăng nhập | 200 | FR-DASH-01–04, 06 | P0 |
| 6 | GET | `/customers` | Đăng nhập | 200 | FR-CUS-01–04 | P0 |
| 7 | GET | `/customers/{customer_id}` | Đăng nhập | 200 | FR-CUS-05, 06 | P0 |
| 8 | GET | `/customers/export` | Đăng nhập | 200 (CSV) | FR-CUS-07 | P0 |
| 9 | POST | `/predict` | Đăng nhập | 200 / 201 | FR-PRED-01–03, FR-CUS-08 | P0 |
| 10 | POST | `/predict/batch` | Đăng nhập | 202 | FR-PRED-04 | P1 |
| 11 | GET | `/jobs/{job_id}` | Admin; Marketer chỉ job mình tạo | 200 | FR-MDL-04, FR-PRED-04 | P0 |
| 12 | GET | `/jobs/{job_id}/result` | Như #11 | 200 (CSV) | FR-PRED-05 | P1 |
| 13 | GET | `/journeys` | Đăng nhập | 200 | FR-SEG-01 | P0 |
| 14 | PATCH | `/journeys/{journey_id}` | **Admin** | 200 | FR-SEG-04 | P1 |
| 15 | GET | `/settings/scoring` | Đăng nhập | 200 | FR-SEG-03 | P0 |
| 16 | POST | `/settings/scoring/preview` | **Admin** | 200 | FR-SEG-03 | P1 |
| 17 | PATCH | `/settings/scoring` | **Admin** | 202 | FR-SEG-03 | P1 |
| 18 | GET | `/models` | **Admin** | 200 | FR-MDL-01 | P0 |
| 19 | GET | `/models/{version}` | **Admin** | 200 | FR-MDL-01 | P0 |
| 20 | GET | `/models/compare` | **Admin** | 200 | FR-MDL-05 | P1 |
| 21 | GET | `/models/active/feature-importance` | Đăng nhập | 200 | FR-DASH-05 | P1 |
| 22 | POST | `/models/retrain` | **Admin** | 202 | FR-MDL-03 | P0 |
| 23 | POST | `/models/{version}/activate` | **Admin** | 202 | FR-MDL-06 | P0 |
| 24 | GET | `/datasets` | **Admin** | 200 | FR-MDL-02 | P1 |
| 25 | POST | `/datasets` | **Admin** | 201 | FR-MDL-02 | P1 |

Marketer gọi endpoint **Admin** → `403`. FE vẫn phải ẩn menu/nút tương ứng, nhưng quyền thật luôn được kiểm tra ở backend.

---

## 5. Auth

Dùng `djangorestframework-simplejwt`. Access token sống **30 phút**, refresh token sống **1 ngày**, không xoay vòng refresh (`ROTATE_REFRESH_TOKENS = False`). Đăng xuất = FE xóa token khỏi bộ nhớ; backend không lưu blacklist.

### 5.1 `GET /health`

```json
// 200
{ "status": "ok", "model_loaded": true, "active_version": "v1" }
```

`model_loaded = false` khi chưa có model active (chưa chạy `seed_db.py`); vẫn trả 200.

### 5.2 `POST /auth/login`

| Trường request | Kiểu | Bắt buộc |
| --- | --- | --- |
| `username` | string | Có |
| `password` | string | Có |

```json
// request
{ "username": "marketer", "password": "demo123" }

// 200
{
  "access": "eyJhbGciOi…",
  "refresh": "eyJhbGciOi…",
  "user": { "id": 2, "username": "marketer", "role": "marketer" }
}

// 401 — một thông điệp chung, không nói sai username hay password
{ "detail": "Sai tên đăng nhập hoặc mật khẩu." }
```

### 5.3 `POST /auth/refresh`

```json
// request
{ "refresh": "eyJhbGciOi…" }

// 200
{ "access": "eyJhbGciOi…" }

// 401 — refresh hết hạn → FE chuyển về trang Login
{ "detail": "Token is invalid or expired", "code": "token_not_valid" }
```

Luồng FE: nhận 401 có `code = token_not_valid` ở request bất kỳ → gọi `/auth/refresh` một lần → thành công thì gửi lại request gốc; thất bại thì đăng xuất.

### 5.4 `GET /auth/me`

```json
// 200
{ "id": 1, "username": "admin", "role": "admin" }
```

---

## 6. Dashboard

### 6.1 `GET /dashboard/summary`

| Query | Kiểu | Mặc định | Ghi chú |
| --- | --- | --- | --- |
| `country` | enum | (tất cả) | Lọc mọi số liệu theo quốc gia (FR-DASH-06) |

Mọi con số tính trên prediction hiện hành của version `active` (BR-05), bằng truy vấn aggregate ở DB.

| Trường | Kiểu | Mô tả |
| --- | --- | --- |
| `total_customers` | integer | |
| `high_risk_count` | integer | Số khách `risk_label = High` |
| `high_risk_rate` | number [0, 1] | `high_risk_count / total_customers` |
| `avg_p_churn` | number [0, 1] | |
| `total_clv_expected` | number | Tổng `clv_expected` |
| `total_value_at_risk` | number | Tổng `value_at_risk` |
| `model` | object \| null | `{version, trained_at, scored_at}`; `null` nếu chưa có model |
| `scoring` | object | Giống response `GET /settings/scoring`, bỏ `editable`, `updated_*` |
| `segments` | array[6] | Luôn đủ 6 phần tử theo thứ tự S1…S6, kể cả khi `count = 0` |
| `segments[].segment` / `name` / `risk_label` / `clv_tier` | | |
| `segments[].count` | integer | |
| `segments[].share` | number [0, 1] | `count / total_customers` |
| `segments[].value_at_risk` | number | Tổng VaR của segment |
| `p_churn_histogram` | array[10] | Bin cố định `[0, 0.1)`, `[0.1, 0.2)`, …, `[0.9, 1.0]` |
| `p_churn_histogram[].bin_start` / `bin_end` / `count` | | |
| `by_country` | array | Sắp xếp `value_at_risk` giảm dần |
| `by_country[].country` / `count` / `high_risk_count` / `value_at_risk` | | |

```json
{
  "total_customers": 50000,
  "high_risk_count": 12348,
  "high_risk_rate": 0.247,
  "avg_p_churn": 0.2882,
  "total_clv_expected": 21816815.0,
  "total_value_at_risk": 4970481.0,
  "model": { "version": "v1", "trained_at": "2026-10-23T16:02:11+07:00", "scored_at": "2026-10-29T10:15:00+07:00" },
  "scoring": { "tau": 0.5, "clv_p33": 143.0, "clv_p67": 342.0, "gross_margin": 0.33, "discount_rate": 0.1, "horizon_years": 3 },
  "segments": [
    { "segment": "S1", "name": "VIP nguy cơ", "risk_label": "High", "clv_tier": "High", "count": 3837, "share": 0.0767, "value_at_risk": 2665288.0 },
    { "segment": "S2", "name": "Tiềm năng dễ mất", "risk_label": "High", "clv_tier": "Mid", "count": 3697, "share": 0.0739, "value_at_risk": 698530.0 },
    { "segment": "S3", "name": "Giá trị thấp rủi ro", "risk_label": "High", "clv_tier": "Low", "count": 4814, "share": 0.0963, "value_at_risk": 287784.0 },
    { "segment": "S4", "name": "Khách trung thành", "risk_label": "Low", "clv_tier": "High", "count": 12663, "share": 0.2533, "value_at_risk": 877674.0 },
    { "segment": "S5", "name": "Ổn định cần nuôi", "risk_label": "Low", "clv_tier": "Mid", "count": 13303, "share": 0.2661, "value_at_risk": 316213.0 },
    { "segment": "S6", "name": "Phổ thông", "risk_label": "Low", "clv_tier": "Low", "count": 11686, "share": 0.2337, "value_at_risk": 124992.0 }
  ],
  "p_churn_histogram": [
    { "bin_start": 0.0, "bin_end": 0.1, "count": 26276 },
    { "bin_start": 0.1, "bin_end": 0.2, "count": 5545 },
    { "bin_start": 0.2, "bin_end": 0.3, "count": 2501 },
    { "bin_start": 0.3, "bin_end": 0.4, "count": 1843 },
    { "bin_start": 0.4, "bin_end": 0.5, "count": 1487 },
    { "bin_start": 0.5, "bin_end": 0.6, "count": 1377 },
    { "bin_start": 0.6, "bin_end": 0.7, "count": 1313 },
    { "bin_start": 0.7, "bin_end": 0.8, "count": 1599 },
    { "bin_start": 0.8, "bin_end": 0.9, "count": 2165 },
    { "bin_start": 0.9, "bin_end": 1.0, "count": 5894 }
  ],
  "by_country": [
    { "country": "USA", "count": 17384, "high_risk_count": 4332, "value_at_risk": 1765970.0 },
    { "country": "UK", "count": 7534, "high_risk_count": 1876, "value_at_risk": 740032.0 },
    { "country": "Canada", "count": 6023, "high_risk_count": 1495, "value_at_risk": 610072.0 }
  ]
}
```

> Số liệu lấy từ lần chạy thử với model baseline (τ = 0,5); `by_country` rút gọn còn 3 nước. Khi chưa có prediction: `total_customers = 0`, `model = null`, `segments` vẫn đủ 6 phần tử với `count = 0` để FE hiển thị trạng thái trống.

---

## 7. Customers

### 7.1 `GET /customers`

| Query | Kiểu | Ghi chú |
| --- | --- | --- |
| `segment` | danh sách enum, phân cách dấu phẩy | `segment=S1,S2` |
| `risk_label` | enum | |
| `clv_tier` | enum | |
| `country` | enum | |
| `city` | enum | Nếu có `country` thì `city` phải thuộc `country`, ngược lại 400 |
| `search` | string ≥ 2 ký tự | Khớp một phần `customer_id`, không phân biệt hoa thường |
| `ordering` | một trong: `p_churn`, `-p_churn`, `clv_expected`, `-clv_expected`, `clv_potential`, `-clv_potential`, `value_at_risk`, `-value_at_risk`, `customer_id`, `-customer_id` | Mặc định `-value_at_risk`; giá trị khác bị bỏ qua |
| `page`, `page_size` | integer | Mục 1 |

Các điều kiện lọc kết hợp bằng AND.

```json
// GET /customers?segment=S1&country=USA&ordering=-value_at_risk&page=1
{
  "count": 1325,
  "next": "http://localhost:8000/api/v1/customers?country=USA&ordering=-value_at_risk&page=2&segment=S1",
  "previous": null,
  "results": [
    {
      "customer_id": "CUS01234",
      "country": "USA",
      "city": "Houston",
      "p_churn": 0.8213,
      "risk_label": "High",
      "clv_expected": 512.4,
      "clv_potential": 1180.75,
      "clv_tier": "High",
      "value_at_risk": 969.75,
      "segment": "S1",
      "journey": { "journey_id": "J1", "segment": "S1", "name": "VIP nguy cơ" }
    }
  ]
}
```

`page` vượt quá số trang → 404 `{"detail": "Invalid page."}` (mặc định DRF).

### 7.2 `GET /customers/{customer_id}`

```json
// 200
{
  "customer_id": "CUS01234",
  "source": "seed",
  "created_at": "2026-10-29T10:10:02+07:00",
  "attributes": {
    "age": 41, "gender": "Female", "country": "USA", "city": "Houston", "signup_quarter": "Q3",
    "membership_years": 3.2, "login_frequency": 6, "session_duration_avg": 18.2, "pages_per_session": 4.1,
    "cart_abandonment_rate": 78.0, "wishlist_items": 2, "total_purchases": 22.0, "average_order_value": 182.3,
    "days_since_last_purchase": 64, "discount_usage_rate": 31.5, "returns_rate": 4.2, "email_open_rate": 8.1,
    "customer_service_calls": 12, "product_reviews_written": 1, "social_media_engagement_score": null,
    "mobile_app_usage": 9.5, "payment_method_diversity": 2, "credit_balance": 2410.0
  },
  "prediction": {
    "p_churn": 0.8213,
    "risk_label": "High",
    "clv_expected": 512.4,
    "clv_potential": 1180.75,
    "clv_tier": "High",
    "value_at_risk": 969.75,
    "segment": "S1",
    "top_reasons": [
      { "feature": "customer_service_calls", "label": "Số lần gọi CSKH", "value": 12, "population_median": 5, "shap_value": 0.2134 },
      { "feature": "cart_abandonment_rate", "label": "Tỷ lệ bỏ giỏ hàng (%)", "value": 78.0, "population_median": 58.1, "shap_value": 0.1402 },
      { "feature": "email_open_rate", "label": "Tỷ lệ mở email (%)", "value": 8.1, "population_median": 19.7, "shap_value": 0.0911 }
    ],
    "model_version": "v1",
    "scored_at": "2026-10-29T10:15:00+07:00"
  },
  "journey": { "journey_id": "J1", "segment": "S1", "name": "VIP nguy cơ" }
}
```

- `attributes` trả giá trị **đã làm sạch** (ví dụ tỷ lệ đã clip về [0, 100]); giá trị bị impute vẫn trả `null` ở đây để người dùng biết dữ liệu gốc bị thiếu.
- `prediction = null` nếu khách chưa được chấm bởi version active (ví dụ ngay sau khi đổi version, trong lúc job `rescore` chạy).
- Chi tiết các bước của lộ trình lấy từ `GET /journeys` (FE cache), không lặp lại ở đây.
- Không tồn tại → 404 `{"detail": "Không tìm thấy."}`.

### 7.3 `GET /customers/export`

- Nhận **cùng query** với 7.1 trừ `page`, `page_size`; xuất **toàn bộ** kết quả (tối đa 50.000 dòng + khách mới).
- Response: `200`, `Content-Type: text/csv; charset=utf-8`, có BOM ở đầu file, `Content-Disposition: attachment; filename="customers_<YYYYMMDD-HHMM>.csv"`.
- Cột, đúng thứ tự:

```csv
customer_id,country,city,segment,journey_id,journey_name,risk_label,p_churn,clv_tier,clv_expected,clv_potential,value_at_risk,top_reason_1,top_reason_2,top_reason_3
CUS01234,USA,Houston,S1,J1,VIP nguy cơ,High,0.8213,High,512.40,1180.75,969.75,Số lần gọi CSKH,Tỷ lệ bỏ giỏ hàng (%),Tỷ lệ mở email (%)
```

---

## 8. Predict

### 8.1 `POST /predict`

Chấm một khách bằng version `active`. Dùng cho cả form khách mới (FR-PRED-01, 02) và what-if (FR-CUS-08).

| Trường request | Kiểu | Bắt buộc | Mô tả |
| --- | --- | --- | --- |
| `customer` | `CustomerAttributes` | Có | 23 trường; trường tùy chọn có thể là `null` hoặc bỏ qua |
| `save` | boolean | Không, mặc định `false` | `true` → tạo khách mới (`source = form`) và lưu prediction |

```json
// request
{
  "customer": {
    "age": 34, "gender": "Female", "country": "UK", "city": "London", "signup_quarter": "Q2",
    "membership_years": 1.5, "login_frequency": 8, "session_duration_avg": null, "pages_per_session": 6.2,
    "cart_abandonment_rate": 65.0, "wishlist_items": 3, "total_purchases": 7, "average_order_value": 95.5,
    "days_since_last_purchase": 40, "discount_usage_rate": 55.0, "returns_rate": 6.0, "email_open_rate": 12.0,
    "customer_service_calls": 8, "product_reviews_written": 1, "social_media_engagement_score": null,
    "mobile_app_usage": 14.0, "payment_method_diversity": 2, "credit_balance": 1500
  },
  "save": false
}
```

| Trường response | Kiểu | Mô tả |
| --- | --- | --- |
| `customer_id` | string \| null | `null` khi `save = false` |
| `saved` | boolean | |
| `prediction` | `Prediction` | |
| `journey` | `JourneySummary` | |
| `imputed_fields` | string[] | Các trường bị thiếu đã được điền bằng median train |

```json
// 200 (save = false)
{
  "customer_id": null,
  "saved": false,
  "prediction": {
    "p_churn": 0.6402, "risk_label": "High",
    "clv_expected": 98.1, "clv_potential": 180.4, "clv_tier": "Mid",
    "value_at_risk": 115.49, "segment": "S2",
    "top_reasons": [
      { "feature": "customer_service_calls", "label": "Số lần gọi CSKH", "value": 8, "population_median": 5, "shap_value": 0.1123 }
    ],
    "model_version": "v1",
    "scored_at": "2026-10-30T09:01:44+07:00"
  },
  "journey": { "journey_id": "J2", "segment": "S2", "name": "Tiềm năng dễ mất" },
  "imputed_fields": ["session_duration_avg", "social_media_engagement_score"]
}
```

- `save = true` → **201**, cùng body nhưng `customer_id = "CUS50001"`, `saved = true`, header `Location: /api/v1/customers/CUS50001`.
- Sai dữ liệu → 400 theo mục 3. Kiểm tra: kiểu, miền giá trị, trường bắt buộc, `city` thuộc `country`.
- Chưa có model active → 409 `{"detail": "Chưa có model active.", "code": "no_active_model"}`.
- Mục tiêu hiệu năng: p95 < 500 ms.
- What-if: FE gửi lại `customer` với vài trường đã đổi và `save = false`.

### 8.2 `POST /predict/batch` (P1)

- `multipart/form-data`, trường `file`: CSV ≤ 5 MB, ≤ 10.000 dòng.
- Header CSV dùng **tên cột gốc của dataset** (`Age`, `Gender`, …, 23 cột). Cột `Churned`, `Lifetime_Value` nếu có sẽ bị bỏ qua.
- Thiếu cột bắt buộc → 400 `{"file": ["Thiếu cột: Country, City"]}`; quá lớn → 413.
- Hợp lệ → **202** `{"job_id": "<uuid>", "type": "batch_predict", "status": "queued"}`.
- Dòng lỗi không làm hỏng cả job: bị bỏ qua và ghi vào `result.error_rows`. Dòng hợp lệ được lưu thành khách mới (`source = upload`).

---

## 9. Jobs

### 9.1 `GET /jobs/{job_id}`

| Trường | Kiểu | Mô tả |
| --- | --- | --- |
| `job_id` | uuid | |
| `type` | enum | `retrain`, `rescore`, `batch_predict` |
| `status` | enum | `queued`, `running`, `succeeded`, `failed` |
| `current_step` | string \| null | `retrain`: `validate`, `clean`, `features`, `train`, `evaluate`, `explain`, `register`; `rescore`/`batch_predict`: `score`, `clv`, `segment`, `write` |
| `progress` | number [0, 1] | |
| `created_by` | string | username |
| `created_at`, `started_at`, `finished_at` | datetime \| null | |
| `log` | string[] | 50 dòng cuối |
| `error` | string \| null | Có giá trị khi `failed` |
| `result` | object \| null | Theo `type`, có khi `succeeded` |

`result` theo loại job:

| `type` | `result` |
| --- | --- |
| `retrain` | `{ "version": "v2", "metrics": {…}, "is_active": false }` — retrain **không** tự activate |
| `rescore` | `{ "version": "v2", "customers_scored": 50000, "duration_seconds": 41.2 }` |
| `batch_predict` | `{ "rows_total": 1000, "rows_scored": 987, "error_rows": [ { "row": 14, "errors": { "Age": ["…"] } } ], "download_url": "/api/v1/jobs/<uuid>/result" }` |

```json
// 200
{
  "job_id": "8f1c2e5a-3b1d-4c55-9a0e-6d2a1f7c9b10",
  "type": "retrain",
  "status": "running",
  "current_step": "train",
  "progress": 0.55,
  "created_by": "admin",
  "created_at": "2026-10-30T14:00:00+07:00",
  "started_at": "2026-10-30T14:00:01+07:00",
  "finished_at": null,
  "log": ["[14:00:01] validate ok (50000 rows)", "[14:00:09] clean ok", "[14:00:15] features ok"],
  "error": null,
  "result": null
}
```

FE polling 3 giây/lần, dừng khi `status` là `succeeded` hoặc `failed`. Marketer xem job không phải của mình → 404 (không tiết lộ job tồn tại).

### 9.2 `GET /jobs/{job_id}/result` (P1)

Chỉ cho `batch_predict` đã `succeeded`. Trả CSV (BOM, UTF-8) gồm 23 cột gốc + `customer_id, segment, journey_id, risk_label, p_churn, clv_tier, clv_expected, clv_potential, value_at_risk`. Job chưa xong → 409 `{"detail": "Job chưa hoàn tất.", "code": "job_not_finished"}`.

---

## 10. Journeys

### 10.1 `GET /journeys`

Không phân trang, luôn trả 6 phần tử theo thứ tự J1…J6.

```json
[
  {
    "journey_id": "J1",
    "segment": "S1",
    "name": "VIP nguy cơ",
    "objective": "Giữ lại",
    "max_spend_pct": 0.10,
    "customer_count": 3837,
    "steps": [
      { "day": 0, "channel": "Phone", "action": "CSKH liên hệ cá nhân, xử lý vấn đề tồn đọng", "offer": null },
      { "day": 2, "channel": "Email", "action": "Tặng quyền lợi phi giá", "offer": "Miễn phí vận chuyển 3 tháng" },
      { "day": 7, "channel": "Email", "action": "Nếu chưa mua lại: gửi voucher", "offer": "Giảm 10–15%, hạn 14 ngày" },
      { "day": 30, "channel": "Email", "action": "Khảo sát hài lòng 1 câu", "offer": null }
    ],
    "kpis": ["Tỷ lệ mua lại 30 ngày", "VaR giữ được", "Số khiếu nại được đóng"],
    "updated_at": "2026-10-29T10:10:02+07:00"
  }
]
```

`max_spend_pct` là tỷ lệ tối đa so với `clv_potential` của từng khách. Nội dung mặc định của 6 journey lấy từ [06-marketing-journeys.md](06-marketing-journeys.md).

### 10.2 `PATCH /journeys/{journey_id}` (Admin, P1)

Trường được sửa: `name`, `objective`, `max_spend_pct` (0–0,5), `steps`, `kpis`. Không sửa được `journey_id`, `segment`. `steps` phải có ≥ 1 phần tử, `day` là integer ≥ 0 tăng dần.

```json
// request
{ "steps": [ { "day": 0, "channel": "Email", "action": "Nhắc giỏ hàng", "offer": null } ] }
```

Response 200: object journey đầy đủ như 10.1. Không có endpoint tạo/xóa journey.

---

## 11. Scoring settings

Gom các ngưỡng và tham số CLV (BR-01, BR-02, BR-10). Chỉ Admin được thay đổi.

### 11.1 `GET /settings/scoring`

```json
// 200
{
  "tau": 0.5,
  "clv_p33": 143.0,
  "clv_p67": 342.0,
  "gross_margin": 0.33,
  "discount_rate": 0.1,
  "horizon_years": 3,
  "updated_at": "2026-10-29T10:10:02+07:00",
  "updated_by": "admin",
  "editable": false
}
```

`editable = true` khi người gọi là Admin. FE dựa vào trường này để hiển thị ô nhập hay chỉ đọc.

### 11.2 `POST /settings/scoring/preview` (Admin)

Gửi một phần hoặc toàn bộ tham số; **không lưu**. Trả số khách và VaR mỗi segment theo tham số mới (ví dụ dưới: tăng τ từ 0,5 lên 0,6 làm S1 giảm từ 3.837 xuống 3.507 khách; tổng VaR không đổi vì τ chỉ đổi cách chia nhóm).

| Trường | Kiểu | Miền hợp lệ |
| --- | --- | --- |
| `tau` | number | 0,05–0,95 |
| `clv_p33`, `clv_p67` | number | > 0 và `clv_p33 < clv_p67` |
| `gross_margin` | number | 0,05–0,90 |
| `discount_rate` | number | 0–0,30 |
| `horizon_years` | integer | 1–5 |

```json
// request
{ "tau": 0.6 }

// 200
{
  "settings": { "tau": 0.6, "clv_p33": 143.0, "clv_p67": 342.0, "gross_margin": 0.33, "discount_rate": 0.1, "horizon_years": 3 },
  "segments": [
    { "segment": "S1", "count": 3507, "value_at_risk": 2537577.0 },
    { "segment": "S2", "count": 3248, "value_at_risk": 643218.0 },
    { "segment": "S3", "count": 4216, "value_at_risk": 262094.0 },
    { "segment": "S4", "count": 12993, "value_at_risk": 1005385.0 },
    { "segment": "S5", "count": 13752, "value_at_risk": 371526.0 },
    { "segment": "S6", "count": 12284, "value_at_risk": 150681.0 }
  ],
  "total_value_at_risk": 4970481.0
}
```

### 11.3 `PATCH /settings/scoring` (Admin)

Body giống 11.2. Lưu tham số rồi tạo job `rescore` để tính lại CLV, VaR, segment cho toàn bộ khách **không chạy lại model**.

```json
// 202
{
  "job_id": "<uuid>", "type": "rescore", "status": "queued",
  "settings": { "tau": 0.6, "clv_p33": 143.0, "clv_p67": 342.0, "gross_margin": 0.33, "discount_rate": 0.1, "horizon_years": 3 }
}
```

- Marketer → 403, tham số không đổi.
- Đang có job khác chạy → 409 (BR-07).
- Khi activate một model version mới (12.6), `clv_p33`/`clv_p67` được **tính lại** từ dữ liệu (BR-02) và ghi đè giá trị cũ; `tau` lấy theo ngưỡng F2 của version đó.

---

## 12. Models và datasets

### 12.1 Object `ModelVersion`

| Trường | Kiểu | Mô tả |
| --- | --- | --- |
| `version` | string | |
| `status` | enum | `active` / `inactive` |
| `algorithm` | string | Ví dụ `LightGBM` |
| `trained_at` | datetime | |
| `dataset_id` | uuid \| `"raw-default"` | Dataset dùng để train |
| `metrics` | object | `{roc_auc, pr_auc, recall, precision, f1, brier}` trên tập test |
| `tau` | number | Ngưỡng F2 của version |
| `clv_spearman_ltv` | number | Spearman(CLV tiềm năng, Lifetime_Value) |
| `params` | object | Hyperparameter (chỉ có ở `GET /models/{version}`) |

### 12.2 `GET /models`

Không phân trang, sắp xếp `trained_at` giảm dần.

```json
[
  {
    "version": "v2", "status": "inactive", "algorithm": "LightGBM",
    "trained_at": "2026-10-30T14:06:40+07:00", "dataset_id": "raw-default",
    "metrics": { "roc_auc": 0.9312, "pr_auc": 0.8954, "recall": 0.8421, "precision": 0.7710, "f1": 0.8050, "brier": 0.0911 },
    "tau": 0.41, "clv_spearman_ltv": 0.6142
  }
]
```

### 12.3 `GET /models/{version}`

Như 12.2 kèm `params`. Không tồn tại → 404.

### 12.4 `GET /models/compare?a=<version>&b=<version>` (P1)

```json
{
  "a": { "version": "v1", "metrics": { "roc_auc": 0.9201, "recall": 0.8100 } },
  "b": { "version": "v2", "metrics": { "roc_auc": 0.9312, "recall": 0.8421 } },
  "diff": { "roc_auc": 0.0111, "recall": 0.0321 }
}
```

`diff = b − a` cho từng metric. Thiếu `a` hoặc `b` → 400.

### 12.5 `POST /models/retrain`

```json
// request — dataset_id tùy chọn, mặc định "raw-default" (CSV gốc trong repo)
{ "dataset_id": "raw-default", "note": "Thử thêm feature service_friction" }

// 202
{ "job_id": "<uuid>", "type": "retrain", "status": "queued" }

// 409 — đã có job queued/running (BR-07)
{ "detail": "Đang có job chạy.", "code": "job_in_progress", "job_id": "<uuid>" }
```

Job thành công tạo version mới ở trạng thái `inactive`; Admin phải activate (12.6).

### 12.6 `POST /models/{version}/activate`

| Trường request | Kiểu | Mặc định | Mô tả |
| --- | --- | --- | --- |
| `confirm` | boolean | `false` | Bắt buộc `true` nếu version mới kém hơn version đang active (BR-08) |

Quy tắc BR-08: cho activate ngay nếu `roc_auc ≥ roc_auc_active − 0,01` **và** `recall ≥ recall_active − 0,01`.

```json
// 202 — activate xong, tạo job rescore toàn bộ khách
{ "version": "v2", "job_id": "<uuid>", "type": "rescore", "status": "queued" }

// 422 — kém hơn và chưa confirm
{
  "detail": "Version v2 có metrics thấp hơn version đang active. Gửi lại với confirm = true để tiếp tục.",
  "code": "metrics_regression",
  "comparison": { "active": { "version": "v1", "roc_auc": 0.9201, "recall": 0.8100 }, "candidate": { "version": "v2", "roc_auc": 0.9012, "recall": 0.7800 } }
}
```

- Version đang active → 400 `{"detail": "Version này đang active."}`.
- Đang có job chạy → 409. Không tồn tại → 404.
- Rollback = activate một version cũ.
- Trong lúc job `rescore` chạy, dashboard và danh sách vẫn đọc prediction của version cũ cho tới khi job ghi xong (ghi trong một transaction).

### 12.7 `GET /models/active/feature-importance` (P1)

| Query | Kiểu | Mặc định |
| --- | --- | --- |
| `top` | integer 1–30 | 10 |

```json
[
  { "feature": "customer_service_calls", "label": "Số lần gọi CSKH", "mean_abs_shap": 0.1845 },
  { "feature": "cart_abandonment_rate", "label": "Tỷ lệ bỏ giỏ hàng (%)", "mean_abs_shap": 0.1612 }
]
```

### 12.8 `GET /datasets` và `POST /datasets` (Admin, P1)

`POST` dùng `multipart/form-data`, trường `file`: CSV ≤ 50 MB, phải có đủ 25 cột như [07-data-dictionary.md](07-data-dictionary.md). Không ghi đè dataset nào.

```json
// 201
{ "dataset_id": "3c7d…", "filename": "customers_2026_11.csv", "rows": 52000, "uploaded_by": "admin", "uploaded_at": "2026-11-02T09:00:00+07:00" }

// 400 — sai schema
{ "file": ["Sai schema."], "schema_errors": [ { "column": "Churned", "problem": "missing" }, { "column": "Age", "problem": "not_numeric" } ] }
```

`GET /datasets` trả mảng các object như 201, kèm dataset mặc định `{"dataset_id": "raw-default", "filename": "ecommerce_customer_dataset.csv", "rows": 50000}`.

---

## 13. Cấu hình DRF tương ứng

Để các quy ước trên đúng “tự nhiên” mà không phải viết tay nhiều:

```python
# backend/config/settings.py (trích)
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.StandardPagination",  # page_size=50, page_size_query_param="page_size", max_page_size=200
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",      # ?search=
        "rest_framework.filters.OrderingFilter",    # ?ordering=
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False,
}
APPEND_SLASH = False
TIME_ZONE = "Asia/Ho_Chi_Minh"
USE_TZ = True
CORS_ALLOWED_ORIGINS = ["http://localhost:4200"]
```

- Permission `IsAdminRole` kiểm tra user thuộc Group `Admin`, gắn vào các view đánh dấu **Admin** ở mục 4.
- `segment=S1,S2` dùng `BaseInFilter` của django-filter.
- Mock API tuần 2: trả đúng các ví dụ JSON trong file này (BE có thể đặt trong `backend/mocks/*.json`).

## 14. Changelog

| Phiên bản | Ngày | Thay đổi |
| --- | --- | --- |
| 1.0.0-draft | 02/10/2026 | Bản đầy đủ đầu tiên: 25 endpoint, quy ước kiểu dữ liệu, lỗi, phân trang, jobs, scoring settings |
