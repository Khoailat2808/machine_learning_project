# 02 – Functional requirements

> 7 module, 43 yêu cầu chức năng (33 P0, 10 P1). P0 = bắt buộc cho bản nộp 09/11, P1 = làm nếu còn thời gian.
> Dùng mã FR làm tiêu đề issue/PR, ví dụ `[FR-CUS-02] filter theo segment`.

## 1. Vai trò và phân quyền

| Module | Marketer | Admin | System (`ml_engine`) |
| --- | --- | --- | --- |
| AUTH – Đăng nhập | Đăng nhập, đăng xuất | + quản lý tài khoản | — |
| DASH – Dashboard | Xem | Xem | — |
| CUS – Khách hàng | Xem, lọc, xuất CSV | Xem, lọc, xuất CSV | — |
| PRED – Chấm điểm | Chấm 1 khách, chấm file | Chấm 1 khách, chấm file | — |
| SEG – Phân khúc & lộ trình | **Chỉ xem** (ngưỡng hiển thị dạng chỉ đọc) | Xem, sửa nội dung lộ trình, chỉnh ngưỡng và tham số CLV | — |
| MDL – Dữ liệu & mô hình | Không truy cập (403) | Upload, retrain, so sánh, activate | — |
| ML – Pipeline | — | Kích hoạt gián tiếp qua MDL | Clean, train, đánh giá, tính CLV, chấm điểm, ghi DB |

## 2. Quy tắc nghiệp vụ chung (BR)

Mọi ngưỡng/tham số lưu trong DB (bảng `model_registry` và `clv_config`), không hard-code trong FE/BE.

| Mã | Quy tắc |
| --- | --- |
| BR-01 | `risk_label` = High nếu p_churn ≥ τ, ngược lại Low. τ mặc định là ngưỡng tối ưu F2 trên validation; Admin chỉnh trong khoảng 0,05–0,95. |
| BR-02 | `clv_tier` = Low nếu clv_potential < P33, Mid nếu P33 ≤ clv_potential < P67, High nếu ≥ P67. P33/P67 tính trên toàn tệp ở lần batch score gần nhất và được lưu lại; khách mới dùng ngưỡng đã lưu. |
| BR-03 | `value_at_risk` = p_churn × clv_potential (USD, làm tròn 2 chữ số). Công thức CLV: [05-clv-methodology.md](05-clv-methodology.md). |
| BR-04 | Phân khúc: High+High = S1, High+Mid = S2, High+Low = S3, Low+High = S4, Low+Mid = S5, Low+Low = S6 (risk_label + clv_tier). Mỗi segment gắn đúng 1 journey. |
| BR-05 | Mỗi khách có đúng 1 prediction hiện hành, của model version đang active. Prediction của version cũ được giữ để so sánh. |
| BR-06 | `top_reasons` = 3 feature có SHAP dương lớn nhất của model churn, hiển thị tên tiếng Việt kèm giá trị thực của khách. |
| BR-07 | Tối đa 1 training job ở trạng thái queued/running tại một thời điểm. |
| BR-08 | Version mới được activate ngay nếu ROC-AUC ≥ AUC cũ − 0,01 và Recall ≥ Recall cũ − 0,01; nếu kém hơn, Admin phải xác nhận lần hai. |
| BR-09 | Trường được phép trống khi chấm điểm là những trường có missing trong dữ liệu gốc; impute bằng median của tập train. |
| BR-10 | Chỉ Admin được thay đổi τ, P33/P67, g (biên lợi nhuận), d (lãi suất chiết khấu). |

## 3. FR-AUTH — Đăng nhập và phân quyền

| Mã | Chức năng | Mô tả và quy tắc | API / màn hình | Ưu tiên |
| --- | --- | --- | --- | --- |
| FR-AUTH-01 | Đăng nhập | Username + mật khẩu → JWT access (30 phút) + refresh (1 ngày). Sai thông tin hiện một thông báo chung. | `POST /auth/login` · Login | P0 |
| FR-AUTH-02 | Duy trì / kết thúc phiên | FE tự refresh token; đăng xuất xóa token. Refresh hết hạn thì đăng nhập lại. | `POST /auth/refresh` | P0 |
| FR-AUTH-03 | Phân quyền theo vai trò | API kiểm tra quyền theo ma trận mục 1. Marketer gọi API MDL nhận 403; menu Models ẩn; vào thẳng `/models` bị chuyển về Dashboard. | Middleware + route guard | P0 |
| FR-AUTH-04 | Quản lý tài khoản | Admin tạo, khóa tài khoản, gán vai trò; bản P0 dùng Django Admin. | `/admin/` | P1 |

Acceptance criteria

