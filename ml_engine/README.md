# ml_engine — Pipeline ML và CLV

Phụ trách: **team BA & Model** (Khoa, Dương). Spec: [docs/02-FRD.md](../docs/02-FRD.md) mục 10, [docs/03-architecture.md](../docs/03-architecture.md) mục 3, [docs/05-clv-methodology.md](../docs/05-clv-methodology.md), [docs/07-data-dictionary.md](../docs/07-data-dictionary.md).

## Cấu trúc

```text
ml_engine/
├── data/raw/            # CSV gốc — đã commit, KHÔNG sửa tay
├── data/processed/      # train/val/test.csv do train.py sinh (split cố định, seed 42) — gitignore
├── src/
│   ├── clean.py         # FR-ML-01: CleanTransformer (6 nhóm lỗi, docs/07 mục 3)
│   ├── features.py      # FR-ML-01: 5 feature mới + encoding; build_preprocessor()
│   ├── train.py         # FR-ML-02, 05: lệnh build model + artifact (main)
│   ├── evaluate.py      # FR-ML-02: tune 3 thuật toán, hiệu chỉnh isotonic, τ theo F2, metrics
│   ├── clv.py           # FR-ML-04: CLV kỳ vọng / tiềm năng, VaR, P33/P67 (docs/05)
│   ├── segment.py       # FR-ML-04: risk, tier, segment, kênh (BR-01, 02, 04, 06, 07) + score()
│   └── explain.py       # FR-ML-03: SHAP → top 3 lý do (BR-05) + global importance
├── artifacts/           # version ACTIVE — commit (< 50 MB)
│   ├── churn_v1.joblib       # {model, raw_pipe, tau, algo, version}
│   ├── clv_config.json       # tham số cho ModelService (bảng dưới)
│   └── top_reasons.json.gz   # 3 lý do của 50.000 khách theo thứ tự dòng CSV (seed_db đọc)
├── reports/
│   ├── churn_tune.json  # kết quả tune 3 thuật toán, metrics test, calibration
│   └── figures/         # hình cho báo cáo (notebooks/02 sinh ra)
└── tests/               # pytest
```

## Lệnh chạy

```bash
pytest ml_engine/tests                      # ~15 giây
python -m ml_engine.src.train               # build lại artifact từ params đã tune, ~6 phút (SHAP cả tệp)
python -m ml_engine.src.train --tune        # tune lại 3 thuật toán từ đầu, ~1 giờ, ghi đè reports/churn_tune.json
python scripts/seed_db.py                   # nạp khách + chấm điểm vào DB, ~15 giây
```

Sau mỗi lần `train`: chạy lại `seed_db.py`, rồi Restart & Run All `notebooks/02`, `03` để số liệu và hình khớp model mới.

## Dùng trong backend (`ModelService`)

```python
import json, joblib
from ml_engine.src.segment import score

config = json.loads((ARTIFACT_DIR / "clv_config.json").read_text(encoding="utf-8"))
bundle = joblib.load(ARTIFACT_DIR / f"{config['version']}.joblib")
score(df_mau, bundle, config, explain=True)        # gọi 1 lần lúc khởi động: dựng SHAP explainer mất ~6 giây

out = score(df, bundle, config, explain=True)     # df: DataFrame 23 cột input, tên gốc như CSV; ~200 ms/khách
# cột: p_churn, risk_label, clv_pred, clv_potential, clv_tier, value_at_risk, segment, channel, imputed_fields, top_reasons
```

- `segment` S1–S6 ↔ lộ trình J1–J6 (`Journey.segment`).
- Danh sách khách / dashboard chỉ đọc prediction có `model_version == config["version"]` (version cũ giữ làm lịch sử).
- Dashboard "độ tin cậy mô hình" và "yếu tố ảnh hưởng" đọc `config["metrics"]` và `config["global_importance"]`.

### `clv_config.json`

| Khóa | Ý nghĩa | Dùng ở |
| --- | --- | --- |
| `version`, `trained_at` | Tên version (= tên file joblib), thời điểm build | Prediction.model_version, dashboard |
| `tau` | Ngưỡng churn (F2 trên validation, D-14) | BR-01 |
| `g`, `d`, `horizon`, `r_bar`, `freq_cap` | Tham số CLV (docs/05) | BR-03 |
| `P33`, `P67` | Ngưỡng tier CLV tiềm năng trên toàn tệp | BR-02 |
| `email_median` | Trung vị Email_Open_Rate tập train | BR-06 |
| `metrics` | ROC-AUC, PR-AUC, Recall, Precision, F1, F2, Brier, confusion matrix trên test | FR-DASH-05 |
| `global_importance` | Top 10 yếu tố theo mean \|SHAP\| | FR-DASH-06 |
| `feature_means` | Trung bình toàn tệp từng cột số | BR-05 ("trung bình 5,7") |

## Quy ước

- Mọi bước tiền xử lý nằm trong **một sklearn Pipeline** dùng chung cho train, seed và `/predict`. Không làm sạch thủ công trong notebook rồi copy kết quả.
- `random_state=42` ở mọi nơi; split 70/15/15 stratify cố định.
- Không dùng `Lifetime_Value` làm feature cho model churn (rò rỉ, docs/07).
- Ngưỡng làm sạch (median, p99) fit trên tập train; P33/P67 tính trên toàn tệp (BR-02). Tất cả lưu cùng artifact.
- Artifact **chỉ** sinh từ `python -m ml_engine.src.train`; notebook chỉ đọc. Chỉ commit artifact của version active.
- SHAP tính trên model chưa hiệu chỉnh (`raw_pipe`): isotonic đơn điệu nên không đổi thứ tự lý do. Model 900 cây sâu 31 tầng
  → ~7 ms/khách, vì vậy lý do của cả tệp tính sẵn lúc build.
