# scripts

| Script | Việc làm | FR |
| --- | --- | --- |
| `seed_db.py` | Nạp CSV vào `customers`, tạo 6 journey, 2 tài khoản demo (admin/marketer), đăng ký model trong `ml_engine/artifacts/`, batch score lần đầu. Chạy lại nhiều lần không tạo dữ liệu trùng. | FR-ML-10 |

Chạy từ thư mục gốc repo, sau `python backend/manage.py migrate`:

```bash
python scripts/seed_db.py
```
