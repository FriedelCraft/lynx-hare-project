"""Advay, phase 1 step 4: write the frozen train/test files from the master pelt CSV.

Rows are copied byte for byte (no reformatting), split at TRAIN_END, and the SHA-256 of
each file is written to data/historical/split.json. Fitting code reads only the train
file; only the final scoring script may open the test file.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "historical"
MASTER = DATA / "pelts_1900_1920.csv"
TRAIN = DATA / "train_1900_1915.csv"
TEST = DATA / "test_1916_1920.csv"
TRAIN_END = 1915


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    header, *rows = MASTER.read_text(encoding="utf-8").splitlines(keepends=True)
    assert header.strip() == "Year,Hare,Lynx", header
    years = [int(r.split(",", 1)[0]) for r in rows]
    assert years == list(range(1900, 1921)), years
    train = [r for r, y in zip(rows, years) if y <= TRAIN_END]
    test = [r for r, y in zip(rows, years) if y > TRAIN_END]
    TRAIN.write_text(header + "".join(train), encoding="utf-8")
    TEST.write_text(header + "".join(test), encoding="utf-8")
    assert TRAIN.read_text().splitlines()[1:] + TEST.read_text().splitlines()[1:] \
        == MASTER.read_text().splitlines()[1:], "split must reassemble the master file"

    record = {
        "master": {"file": MASTER.name, "sha256": sha256(MASTER)},
        "train": {"file": TRAIN.name, "years": [1900, TRAIN_END], "rows": len(train),
                  "sha256": sha256(TRAIN)},
        "test": {"file": TEST.name, "years": [TRAIN_END + 1, 1920], "rows": len(test),
                 "sha256": sha256(TEST)},
        "rules": [
            "Fitting, scaling, early stopping, seed or configuration choices may read only the train file.",
            "The test file is opened only by the final scoring step, after forecasts are frozen.",
            "Forecasts integrate from 1900 (t = 0) through 1920; no restart from any test value.",
            "If the master file changes, rerun this script and use a new results directory.",
        ],
        "created_by": "scripts/advay_make_split.py",
    }
    (DATA / "split.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
