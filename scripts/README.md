# scripts

| Script | Việc làm | FR |
| --- | --- | --- |
| `seed_db.py` | Nạp 50.000 khách từ CSV vào `customers` (ID `CUS00001`… theo thứ tự dòng), tạo 6 lộ trình, 2 tài khoản demo, chấm điểm bằng model trong `ml_engine/artifacts/` và ghi `predictions` (kèm 3 lý do SHAP đã tính sẵn). ~15 giây. | FR-ML-06 |

Chạy từ thư mục gốc repo, sau `python backend/manage.py migrate`:

```bash
python scripts/seed_db.py
```

Chạy lại nhiều lần không tạo dữ liệu trùng:

- `customers`, `predictions`: upsert theo `customer_id` và (`customer_id`, `model_version`).
- Lộ trình và tài khoản demo chỉ tạo khi chưa có → nội dung đã sửa trong Django Admin và mật khẩu đã đổi được giữ nguyên.
- Sau khi train lại (`python -m ml_engine.src.train`), chạy lại script để chấm theo version mới; prediction của version cũ được giữ làm lịch sử.

Giá trị ngoài miền nhập liệu (Age < 13 hoặc > 100, Total_Purchases âm, tỷ lệ > 100%) được sửa như `CleanTransformer` trước khi ghi,
nên chấm lại từ DB vẫn ra cùng kết quả. Tài khoản demo lấy từ `.env` (`DEMO_ADMIN_*`, `DEMO_MARKETER_*`, xem `.env.example`).
