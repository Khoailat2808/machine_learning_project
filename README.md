# Team 09 – Dự báo churn, ước tính CLV và cá nhân hóa lộ trình marketing

Đồ án môn **Machine Learning in Business** (lớp 261BIM401401, GV: thầy Trần Duy Thanh), nhóm 09, UEL.

Hệ thống web nội bộ cho doanh nghiệp thương mại điện tử:

1. **Dự báo xác suất rời bỏ (churn)** cho từng khách hàng bằng mô hình học máy.
2. **Ước tính giá trị vòng đời (CLV)** bằng công thức chiết khấu lợi nhuận ròng 3 năm, dùng xác suất churn làm tỷ lệ giữ chân.
3. **Xếp khách vào 6 phân khúc** (rủi ro cao/thấp × CLV High/Mid/Low) và **gán lộ trình marketing** có cơ sở nghiên cứu cho từng phân khúc.
4. Ưu tiên hành động theo **Value at Risk = P(churn) × CLV tiềm năng**.

> Hạn nộp: **09/11/2026**. Sản phẩm chạy local; nộp link repo (tag `v1.0`), báo cáo và slide.

## Tech stack

| Lớp | Công nghệ |
| --- | --- |
| Frontend | Angular 17+, Angular Material, Chart.js (ng2-charts) |
| Backend | Django 5 + Django REST Framework, simplejwt |
| Database | SQLite (Django ORM, bật WAL mode) |
| ML | Python 3.11, pandas, scikit-learn, LightGBM/XGBoost, SHAP, Optuna, joblib |
| Version control | Git + GitHub, GitHub Projects |

## Cấu trúc repo

```text
machine_learning_project/
├── frontend/            # Angular app — team FE (Tiến, Thành)
├── backend/             # Django project — team BE (Đạt, Huy)
├── ml_engine/           # Pipeline ML + CLV — team BA & Model (Khoa, Dương)
│   ├── data/raw/        # CSV gốc (đã commit)
│   ├── data/processed/  # dữ liệu trung gian (gitignore)
│   ├── src/             # ingest, validate, clean, features, train, evaluate, explain, clv, score, segment
│   ├── artifacts/       # model .joblib + clv_config.json của version active
│   ├── reports/         # biểu đồ, bảng metrics
│   └── tests/
├── notebooks/           # EDA và thử nghiệm (không phải code chính thức)
├── scripts/             # seed_db.py: dựng DB + chấm điểm lần đầu
├── docs/                # toàn bộ spec và tài liệu thiết kế
└── .github/             # template PR / issue
```

## Tài liệu

Đọc theo thứ tự này nếu mới vào dự án:

| # | Tài liệu | Ai cần đọc kỹ |
| --- | --- | --- |
| 1 | [Product spec](docs/01-product-spec.md) – bài toán, mục tiêu, phạm vi, phân khúc | Cả nhóm |
| 2 | [Functional requirements](docs/02-functional-requirements.md) – 43 FR, quy tắc nghiệp vụ, acceptance criteria | Cả nhóm |
| 3 | [Kiến trúc & data model](docs/03-architecture.md) – pipeline, bảng DB, xử lý lỗi | BE, BA & Model |
| 4 | [API contract](docs/04-api-contract.md) – 25 endpoint, kiểu dữ liệu, lỗi, request/response mẫu | FE, BE |
| 5 | [Phương pháp CLV](docs/05-clv-methodology.md) – công thức, tham số, so sánh phương án | BA & Model |
| 6 | [Lộ trình marketing](docs/06-marketing-journeys.md) – 6 lộ trình và nguồn nghiên cứu | BA & Model, FE |
| 7 | [Data dictionary](docs/07-data-dictionary.md) – 25 cột, lỗi dữ liệu, quy tắc làm sạch | BA & Model, BE |

Quy trình làm việc với git: [CONTRIBUTING.md](CONTRIBUTING.md).

## Chạy local (sẽ hoàn thiện ở tuần 5)

Yêu cầu: Python 3.11, Node 20 LTS, Git.

```bash
# 1. Backend + ML
python -m venv .venv
# Windows: .venv\Scripts\activate    |  macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env

# 2. Dựng database + chấm điểm 50.000 khách
python backend/manage.py migrate
python scripts/seed_db.py

# 3. Chạy backend
python backend/manage.py runserver        # http://localhost:8000

# 4. Chạy frontend (terminal khác)
cd frontend && npm ci && npm start        # http://localhost:4200
```

Tài khoản demo do `seed_db.py` tạo: `admin` / `marketer` (mật khẩu ghi trong `.env.example`).

## Thành viên

| Sub-team | Thành viên | Phụ trách chính |
| --- | --- | --- |
| BA & Model | Trần Anh Khoa (leader), Dương | Spec, EDA, model churn, CLV, phân khúc, báo cáo |
| Frontend | Tiến, Thành | Angular: Dashboard, Customers, Predict, Models, Journeys |
| Backend | Đạt, Huy | Django API, auth, ModelService, job runner, seed |
