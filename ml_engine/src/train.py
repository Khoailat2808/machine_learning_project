"""FR-ML-05, 08: split, train, tune, register (docs/03 mục 3)."""
from pathlib import Path

from sklearn.model_selection import train_test_split

PROCESSED_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"


def split_data(df, target="Churned", random_state=42, out_dir=None):
    """Chia 70/15/15 stratify theo target. out_dir → ghi train/val/test.csv để cả nhóm dùng chung."""
    train, rest = train_test_split(df, test_size=0.30, stratify=df[target], random_state=random_state)
    val, test = train_test_split(rest, test_size=0.50, stratify=rest[target], random_state=random_state)
    if out_dir is not None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, part in [("train", train), ("val", val), ("test", test)]:
            part.to_csv(out_dir / f"{name}.csv", index=False)
    return train, val, test
