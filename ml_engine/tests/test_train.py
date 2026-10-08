import pandas as pd

from ml_engine.src.train import split_data


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