- [ ] `admin` và `marketer` đăng nhập được ngay sau `seed_db.py`.
- [ ] Gọi API bất kỳ (trừ login) không có token → 401.
- [ ] Marketer gọi `POST /models/retrain` → 403, không tạo job.

## 4. FR-DASH — Dashboard

| Mã | Chức năng | Mô tả và quy tắc | API / màn hình | Ưu tiên |
| --- | --- | --- | --- | --- |
| FR-DASH-01 | Thẻ KPI | Tổng khách, % High risk, tổng CLV kỳ vọng, tổng VaR, version model active + ngày chấm. | `GET /dashboard/summary` | P0 |
| FR-DASH-02 | Ma trận 2 × 3 | Mỗi ô: tên segment, số khách, % tổng, tổng VaR. Nhấn mạnh S1. | `GET /dashboard/summary` | P0 |
| FR-DASH-03 | Đi tới danh sách | Bấm một ô → Customers lọc sẵn segment đó, sắp xếp VaR giảm dần. | Router | P0 |
| FR-DASH-04 | Biểu đồ phân bố | Histogram p_churn (10 bin, vạch τ); cột số khách + VaR theo quốc gia. | `GET /dashboard/summary` | P0 |
| FR-DASH-05 | Yếu tố ảnh hưởng toàn cục | Top 10 feature theo mean \|SHAP\|, tên tiếng Việt. | `GET /models/active/feature-importance` | P1 |
| FR-DASH-06 | Lọc theo quốc gia | Dropdown Country, tính lại toàn bộ thẻ và biểu đồ. | `GET /dashboard/summary?country=` | P1 |

Acceptance criteria

- [ ] Tổng 6 ô ma trận = thẻ tổng số khách.
- [ ] Dashboard tải < 2 giây với 50.000 khách (aggregate ở DB, không tải toàn bộ bản ghi về FE).
- [ ] Chưa có prediction → trạng thái trống hướng dẫn chạy `seed_db.py`, không lỗi trang.

## 5. FR-CUS — Quản lý khách hàng

| Mã | Chức năng | Mô tả và quy tắc | API / màn hình | Ưu tiên |
| --- | --- | --- | --- | --- |
| FR-CUS-01 | Danh sách | Phân trang 50 dòng: customer_id, country, p_churn (%), risk_label, clv_expected, clv_tier, VaR, segment. Mặc định VaR giảm dần. | `GET /customers` | P0 |
| FR-CUS-02 | Lọc | AND theo segment (nhiều lựa chọn), risk_label, clv_tier, country, city (phụ thuộc country). Bộ lọc nằm trên URL query. | `GET /customers?segment=&risk_label=&clv_tier=&country=&city=` | P0 |
| FR-CUS-03 | Tìm kiếm | Theo customer_id, khớp một phần. | `GET /customers?search=` | P0 |
| FR-CUS-04 | Sắp xếp | Theo p_churn, clv_expected, clv_potential, VaR (tăng/giảm). | `GET /customers?ordering=-value_at_risk` | P0 |
| FR-CUS-05 | Hồ sơ khách | 23 thuộc tính nhóm theo Hành vi / Mua sắm / Tương tác; p_churn, CLV kỳ vọng (`clv_expected`), CLV tiềm năng (`clv_potential`), VaR, segment; lộ trình đề xuất. | `GET /customers/{customer_id}` | P0 |
| FR-CUS-06 | Giải thích dự đoán | 3 lý do chính (BR-06), ví dụ “Gọi CSKH 12 lần (trung bình 5,7)”. | `GET /customers/{customer_id}` | P0 |
| FR-CUS-07 | Xuất CSV | Toàn bộ kết quả của bộ lọc (không chỉ trang hiện tại); UTF-8 có BOM. | `GET /customers/export` | P0 |
| FR-CUS-08 | What-if | Kéo 4 biến can thiệp được (Customer_Service_Calls, Cart_Abandonment_Rate, Email_Open_Rate, Discount_Usage_Rate) xem p_churn, segment đổi. Không lưu DB. | `POST /predict` (`save: false`) | P1 |

Acceptance criteria

- [ ] Lọc S1 + USA trả đúng số dòng so với truy vấn trực tiếp DB.
- [ ] Customer id không tồn tại → 404 và trang “Không tìm thấy khách hàng”.
- [ ] CSV mở bằng Excel không lỗi font; số dòng = số kết quả bộ lọc.
- [ ] Bộ lọc không ra kết quả → trạng thái trống có nút “Xóa bộ lọc”.

## 6. FR-PRED — Chấm điểm khách mới

