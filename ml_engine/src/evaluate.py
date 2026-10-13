"""FR-ML-06: tune 3 thuật toán → chọn theo CV PR-AUC → hiệu chỉnh isotonic → τ theo F2 trên val → metrics trên test.

Chạy: python -m ml_engine.src.evaluate [--n-trials 50]
"""
import argparse
import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import (
    average_precision_score, brier_score_loss, confusion_matrix, f1_score, fbeta_score,
    precision_recall_curve, precision_score, recall_score, roc_auc_score,
)

from ml_engine.src.train import PROCESSED_DIR, SEARCH_SPACES, best_pipeline, split_data, tune

ML_DIR = Path(__file__).resolve().parents[1]
RAW = ML_DIR / "data" / "raw" / "ecommerce_customer_dataset.csv"
TAU_RANGE = (0.05, 0.95)  # BR-01


def f2_threshold(y, p, lo=TAU_RANGE[0], hi=TAU_RANGE[1]):
    """τ trong [lo, hi] cho F2 lớn nhất. Trả (τ, F2)."""
    prec, rec, thr = precision_recall_curve(y, p)
    prec, rec = prec[:-1], rec[:-1]  # điểm cuối không có ngưỡng
    with np.errstate(invalid="ignore", divide="ignore"):
        f2 = np.nan_to_num(5 * prec * rec / (4 * prec + rec))
    ok = (thr >= lo) & (thr <= hi)
    i = np.argmax(f2[ok])
    return float(thr[ok][i]), float(f2[ok][i])


def metrics(y, p, tau):
    pred = (p >= tau).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred).ravel()
    return {
        "roc_auc": roc_auc_score(y, p), "pr_auc": average_precision_score(y, p),
        "recall": recall_score(y, pred), "precision": precision_score(y, pred),
        "f1": f1_score(y, pred), "f2": fbeta_score(y, pred, beta=2), "brier": brier_score_loss(y, p),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }


def run(df, n_trials=50, target="Churned"):
    train, val, test = split_data(df, target=target, out_dir=PROCESSED_DIR)
    X_tr, y_tr = train.drop(columns=target), train[target]
    X_val, y_val = val.drop(columns=target), val[target]
    X_te, y_te = test.drop(columns=target), test[target]

    candidates = {}
    for algo in SEARCH_SPACES:
        t0 = time.time()
        study = tune(X_tr, y_tr, algo, n_trials=n_trials)
        pipe = best_pipeline(algo, study).fit(X_tr, y_tr)
        p_val = pipe.predict_proba(X_val)[:, 1]
        candidates[algo] = {
            "study": study, "pipe": pipe,
            "report": {
                "cv_pr_auc": study.best_value, "best_trial": study.best_trial.number,
                "best_params": study.best_params, "minutes": round((time.time() - t0) / 60, 1),
                "val_roc_auc": roc_auc_score(y_val, p_val), "val_pr_auc": average_precision_score(y_val, p_val),
            },
        }
        print(algo, json.dumps(candidates[algo]["report"], default=float))

    best = max(candidates, key=lambda a: candidates[a]["report"]["cv_pr_auc"])
    raw_pipe = candidates[best]["pipe"]
    calibrated = CalibratedClassifierCV(clone(raw_pipe), method="isotonic", cv=5).fit(X_tr, y_tr)

    tau, val_f2 = f2_threshold(y_val, calibrated.predict_proba(X_val)[:, 1])
    p_te = calibrated.predict_proba(X_te)[:, 1]
    frac_pos, mean_pred = calibration_curve(y_te, p_te, n_bins=10)
    report = {
        "selected": best, "tau": tau, "val_f2_at_tau": val_f2,
        "test": metrics(y_te, p_te, tau),
        "test_brier_uncalibrated": brier_score_loss(y_te, raw_pipe.predict_proba(X_te)[:, 1]),
        "calibration_curve": {"mean_pred": mean_pred.tolist(), "frac_pos": frac_pos.tolist()},
        "candidates": {a: c["report"] for a, c in candidates.items()},
        "trials_history": {a: [t.value for t in c["study"].trials] for a, c in candidates.items()},
    }
    return calibrated, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=RAW)
    ap.add_argument("--n-trials", type=int, default=50)
    args = ap.parse_args()

    model, report = run(pd.read_csv(args.data), n_trials=args.n_trials)
    (ML_DIR / "reports" / "churn_tune.json").write_text(json.dumps(report, indent=2, default=float), encoding="utf-8")
    joblib.dump({"model": model, "tau": report["tau"], "algo": report["selected"]}, ML_DIR / "artifacts" / "churn_v1.joblib", compress=3)  # < 50 MB (CONTRIBUTING)
    print(json.dumps({k: report[k] for k in ("selected", "tau", "test")}, indent=2, default=float))


if __name__ == "__main__":
    main()
