"""FR-ML-06: nạp 50.000 khách, 6 lộ trình, tài khoản demo và chấm điểm vào DB. Chạy lại không tạo trùng.

Chạy từ root repo, sau `python backend/manage.py migrate`:
    python scripts/seed_db.py

Sau khi train lại (`python -m ml_engine.src.train`): chạy lại script để chấm theo version mới;
prediction của version cũ được giữ làm lịch sử (unique theo customer + model_version).
"""
import gzip
import json
import os
import sys
import time
from pathlib import Path

import joblib
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
BATCH = 1000
SCORE_FIELDS = ("p_churn", "risk_label", "clv_pred", "clv_potential", "clv_tier", "value_at_risk", "segment", "channel")

# docs/06-marketing-journeys.md; nội dung sửa tiếp qua Django Admin (seed không ghi đè)
JOURNEYS = [
    dict(journey_id="J1", segment="S1", name="VIP nguy cơ", goal="Giữ lại", max_spend_pct=0.10,
         kpi="Mua lại trong 30 ngày, VaR giữ được, số khiếu nại được đóng",
         steps=[dict(day=0, channel="Phone", action="CSKH liên hệ cá nhân trong 48h, xử lý vấn đề tồn đọng", offer=None),
                dict(day=2, channel="Email", action="Gửi quyền lợi phi giá", offer="Miễn phí vận chuyển 3 tháng, hỗ trợ ưu tiên"),
                dict(day=7, channel="Email / Push", action="Nếu chưa mua lại: gửi voucher", offer="Voucher 10–15%, hạn 14 ngày"),
                dict(day=30, channel="Email", action="Khảo sát hài lòng 1 câu", offer=None)]),
    dict(journey_id="J2", segment="S2", name="Tiềm năng dễ mất", goal="Giữ lại", max_spend_pct=0.05,
         kpi="Tỷ lệ khôi phục giỏ, mua lại 30 ngày, tỷ lệ dùng voucher (càng thấp càng tốt)",
         steps=[dict(day=0, channel="Email / Push", action="Nhắc giỏ hàng, hiển thị sẵn tổng chi phí", offer=None),
                dict(day=2, channel="Email / Push", action="Link thanh toán không cần đăng nhập lại",
                     offer="Miễn phí vận chuyển cho giỏ đó"),
                dict(day=5, channel="Email", action="Gợi ý sản phẩm thay thế từ wishlist", offer=None),
                dict(day=10, channel="Email", action="Chỉ gửi khi vẫn chưa mua", offer="Voucher 10%, hạn 7 ngày")]),
    dict(journey_id="J3", segment="S3", name="Giá trị thấp rủi ro", goal="Tìm lý do, chi phí thấp", max_spend_pct=0.02,
         kpi="Tỷ lệ trả lời khảo sát, chi phí trên mỗi khách giữ được, phân bố lý do rời bỏ",
         steps=[dict(day=0, channel="Email", action="Khảo sát 1 câu: lý do ít mua (giá, vận chuyển, sản phẩm, dịch vụ)",
                     offer=None),
                dict(day=3, channel="Email", action="Chỉ với khách chọn giá hoặc vận chuyển",
                     offer="Miễn phí vận chuyển đơn kế tiếp"),
                dict(day=14, channel="Email", action="Không phản hồi: chuyển về nhịp newsletter của S6, không voucher lớn",
                     offer=None)]),
    dict(journey_id="J4", segment="S4", name="Khách trung thành", goal="Khuếch đại", max_spend_pct=0.03,
         kpi="Khách mới từ giới thiệu, retention 12 tháng, tỷ lệ chuyển sang rủi ro cao",
         steps=[dict(day=0, channel="Email + App", action="Mời hạng Gold, mua sớm sản phẩm mới", offer=None),
                dict(day=7, channel="Email", action="Chương trình giới thiệu bạn bè", offer="Thưởng cho cả hai bên"),
                dict(day=14, channel="Email", action="Mời viết đánh giá (14 ngày sau mỗi đơn)", offer=None)]),
    dict(journey_id="J5", segment="S5", name="Ổn định cần nuôi", goal="Tăng giá trị", max_spend_pct=0.03,
         kpi="AOV, số ngành hàng mỗi khách mua, tỷ lệ lên S4 sau 6 tháng",
         steps=[dict(day=0, channel="Email + App", action="Vào hạng Silver, hiển thị tiến độ lên Gold", offer=None),
                dict(day=3, channel="Email / Social",
                     action="Gợi ý từ wishlist và ngành hàng bổ sung (loại khách trả hàng / dùng mã thuộc top 25%)",
                     offer=None),
                dict(day=10, channel="Email", action="Bundle 2–3 sản phẩm tăng giá trị đơn", offer="Giá bundle")]),
    dict(journey_id="J6", segment="S6", name="Phổ thông", goal="Chi phí thấp", max_spend_pct=0.01,
         kpi="Chi phí trên mỗi khách, tỷ lệ dùng app, tỷ lệ lên S5",
         steps=[dict(day=0, channel="Email", action="Newsletter 2 tuần/lần", offer=None),
                dict(day=7, channel="Email + SMS", action="Mời cài và dùng app", offer="Ưu đãi nhỏ cho đơn đầu trên app")]),
]


