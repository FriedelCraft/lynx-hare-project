"""Checks on Advay's historical data files: integrity, split and leakage guards."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from lynx_hare.data import read_training

DATA = Path(__file__).resolve().parents[1] / "data" / "historical"


def rows(name):
    with (DATA / name).open(newline="", encoding="utf-8") as f:
        return [(int(r["Year"]), float(r["Hare"]), float(r["Lynx"])) for r in csv.DictReader(f)]


def test_master_file_is_clean():
    table = np.array(rows("pelts_1900_1920.csv"))
    assert table[:, 0].tolist() == list(range(1900, 1921))
    assert np.isfinite(table).all() and (table[:, 1:] > 0).all()


def test_split_reassembles_master_without_overlap():
    train, test, master = rows("train_1900_1915.csv"), rows("test_1916_1920.csv"), rows("pelts_1900_1920.csv")
    assert [y for y, *_ in train] == list(range(1900, 1916))
    assert [y for y, *_ in test] == list(range(1916, 1921))
    assert train + test == master


def test_recorded_hashes_match_files():
    record = json.loads((DATA / "split.json").read_text())
    for part in ("master", "train", "test"):
        path = DATA / record[part]["file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record[part]["sha256"], part
    provenance = json.loads((DATA / "provenance.json").read_text())
    assert provenance["file_sha256"] == record["master"]["sha256"]


def test_training_contract_sees_only_training_years():
    from_train = read_training(DATA / "train_1900_1915.csv", 1900, 1915)
    from_master = read_training(DATA / "pelts_1900_1920.csv", 1900, 1915)
    assert from_train.years.tolist() == from_master.years.tolist() == list(range(1900, 1916))
    np.testing.assert_array_equal(from_train.observations, from_master.observations)
    np.testing.assert_array_equal(from_train.scale, [77.4, 59.4])
    np.testing.assert_array_equal(from_train.initial_state, [30.0, 4.0])
