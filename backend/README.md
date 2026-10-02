# backend — Django + DRF

Phụ trách: **team BE** (Đạt, Huy). Spec: [docs/03-architecture.md](../docs/03-architecture.md), [docs/04-api-contract.md](../docs/04-api-contract.md), [docs/02-functional-requirements.md](../docs/02-functional-requirements.md).

## Cấu trúc dự kiến

```text
backend/
├── manage.py
├── requirements.txt          # ghim phiên bản (pip freeze)
├── config/                   # settings.py, urls.py, wsgi.py
└── apps/
    ├── accounts/             # login, JWT, Group Marketer/Admin (FR-AUTH)
    ├── customers/            # Customer model, list/filter/detail/export (FR-CUS, FR-DASH)
    ├── predictions/          # Prediction, Journey, /predict, ModelService (FR-PRED, FR-SEG)
    └── models_mgmt/          # ModelVersion, TrainingJob, retrain, activate (FR-MDL)
```

## Thư viện chính

`django>=5.0,<5.3`, `djangorestframework`, `djangorestframework-simplejwt`, `django-cors-headers`, `django-filter`, cộng các thư viện của `ml_engine` (pandas, scikit-learn, lightgbm, shap, joblib).

## Quy ước

- Prefix API: `/api/v1`. Response/lỗi theo đúng [04-api-contract.md](../docs/04-api-contract.md).
- `ModelService` là singleton, load model **một lần** khi khởi động.
- Kiểm tra quyền ở mọi view theo ma trận trong [02-functional-requirements.md](../docs/02-functional-requirements.md) mục 1; đặc biệt `PATCH /models/active/thresholds` và mọi API `/models` chỉ cho Admin.
- SQLite bật WAL mode; batch ghi bằng `bulk_create(update_conflicts=True)` lô 1.000 dòng.
- Tuần 2 phải có **mock API** trả JSON mẫu để FE làm song song.