def customer_ids(n):
    """CSV không có ID: sinh theo thứ tự dòng (khớp thứ tự của artifacts/top_reasons.json.gz)."""
    return [f"CUS{i:05d}" for i in range(1, n + 1)]


def load_artifacts(artifact_dir):
    config = json.loads((artifact_dir / "clv_config.json").read_text(encoding="utf-8"))
    bundle = joblib.load(artifact_dir / f"{config['version']}.joblib")
    with gzip.open(artifact_dir / "top_reasons.json.gz", "rt", encoding="utf-8") as f:
        reasons = json.load(f)
    if reasons["version"] != config["version"]:
        raise SystemExit("top_reasons.json.gz khác version với clv_config.json → chạy lại: python -m ml_engine.src.train")
    return config, bundle, reasons["reasons"]


def demo_users():
    """(username, password, superuser) từ .env (xem .env.example). D-17: không phân quyền trên web; admin vào /admin/."""
    env = os.environ.get
    return [(env("DEMO_ADMIN_USERNAME", "admin"), env("DEMO_ADMIN_PASSWORD", "admin123"), True),
            (env("DEMO_MARKETER_USERNAME", "marketer"), env("DEMO_MARKETER_PASSWORD", "demo123"), False)]


def seed(df, artifact_dir, users):
    """Upsert customers + predictions theo lô, tạo lộ trình và tài khoản nếu chưa có. Trả số dòng đã ghi."""
    from django.contrib.auth.models import User
    from django.db import transaction

    from apps.customers.models import Customer
    from apps.predictions.models import Journey, Prediction
    from ml_engine.src.clean import CleanTransformer
    from ml_engine.src.segment import score

    config, bundle, reasons = load_artifacts(artifact_dir)
    if len(reasons) < len(df):
        raise SystemExit("top_reasons.json.gz ít dòng hơn CSV → chạy lại: python -m ml_engine.src.train")
    df = df.reset_index(drop=True)
    ids = customer_ids(len(df))
    scored = score(df, bundle, config)

    # Customer chỉ nhận giá trị trong miền FR-PRED: sửa giống CleanTransformer (Age sai → trống, clip âm / > 100%),
    # nên chấm lại từ DB vẫn ra cùng kết quả.
    columns = {f.db_column: f.name for f in Customer._meta.fields if f.db_column}
    inputs = CleanTransformer()._fix_values(df)[list(columns)].rename(columns=columns)
    inputs = inputs.astype(object).where(inputs.notna(), None)

    with transaction.atomic():
        journeys = {}
        for j in JOURNEYS:
            fields = {k: v for k, v in j.items() if k != "journey_id"}
            journeys[j["segment"]] = Journey.objects.get_or_create(journey_id=j["journey_id"], defaults=fields)[0]

        Customer.objects.bulk_create(
            [Customer(customer_id=cid, source=Customer.Source.SEED, **row)
             for cid, row in zip(ids, inputs.to_dict("records"))],
            batch_size=BATCH, update_conflicts=True, unique_fields=["customer_id"],
            update_fields=[*columns.values(), "source"])

        Prediction.objects.bulk_create(
            [Prediction(customer_id=cid, model_version=config["version"], journey=journeys[row["segment"]],
                        top_reasons=reasons[i], **{f: row[f] for f in SCORE_FIELDS})
             for i, (cid, row) in enumerate(zip(ids, scored.to_dict("records")))],
            batch_size=BATCH, update_conflicts=True, unique_fields=["customer", "model_version"],
            update_fields=[*SCORE_FIELDS, "journey", "top_reasons", "scored_at"])

        for username, password, is_admin in users:
            if not User.objects.filter(username=username).exists():  # chạy lại không đổi mật khẩu đã sửa
                create = User.objects.create_superuser if is_admin else User.objects.create_user
                create(username, password=password)
    return len(ids)


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # console Windows mặc định cp1252, không in được tiếng Việt
    sys.path[:0] = [str(REPO / "backend"), str(REPO)]
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()
    from django.conf import settings

    t0 = time.perf_counter()
    users = demo_users()
    n = seed(pd.read_csv(settings.DATASET_PATH), Path(settings.ARTIFACT_DIR), users)
    print(f"Đã nạp {n:,} khách + prediction, {len(JOURNEYS)} lộ trình trong {time.perf_counter() - t0:.1f}s.")
    print(f"Tài khoản demo: {', '.join(u for u, _, _ in users)} (mật khẩu trong .env / .env.example; "
          "tài khoản đã có thì giữ nguyên mật khẩu)")


if __name__ == "__main__":
    main()
