# ml_engine — Pipeline ML và CLV

Phụ trách: **team BA & Model** (Khoa, Dương). Spec: [docs/03-architecture.md](../docs/03-architecture.md) mục 3, [docs/05-clv-methodology.md](../docs/05-clv-methodology.md), [docs/07-data-dictionary.md](../docs/07-data-dictionary.md).

## Cấu trúc

```text
ml_engine/
├── data/raw/            # CSV gốc — đã commit, KHÔNG sửa tay
├── data/processed/      # train/val/test split, dữ liệu đã làm sạch — gitignore
├── src/
│   ├── ingest.py        # FR-ML-01: đọc CSV, sinh customer_id
│   ├── validate.py      # FR-ML-02: kiểm tra schema 25 cột
│   ├── clean.py         # FR-ML-03: CleanTransformer (6 nhóm lỗi)
│   ├── features.py      # FR-ML-04: feature engineering + encoding
│   ├── train.py         # FR-ML-05, 08: train, tune, register
│   ├── evaluate.py      # FR-ML-06: metrics, τ theo F2, calibration
│   ├── explain.py       # FR-ML-07: SHAP
│   ├── clv.py           # công thức CLV 3 năm (xem docs/05 mục 5)
│   ├── score.py         # FR-ML-09: batch score
│   └── segment.py       # BR-01, 02, 04: risk, tier, segment, journey
├── artifacts/           # churn_vX.joblib + clv_config.json của version ACTIVE (commit, < 50 MB)
├── reports/             # biểu đồ, bảng metrics cho báo cáo
└── tests/               # pytest
```

## Quy ước

- Mọi bước tiền xử lý nằm trong **một sklearn Pipeline** dùng chung cho train và `/predict`. Không làm sạch thủ công trong notebook rồi copy kết quả.
- `random_state=42` ở mọi nơi; file split cố định lưu trong `data/processed/`.
- Không dùng `Lifetime_Value` làm feature cho model churn.
- Ngưỡng làm sạch (median, p99) và tham số CLV fit trên train, lưu cùng artifact.
- Chỉ commit artifact của version active. Model thử nghiệm để trong `artifacts/experiments/` (gitignore).

## Chạy (khi đã có code)

```bash
pytest ml_engine/tests
python -m ml_engine.src.train --data ml_engine/data/raw/ecommerce_customer_dataset.csv
```