| Mã | Chức năng | Mô tả và quy tắc | API / màn hình | Ưu tiên |
| --- | --- | --- | --- | --- |
| FR-PRED-01 | Chấm 1 khách | Form 23 trường (bảng dưới). Trả p_churn, risk_label, clv_expected, clv_potential, clv_tier, VaR, segment, journey, 3 lý do; < 500 ms. | `POST /predict` | P0 |
| FR-PRED-02 | Lưu khách mới | Bấm “Lưu vào danh sách” → tạo customer (source = form) + prediction. Không bấm thì không ghi DB. | `POST /predict` (`save: true`) | P0 |
| FR-PRED-03 | Báo lỗi nhập liệu | Angular chặn tại ô; BE trả 400 dạng `{field: message}`. | Serializer + Reactive Forms | P0 |
| FR-PRED-04 | Chấm hàng loạt | Upload CSV ≤ 10.000 dòng; dòng lỗi bỏ qua và liệt kê (số dòng + lý do). | `POST /predict/batch` → job_id | P1 |
| FR-PRED-05 | Tải kết quả | CSV kết quả (cột gốc + cột dự đoán) và file lỗi. | `GET /jobs/{id}/result` | P1 |

### Bảng validate 23 trường input

| Trường | Kiểu | Miền hợp lệ | Bắt buộc |
| --- | --- | --- | --- |
| Age | số nguyên | 13–100 | Tùy chọn |
| Gender | chọn | Male, Female, Other | Bắt buộc |
| Country | chọn | USA, UK, Canada, Germany, Australia, France, India, Japan | Bắt buộc |
| City | chọn | 5 thành phố theo Country (xem [data dictionary](07-data-dictionary.md)) | Bắt buộc |
| Signup_Quarter | chọn | Q1–Q4 | Bắt buộc |
| Membership_Years | số thực | 0–10 | Bắt buộc |
| Login_Frequency | số nguyên | 0–50 | Bắt buộc |
| Session_Duration_Avg (phút) | số thực | 0–120 | Tùy chọn |
| Pages_Per_Session | số thực | 0–30 | Tùy chọn |
| Cart_Abandonment_Rate (%) | số thực | 0–100 | Bắt buộc |
| Wishlist_Items | số nguyên | 0–50 | Tùy chọn |
| Total_Purchases | số thực | 0–150 | Bắt buộc |
| Average_Order_Value (USD) | số thực | > 0 và ≤ 10.000 | Bắt buộc |
| Days_Since_Last_Purchase | số nguyên | 0–365 | Tùy chọn |
| Discount_Usage_Rate (%) | số thực | 0–100 | Tùy chọn |
| Returns_Rate (%) | số thực | 0–100 | Tùy chọn |
| Email_Open_Rate (%) | số thực | 0–100 | Tùy chọn |
| Customer_Service_Calls | số nguyên | 0–30 | Tùy chọn |
| Product_Reviews_Written | số nguyên | 0–30 | Tùy chọn |
| Social_Media_Engagement_Score | số thực | 0–100 | Tùy chọn |
| Mobile_App_Usage | số thực | 0–100 | Tùy chọn |
| Payment_Method_Diversity | số nguyên | 1–5 | Tùy chọn |
| Credit_Balance (USD) | số thực | 0–10.000 | Tùy chọn |

Acceptance criteria

- [ ] Cùng một input, `/predict` và batch score cho cùng p_churn (sai số < 0,001).
- [ ] Age = 200 bị chặn ở FE; gọi thẳng API → 400 kèm lỗi trường Age.
- [ ] Bỏ trống mọi trường tùy chọn vẫn chấm được, kết quả ghi “14 trường được ước lượng”.

## 7. FR-SEG — Phân khúc và lộ trình

| Mã | Chức năng | Mô tả và quy tắc | API / màn hình | Ưu tiên |
| --- | --- | --- | --- | --- |
| FR-SEG-01 | Xem 6 lộ trình | Mỗi segment một thẻ: tên, điều kiện (BR-04), số khách, các bước theo ngày (kênh, hành động, ưu đãi), KPI. | `GET /journeys` | P0 |
| FR-SEG-02 | Gán segment + journey tự động | Mỗi lần tạo/cập nhật prediction đều tính segment (BR-01, 02, 04) và gắn journey. | Service nội bộ | P0 |
| FR-SEG-03 | Chỉnh ngưỡng (chỉ Admin) | Admin đổi τ, P33/P67 và g, d; xem trước số khách mỗi segment, xác nhận thì cập nhật lại segment toàn bộ khách mà không chạy lại model. | `POST /settings/scoring/preview`, `PATCH /settings/scoring` | P1 |
| FR-SEG-04 | Sửa nội dung lộ trình | Admin sửa tên, bước, ưu đãi; không được xóa journey. | `PATCH /journeys/{id}` | P1 |

