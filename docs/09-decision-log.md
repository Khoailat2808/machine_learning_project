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
