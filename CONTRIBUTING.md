# Quy trình làm việc với Git

Mục tiêu: `main` luôn chạy được, ai cũng biết mình đang làm gì, và không ai ghi đè code của người khác.

## Nhánh

```text
main        ← chỉ nhận merge từ develop vào cuối tuần, gắn tag v0.1 … v1.0
 └─ develop ← nhánh tích hợp hằng ngày
     └─ feature/<team>-<mô-tả-ngắn>
```

| Team | Tiền tố | Ví dụ |
| --- | --- | --- |
| BA & Model | `feature/ml-` | `feature/ml-clean-pipeline`, `feature/ml-clv` |
| Frontend | `feature/fe-` | `feature/fe-dashboard`, `feature/fe-predict-form` |
| Backend | `feature/be-` | `feature/be-customers-api`, `feature/be-retrain-job` |
| Sửa lỗi | `fix/` | `fix/be-predict-validation` |
| Tài liệu | `docs/` | `docs/api-contract-v1` |

Luôn tạo nhánh từ `develop` mới nhất:

```bash
git checkout develop
git pull
git checkout -b feature/fe-dashboard
```

## Commit

Theo [Conventional Commits](https://www.conventionalcommits.org/), viết tiếng Việt hoặc tiếng Anh đều được, miễn ngắn và rõ:

```text
feat(fe): thêm bộ lọc segment cho danh sách khách
fix(be): trả 400 khi Age ngoài khoảng 13–100
exp(ml): thử LightGBM + Optuna 50 trials
docs: cập nhật API contract cho /predict
test(ml): thêm test cho clean.py
```

Loại commit: `feat`, `fix`, `exp` (thử nghiệm ML), `docs`, `test`, `refactor`, `chore`.

## Pull request

1. Push nhánh, mở PR vào `develop`, điền theo template.
2. Gắn PR với issue tương ứng (`Closes #12`) và ghi mã FR trong tiêu đề, ví dụ `[FR-CUS-02] filter theo segment`.
3. Cần **1 reviewer**. PR chạm vào API contract (`docs/04-api-contract.md`, serializer, service gọi API) phải có 1 người của team còn lại review (FE ↔ BE).
4. Không tự merge PR của chính mình.
5. Sau khi merge, xóa nhánh feature.

## Không commit những thứ này

- `.env`, mật khẩu, token
- `db.sqlite3` (mỗi người tự dựng bằng `scripts/seed_db.py`)
- `ml_engine/data/processed/`, `node_modules/`, `__pycache__/`, `.venv/`
- File `.joblib` > 50 MB hoặc model thử nghiệm (chỉ commit model của version active)
- Output notebook quá nặng: clear output trước khi commit nếu > 5 MB

## Theo dõi công việc

- Mỗi task trong checklist của nhóm là một issue trên GitHub Projects (dùng template *Task*).
- Cột board: `Todo` → `In progress` → `In review` → `Done`.
- Bị chặn quá 1 ngày thì nhắn nhóm ngay, ghi lý do vào issue.

## Thiết lập lần đầu cho repo (chỉ leader làm)

Trên GitHub → Settings → Branches → Add rule cho `main`:

- Require a pull request before merging (1 approval)
- Do not allow bypassing the above settings

Settings → Collaborators: mời 5 thành viên và thầy (nếu repo private).