Acceptance criteria

- [ ] Sau seed: đủ 6 journey, mọi khách có segment + journey.
- [ ] Đổi τ 0,5 → 0,7: số khách High risk giảm, tổng 6 segment vẫn bằng tổng khách.
- [ ] Marketer gọi `PATCH /settings/scoring` → 403, ngưỡng không đổi; giao diện Marketer chỉ hiển thị ngưỡng dạng chỉ đọc.

## 8. FR-MDL — Dữ liệu và mô hình (Admin)

| Mã | Chức năng | Mô tả và quy tắc | API / màn hình | Ưu tiên |
| --- | --- | --- | --- | --- |
| FR-MDL-01 | Danh sách version | Loại, thuật toán, ngày train, metrics (AUC, Recall, F1), tham số CLV (g, d), τ, trạng thái active. | `GET /models` | P0 |
| FR-MDL-02 | Upload dataset | CSV ≤ 50 MB; kiểm tra đủ 25 cột, đúng kiểu; sai thì liệt kê lỗi, không ghi đè. | `POST /datasets` | P1 |
| FR-MDL-03 | Retrain | Chọn dataset → tạo training job chạy nền (BR-07). Nút khóa khi đang có job. | `POST /models/retrain` → job_id | P0 |
| FR-MDL-04 | Theo dõi job | queued/running/done/failed, bước hiện tại, log; FE polling 3 giây. | `GET /jobs/{id}` | P0 |
| FR-MDL-05 | So sánh version | 2 version cùng loại → bảng metrics cạnh nhau và chênh lệch. | `GET /models/compare?a=&b=` | P1 |
| FR-MDL-06 | Activate / rollback | Activate theo BR-08, rồi tự batch score lại toàn bộ khách. | `POST /models/{version}/activate` | P0 |

Acceptance criteria

- [ ] Retrain trên CSV gốc xong → version mới xuất hiện cùng metrics.
- [ ] Job lỗi → failed có log; version active và dashboard không đổi.
- [ ] Retrain lần 2 khi job đầu chưa xong → 409.
- [ ] Activate version cũ → dashboard hiển thị số liệu version đó sau khi batch score xong.

## 9. FR-ML — Chức năng hệ thống của `ml_engine`

| Mã | Chức năng | Mô tả và quy tắc | File | Ưu tiên |
| --- | --- | --- | --- | --- |
| FR-ML-01 | Ingest | Đọc CSV, sinh customer_id CUS00001… nếu chưa có. | `ingest.py` | P0 |
| FR-ML-02 | Validate | Schema 25 cột, kiểu, miền giá trị; báo lỗi theo cột. | `validate.py` | P0 |
| FR-ML-03 | Clean | 6 nhóm lỗi trong [data dictionary](07-data-dictionary.md); dạng sklearn transformer. | `clean.py` | P0 |
| FR-ML-04 | Feature engineering | 5 feature mới + encoding; chung một Pipeline cho train và inference. | `features.py` | P0 |
| FR-ML-05 | Train + tune | ≥ 3 thuật toán cho model churn (LR, RF, LightGBM/XGBoost); Optuna/RandomizedSearchCV; 5-fold CV; seed 42. | `train.py` | P0 |
| FR-ML-06 | Evaluate | Metrics trên test, chọn τ theo F2, hiệu chỉnh xác suất (isotonic), xuất báo cáo vào `reports/`. | `evaluate.py` | P0 |
| FR-ML-07 | Explain | SHAP TreeExplainer: global importance + top 3 lý do mỗi khách. | `explain.py` | P0 |
| FR-ML-08 | Register | Lưu `.joblib` + `clv_config.json`, ghi metadata + metrics + ngưỡng vào `model_registry`. | `train.py` | P0 |
| FR-ML-09 | Batch score + CLV + segment | Chấm toàn bộ khách, tính CLV kỳ vọng và tiềm năng theo công thức 3 năm, VaR, segment, journey; `bulk_create` lô 1.000 dòng; 50.000 khách < 2 phút. | `score.py`, `clv.py`, `segment.py` | P0 |
| FR-ML-10 | Seed demo | `python scripts/seed_db.py`: nạp CSV, 6 journey, 2 tài khoản demo, đăng ký model đã commit, batch score lần đầu. Chạy lại không tạo trùng. | `scripts/seed_db.py` | P0 |

Acceptance criteria

- [ ] `train.py` chạy 2 lần cùng dữ liệu cho cùng metrics.
- [ ] `pytest ml_engine/tests` pass, có test cho từng quy tắc làm sạch và cho `clv.py`.
- [ ] Máy mới clone repo, chạy `seed_db.py` một lần là dashboard có đủ 50.000 khách.
