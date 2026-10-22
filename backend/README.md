# backend — Django + DRF

Phụ trách: **team BE** (Đạt, Huy). Spec: [docs/03-architecture.md](../docs/03-architecture.md), [docs/04-api-contract.md](../docs/04-api-contract.md), [docs/02-FRD.md](../docs/02-FRD.md).

## Cấu trúc dự kiến

```text
backend/
├── manage.py
├── requirements.txt          # ghim phiên bản (pip freeze)
├── config/                   # settings.py, urls.py, wsgi.py
└── apps/
    ├── accounts/             # login, JWT (FR-AUTH)
    ├── customers/            # Customer model, list/filter/detail/export (FR-CUS, FR-DASH)
    ├── predictions/          # Prediction, Journey, /predict, /model/info, ModelService (FR-PRED, FR-SEG)
    └── campaigns/            # /campaigns/preview, export, Campaign (FR-CAMP)
```

## Thư viện chính

`django>=5.0,<5.3`, `djangorestframework`, `djangorestframework-simplejwt`, `django-cors-headers`, `django-filter`, cộng các thư viện của `ml_engine` (pandas, scikit-learn, lightgbm, shap, joblib).

## Quy ước

- Prefix API: `/api/v1`. Response/lỗi theo đúng [04-api-contract.md](../docs/04-api-contract.md).
- `ModelService` là singleton, load model **một lần** khi khởi động.
- Mọi view yêu cầu đăng nhập (`IsAuthenticated`); không có phân quyền theo vai trò ([02-FRD.md](../docs/02-FRD.md) mục 2).
- SQLite bật WAL mode; batch ghi bằng `bulk_create(update_conflicts=True)` lô 1.000 dòng.
- Tuần 2 phải có **mock API** trả JSON mẫu để FE làm song song.
