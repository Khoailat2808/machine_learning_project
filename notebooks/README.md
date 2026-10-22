# notebooks

Chỉ dùng cho EDA và thử nghiệm. Code chính thức nằm trong `ml_engine/src/`.

| Notebook | Nội dung | Phụ trách |
| --- | --- | --- |
| `01_eda.ipynb` | Phân phối, missing, outlier, phân tích theo nhãn churn, pipeline làm sạch chính thức | Dương |
| `02_churn_experiments.ipynb` | So sánh thuật toán, lịch sử tune, chọn τ, calibration, SHAP toàn tệp (đọc `reports/churn_tune.json`, không train lại) | Khoa |
| `03_clv_experiments.ipynb` | Biến thể CLV, độ nhạy d, CLV kỳ vọng và tiềm năng (đọc `artifacts/clv_config.json`) | Dương |

Quy ước: đặt tên `NN_mo-ta.ipynb`, đọc dữ liệu từ `../ml_engine/data/raw/`. Notebook **không ghi** vào `artifacts/` hay `data/processed/`;
artifact chỉ sinh từ `python -m ml_engine.src.train`.

## Chạy

```bash
pip install -r notebooks/requirements.txt
python -m ml_engine.src.train          # cần artifact trước khi chạy 02, 03
jupyter nbconvert --to notebook --execute --inplace notebooks/0*.ipynb   # Restart & Run All trước khi commit
```
