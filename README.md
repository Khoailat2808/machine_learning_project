# Team 09 – Webapp hỗ trợ marketing: giữ chân khách theo churn và CLV

Đồ án môn **Machine Learning in Business** (lớp 261BIM401401, GV: thầy Trần Duy Thanh), nhóm 09, UEL.

Webapp nội bộ giúp **bộ phận marketing** của một doanh nghiệp thương mại điện tử trả lời 3 câu hỏi trước mỗi chiến dịch giữ chân:

1. **Giữ ai?** Mô hình học máy dự báo xác suất rời bỏ (churn), kết hợp giá trị vòng đời (CLV) thành **Value at Risk = P(churn) × CLV tiềm năng** để xếp hạng khách.
2. **Làm gì với họ?** 6 phân khúc (rủi ro × CLV), mỗi phân khúc một lộ trình marketing có cơ sở nghiên cứu, kèm 3 lý do rủi ro của từng khách (SHAP).
3. **Chi bao nhiêu, thu về gì?** Mô phỏng chiến dịch (chi phí, giá trị kỳ vọng giữ lại, ROI, tỷ lệ hòa vốn) và xuất danh sách khách để gửi email/SMS.

> Hạn nộp: **09/11/2026**. Sản phẩm chạy local; nộp link repo (tag `v1.0`), báo cáo và slide.

## Tech stack

| Lớp | Công nghệ |
| --- | --- |
| Frontend | Angular 17+, Angular Material, Chart.js (ng2-charts) |
| Backend | Django 5 + Django REST Framework, simplejwt |
| Database | SQLite (Django ORM, bật WAL mode) |
| ML | Python 3.11, pandas, scikit-learn, LightGBM, SHAP, Optuna, joblib |
| Version control | Git + GitHub, GitHub Projects |

## Cấu trúc repo

```text
team09-churn-clv/
├── frontend/            # Angular app — team FE (Tiến, Thành)
├── backend/             # Django project — team BE (Đạt, Huy)
├── ml_engine/           # Pipeline ML + CLV — team BA & Model (Khoa, Dương)
│   ├── data/raw/        # CSV gốc (đã commit)
│   ├── data/processed/  # dữ liệu trung gian (gitignore)
│   ├── src/             # clean, features, train, evaluate, clv, segment, explain
│   ├── artifacts/       # model .joblib, clv_config.json, top_reasons.json.gz của version active
│   ├── reports/         # churn_tune.json, figures/ cho báo cáo
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
| 1 | [BRD](docs/01-BRD.md) – vấn đề của marketing, mục tiêu, người dùng, phạm vi, chỉ số thành công | Cả nhóm |
| 2 | [FRD](docs/02-FRD.md) – luồng làm việc, 33 FR, quy tắc nghiệp vụ, acceptance criteria | Cả nhóm |
| 3 | [Kiến trúc & data model](docs/03-architecture.md) – pipeline, bảng DB, xử lý lỗi | BE, BA & Model |
| 4 | [API contract](docs/04-api-contract.md) – endpoint, request/response mẫu | FE, BE |
| 5 | [Phương pháp CLV](docs/05-clv-methodology.md) – công thức, tham số, so sánh phương án | BA & Model |
| 6 | [Lộ trình marketing](docs/06-marketing-journeys.md) – 6 lộ trình và nguồn nghiên cứu | BA & Model, FE |
| 7 | [Data dictionary](docs/07-data-dictionary.md) – 25 cột, lỗi dữ liệu, quy tắc làm sạch | BA & Model, BE |
| 8 | [Plan & checklist](docs/08-plan-and-checklist.md) – task theo tuần, deadline | Cả nhóm |
| 9 | [Decision log](docs/09-decision-log.md) – các quyết định đã chốt và lý do | Cả nhóm |

Quy trình làm việc với git: [CONTRIBUTING.md](CONTRIBUTING.md).

## Chạy local (sẽ hoàn thiện ở tuần 5)

Yêu cầu: Python 3.11, Node 20.19+ (hoặc 22, 24 — Angular 21), Git.

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

Tài khoản demo do `seed_db.py` tạo: `marketer` (web) và `admin` (Django Admin) (mật khẩu ghi trong `.env.example`).

## Thành viên

| Sub-team | Thành viên | Phụ trách chính |
| --- | --- | --- |
| BA & Model | Trần Anh Khoa (leader), Dương | Spec, EDA, model churn, CLV, phân khúc, báo cáo |
| Frontend | Tiến, Thành | Angular: Tổng quan, Khách hàng, Lộ trình, Chiến dịch, Chấm điểm |
| Backend | Đạt, Huy | Django API, auth, ModelService, campaign, seed |
