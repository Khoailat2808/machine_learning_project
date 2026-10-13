"""FR-ML-05, 08: split, train, tune, register (docs/03 mục 3)."""
from pathlib import Path

import optuna
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml_engine.src.features import build_preprocessor

PROCESSED_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"
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
