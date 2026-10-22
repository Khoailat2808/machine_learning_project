import json

import optuna
import pandas as pd
import pytest

from ml_engine.src.evaluate import calibrate
from ml_engine.src.train import ARTIFACTS_DIR, RAW, build_artifacts, make_pipeline, split_data

# Khóa ModelService đọc từ clv_config.json (docs/03 mục 4)
CONFIG_KEYS = {"version", "trained_at", "tau", "email_median", "metrics", "global_importance",
               "g", "d", "horizon", "r_bar", "freq_cap", "P33", "P67"}


def test_split_70_15_15_stratified(tmp_path):
    df = pd.DataFrame({"x": range(1000), "Churned": [1] * 290 + [0] * 710})
    train, val, test = split_data(df, out_dir=tmp_path)
    assert (len(train), len(val), len(test)) == (700, 150, 150)
    for part in (train, val, test):
        assert abs(part["Churned"].mean() - 0.29) < 0.01
    assert set(train.x) | set(val.x) | set(test.x) == set(df.x)  # không mất, không trùng dòng
    assert len(set(train.x) & set(val.x)) == len(set(val.x) & set(test.x)) == 0
    assert split_data(df)[2].x.tolist() == test.x.tolist()  # seed 42 → tái lập được
    assert pd.read_csv(tmp_path / "test.csv").x.tolist() == test.x.tolist()


@pytest.mark.skipif(not RAW.exists(), reason="thiếu CSV gốc")
def test_build_artifacts_on_sample():
    df = pd.read_csv(RAW).sample(3000, random_state=0).reset_index(drop=True)
    parts = [x for part in split_data(df) for x in (part.drop(columns="Churned"), part["Churned"])]
    params = {"n_estimators": 100, "learning_rate": 0.1, "num_leaves": 16, "min_child_samples": 20,
              "subsample": 1.0, "colsample_bytree": 1.0, "reg_lambda": 1.0, "scale_pos_weight": 2.0}
    raw_pipe = make_pipeline("lightgbm", optuna.trial.FixedTrial(params)).fit(*parts[:2])
    calibrated, report = calibrate(raw_pipe, *parts)

    bundle, config = build_artifacts(df, calibrated, raw_pipe, {"selected": "lightgbm", **report}, "churn_test")

    assert CONFIG_KEYS <= config.keys()
    assert 0.05 <= config["tau"] <= 0.95 and 0 < config["P33"] < config["P67"]
    assert config["email_median"] == raw_pipe.named_steps["pre"].named_steps["features"].email_median_
    assert {"roc_auc", "recall"} <= config["metrics"].keys()
    assert bundle["raw_pipe"] is raw_pipe and bundle["version"] == config["version"] == "churn_test"
    json.dumps(config, default=float)  # ghi được ra file


@pytest.mark.skipif(not (ARTIFACTS_DIR / "clv_config.json").exists(), reason="chưa build artifact")
def test_committed_config_matches_contract():
    config = json.loads((ARTIFACTS_DIR / "clv_config.json").read_text(encoding="utf-8"))
    assert CONFIG_KEYS <= config.keys()
    assert (ARTIFACTS_DIR / f"{config['version']}.joblib").exists()
