from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import fbeta_score

from ml_engine.src.evaluate import f2_threshold
from ml_engine.src.train import best_pipeline, tune

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "ecommerce_customer_dataset.csv"


def test_f2_threshold_is_best_in_range():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 2000)
    p = np.clip(0.3 * y + rng.uniform(0, 0.7, 2000), 0, 1)
    tau, f2 = f2_threshold(y, p)
    assert 0.05 <= tau <= 0.95
    assert f2 == pytest.approx(fbeta_score(y, p >= tau, beta=2))
    grid = [fbeta_score(y, p >= t, beta=2) for t in np.linspace(0.05, 0.95, 91)]
    assert f2 >= max(grid) - 1e-9
    assert f2_threshold(y, p, lo=0.6)[0] >= 0.6  # kẹp đúng khoảng BR-01


@pytest.mark.skipif(not RAW.exists(), reason="thiếu CSV gốc")
@pytest.mark.parametrize("algo", ["logreg", "random_forest", "lightgbm"])
def test_tune_smoke(algo):
    df = pd.read_csv(RAW).sample(600, random_state=0)
    y = df.pop("Churned")
    study = tune(df, y, algo, n_trials=2, cv=3)
    assert len(study.trials) == 2 and 0 < study.best_value <= 1
    p = best_pipeline(algo, study).fit(df, y).predict_proba(df)[:, 1]
    assert p.shape == (600,)
