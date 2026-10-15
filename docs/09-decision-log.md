# 09 – Decision log

Ghi lại mọi quyết định đã chốt để không bàn lại. Muốn đổi một quyết định: mở issue, ghi lý do, cập nhật bảng này qua PR.

| # | Ngày | Quyết định | Lý do | Người chốt |
| --- | --- | --- | --- | --- |
| D-01 | 09/2026 | Dùng dataset tổng hợp `ecommerce_customer_dataset.csv` | Thầy đã duyệt | Thầy, Khoa |
| D-02 | 09/2026 | FE và BE tách riêng, không dùng Streamlit-only | Yêu cầu của môn học | Thầy |
| D-03 | 02/10 | Tech stack: Angular + Django + Git/GitHub | Thống nhất trong nhóm | Cả nhóm |
| D-04 | 02/10 | Database: **SQLite** thay MongoDB | Chạy local, không cần cài server, dùng trọn Django ORM/Admin/auth; đổi sang PostgreSQL chỉ cần sửa `DATABASES` | Khoa |
| D-05 | 02/10 | **Chạy local**, nộp link repo GitHub (tag `v1.0`) | Không cần deploy; giảm rủi ro hạ tầng | Khoa |
| D-06 | 02/10 | CLV = xác suất churn từ model kết hợp công thức AOV × tần suất × biên lợi nhuận × hệ số giữ chân | Thầy đã duyệt hướng tiếp cận | Thầy |
| D-07 | 02/10 | Cụ thể hóa CLV: horizon 3 năm, trừ hàng trả lại, g = 33%, d = 10%; hai giá trị CLV tiềm năng / kỳ vọng | Kết quả so sánh 6 biến thể ([05-clv-methodology.md](05-clv-methodology.md)); **đang chờ thầy góp ý** | Khoa |
| D-08 | 02/10 | BG/NBD chỉ dùng kiểm định chéo, không làm CLV chính thức | Khớp kém với nhãn churn (AUC 0,61 so với 0,92 của model ML) | Khoa |
| D-09 | 02/10 | Phân khúc bằng luật 2 × 3 (Risk × CLV tier); K-Means là P1 | Dễ giải thích, gắn thẳng hành động | Khoa |
| D-10 | 02/10 | **Chỉ Admin** được chỉnh ngưỡng churn, ngưỡng tier CLV và tham số CLV; Marketer chỉ xem | Tránh mỗi người một ngưỡng làm số liệu không nhất quán | Khoa |
| D-11 | 02/10 | Không làm A/B test thật; uplift chỉ mô phỏng | Không có khách thật, kênh gửi, thời gian quan sát | Khoa |
| D-12 | 02/10 | Retrain thủ công qua Job runner (thread/Django-Q), không Celery | Ít hạ tầng, đủ cho 1 job/lần | Khoa |
| D-13 | 02/10 | Commit CSV gốc và model `.joblib` active vào repo; không commit `db.sqlite3` | Thầy clone về chạy được ngay bằng `seed_db.py` | Khoa |
| D-14 | 13/10 | Model churn v1 = **LightGBM** đã hiệu chỉnh isotonic, **τ = 0,186** (tối ưu F2 trên validation, đúng BR-01) thay mốc tạm 0,5 | Tune Optuna 50 trial × 3 thuật toán, chọn theo PR-AUC 5-fold (LightGBM 0,884 > RF 0,872 > LR 0,611). Test: AUC 0,918, Recall 0,858, Precision 0,723. τ thấp là đúng lý thuyết (τ* ≈ F2*/5 với xác suất đã hiệu chỉnh). τ = 0,5 chỉ đạt Recall 0,761 → trượt tiêu chí ≥ 0,80. Admin vẫn nâng τ được (0,25–0,30 mất < 0,01 F2) nếu danh sách High quá dài. Chi tiết: `ml_engine/reports/churn_tune.json` | Khoa |
| D-15 | 15/10/2026 | Schema Django giai đoạn A: 23 thuộc tính Python viết thường, `db_column` giữ nguyên tên docs/07; kiểu/miền/null theo docs/02 mục 6; `Journey.kpi` là text; `model_type` chỉ có `churn`; CLV đi kèm version với khóa `g`, `d`, `horizon`, `P33`, `P67`; không có default τ | Nhất quán ORM, CSV và pipeline; không lưu `Lifetime_Value`/`Churned`, không impute trong model. Các trường hợp lệ vẫn có thể thiếu 14 input tùy chọn. | Tiến Đạt |
| D-16 | 15/10/2026 | `TrainingJob` bổ sung `progress`, FK `result_version`, FK `created_by`; thời điểm bắt đầu/kết thúc và hai FK đều nullable. BR-07 ràng buộc ở DB bằng partial unique index trên biểu thức hằng `1`, với điều kiện status thuộc queued/running | Khớp contract GET jobs và trạng thái chưa chạy. Đã xác minh SQLite 3.45.3 tạo index và chặn cả insert lẫn chuyển trạng thái gây hai job đang chờ/chạy. Không cần thêm trường kỹ thuật hay job runner trong giai đoạn A. | Tiến Đạt |

### Ghi chú triển khai D-15/D-16

- Unique có điều kiện trên `model_type` khi `is_active=True`; Prediction unique theo `(customer, model_version)`, cho phép giữ lịch sử version cũ.
- Xóa Customer kéo theo Prediction (`CASCADE`). Các tham chiếu ModelVersion/Journey dùng `PROTECT` để giữ lịch sử; xóa User chỉ xóa liên kết người tạo (`SET_NULL`). Admin không cho xóa Journey theo FR-SEG-04.
- WAL đã có tại `DATABASES.default.OPTIONS.init_command`; không bổ sung signal hoặc sửa settings.
- Choices, miền số, cặp country/city và cấu trúc JSON được kiểm tra khi `full_clean()`/Admin form chạy. `save()`, `update()` và `bulk_create()` không tự gọi `full_clean()`; import/seed và API phải validate trước khi ghi. Các unique constraint nêu trên vẫn được DB bảo vệ trực tiếp.
- API tiếp tục giữ tên trong docs/04; lớp API cần ánh xạ tên Python sang tên input gốc khi cần. Giai đoạn B chưa được phân công lại từ Huy, chưa triển khai.
