"""FR-ML-05, 08: split, train, tune, register (docs/03 mục 3).

Chạy: python -m ml_engine.src.train           # dùng lại best_params trong reports/churn_tune.json, vài phút
      python -m ml_engine.src.train --tune    # tune lại 3 thuật toán (~55 phút), ghi đè churn_tune.json
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import optuna
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml_engine.src.clv import build_clv_config
from ml_engine.src.features import build_preprocessor

ML_DIR = Path(__file__).resolve().parents[1]
RAW = ML_DIR / "data" / "raw" / "ecommerce_customer_dataset.csv"
PROCESSED_DIR = ML_DIR / "data" / "processed"
ARTIFACTS_DIR = ML_DIR / "artifacts"
TUNE_REPORT = ML_DIR / "reports" / "churn_tune.json"
SEED = 42


def split_data(df, target="Churned", random_state=SEED, out_dir=None):
    """Chia 70/15/15 stratify theo target. out_dir → ghi train/val/test.csv để cả nhóm dùng chung."""
    train, rest = train_test_split(df, test_size=0.30, stratify=df[target], random_state=random_state)
    val, test = train_test_split(rest, test_size=0.50, stratify=rest[target], random_state=random_state)
    if out_dir is not None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, part in [("train", train), ("val", val), ("test", test)]:
            part.to_csv(out_dir / f"{name}.csv", index=False)
    return train, val, test


def _lr(t):
    return LogisticRegression(C=t.suggest_float("C", 1e-3, 100, log=True), class_weight="balanced", max_iter=2000)


def _rf(t):
    return RandomForestClassifier(
        n_estimators=t.suggest_int("n_estimators", 100, 500, step=50),
        max_depth=t.suggest_int("max_depth", 4, 20),
        min_samples_leaf=t.suggest_int("min_samples_leaf", 1, 50, log=True),
        max_features=t.suggest_float("max_features", 0.1, 0.8),
        class_weight=t.suggest_categorical("class_weight", ["balanced", "balanced_subsample"]),
        n_jobs=-1, random_state=SEED,
    )


def _lgbm(t):
    return LGBMClassifier(
        n_estimators=t.suggest_int("n_estimators", 100, 1000, step=50),
        learning_rate=t.suggest_float("learning_rate", 0.01, 0.2, log=True),
        num_leaves=t.suggest_int("num_leaves", 8, 128, log=True),
        min_child_samples=t.suggest_int("min_child_samples", 5, 200, log=True),
        subsample=t.suggest_float("subsample", 0.5, 1.0), subsample_freq=1,
        colsample_bytree=t.suggest_float("colsample_bytree", 0.4, 1.0),
        reg_lambda=t.suggest_float("reg_lambda", 1e-3, 10, log=True),
        scale_pos_weight=t.suggest_float("scale_pos_weight", 1.0, 4.0),  # neg/pos ≈ 2,46
        n_jobs=-1, random_state=SEED, verbose=-1,
    )


# Mỗi thuật toán: hàm (trial) → estimator. LR cần chuẩn hóa vì preprocessor để nguyên thang đo.
SEARCH_SPACES = {"logreg": _lr, "random_forest": _rf, "lightgbm": _lgbm}


def make_pipeline(algo, trial):
    steps = [("pre", build_preprocessor())]
    if algo == "logreg":
        steps.append(("scale", StandardScaler()))
    return Pipeline(steps + [("model", SEARCH_SPACES[algo](trial))])


def tune(X, y, algo, n_trials=50, cv=5):
    """Optuna TPE, tối đa PR-AUC trung bình StratifiedKFold. Preprocessor fit lại trong từng fold → không rò nhãn."""
    folds = StratifiedKFold(cv, shuffle=True, random_state=SEED)

    def objective(trial):
        return cross_val_score(make_pipeline(algo, trial), X, y, cv=folds, scoring="average_precision").mean()

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=SEED))
    study.optimize(objective, n_trials=n_trials)
    return study


def best_pipeline(algo, study):
    """Pipeline chưa fit với bộ tham số tốt nhất của study."""
    return make_pipeline(algo, optuna.trial.FixedTrial(study.best_params))


def build_artifacts(df, calibrated, raw_pipe, report, version):
    """Chấm p_churn toàn tệp → CLV trên dữ liệu ĐÃ clean (docs/05 mục 5) → (bundle joblib, clv_config).

    P33/P67 tính trên toàn tệp (BR-02); freq_cap và email_median lấy từ pipeline đã fit trên train.
    """
    X = df.drop(columns="Churned", errors="ignore")
    pre = raw_pipe.named_steps["pre"]
    features = pre.named_steps["features"]
    p = calibrated.predict_proba(X)[:, 1]
    config = build_clv_config(pre.named_steps["clean"].transform(X), p, freq_cap=features.freq_cap_)
    config |= {
        "version": version,
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tau": report["tau"],
        "email_median": features.email_median_,  # BR-06
        "metrics": report["test"],
        "global_importance": None,  # explain.py điền (FR-DASH-06)
    }
    bundle = {"model": calibrated, "raw_pipe": raw_pipe, "tau": report["tau"],
              "algo": report["selected"], "version": version}
    return bundle, config


def refit(df):
    """Fit lại thuật toán + params đã chọn trong churn_tune.json, không tune. Trả (calibrated, raw_pipe, report)."""
    from ml_engine.src.evaluate import calibrate, load_splits  # evaluate import train → tránh vòng lặp

    prev = json.loads(TUNE_REPORT.read_text(encoding="utf-8"))
    algo = prev["selected"]
    splits = load_splits(df)
    raw_pipe = make_pipeline(algo, optuna.trial.FixedTrial(prev["candidates"][algo]["best_params"]))
    raw_pipe.fit(*splits[:2])
    calibrated, final = calibrate(raw_pipe, *splits)
    return calibrated, raw_pipe, {"selected": algo, **final}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=RAW)
    ap.add_argument("--tune", action="store_true", help="tune lại 3 thuật toán thay vì dùng params đã lưu")
    ap.add_argument("--n-trials", type=int, default=50)
    ap.add_argument("--version", default="churn_v1")
    args = ap.parse_args()

    df = pd.read_csv(args.data)
    if args.tune:
        from ml_engine.src.evaluate import run

        calibrated, raw_pipe, report = run(df, n_trials=args.n_trials)
        TUNE_REPORT.write_text(json.dumps(report, indent=2, default=float), encoding="utf-8")
    else:
        calibrated, raw_pipe, report = refit(df)

    bundle, config = build_artifacts(df, calibrated, raw_pipe, report, args.version)
    joblib.dump(bundle, ARTIFACTS_DIR / f"{args.version}.joblib", compress=3)  # < 50 MB (CONTRIBUTING)
    (ARTIFACTS_DIR / "clv_config.json").write_text(json.dumps(config, indent=2, default=float), encoding="utf-8")
    print(json.dumps({k: config[k] for k in ("version", "tau", "P33", "P67", "freq_cap", "email_median", "metrics")},
                     indent=2, default=float))


if __name__ == "__main__":
    main()
