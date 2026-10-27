"""Score already-frozen historical forecasts; this module never fits a model."""
import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lynx_hare.experiments import save_json, sha256, metrics
from lynx_hare.data import write_csv

FOLDERS = {"primary": "yash_pinn_v1", "wider_bounds": "yash_pinn_wider_v1",
           "physics100": "yash_pinn_physics100_v1", "baseline": "yash_matching_baseline_v2"}
BASE = ROOT / "results/historical"
OUTPUT = BASE / "yash_evaluation_v1"


def frozen(folder):
    record = json.loads((folder / "manifest.json").read_text())
    if record["status"] != "forecasts_frozen_unscored":
        raise ValueError(f"Forecasts are not frozen: {folder}")
    for name, digest in record["output_hashes"].items():
        if sha256(folder / name.replace("\\", "/")) != digest:
            raise ValueError(f"Changed frozen output: {folder / name}")
    for name, digest in record["source_hashes"].items():
        if sha256(ROOT / name.replace("\\", "/")) != digest:
            raise ValueError(f"Changed fitted source: {name}")
    return record


def load_forecast(path):
    table = np.loadtxt(path, delimiter=",", skiprows=1)
    np.testing.assert_array_equal(table[:, 0], np.arange(1916, 1921))
    if not np.isfinite(table).all() or (table[:, 1:] < 0).any():
        raise ValueError(f"Invalid frozen forecast {path}")
    return table[:, 1:]


def run():
    if OUTPUT.exists():
        raise ValueError("Evaluation already exists; retain this frozen evaluation")
    manifests = {name: frozen(BASE / folder) for name, folder in FOLDERS.items()}
    assert manifests["primary"]["config_sha256"] == manifests["baseline"]["config_sha256"]
    assert len({m["training_sha256"] for m in manifests.values()}) == 1
    predictions, rows = {}, []
    for case in ("primary", "wider_bounds", "physics100"):
        folder = BASE / FOLDERS[case]
        selected = json.loads((folder / "selected_runs.json").read_text())
        for path in sorted((folder / "runs").glob("*/summary.json")):
            s = json.loads(path.read_text())
            name = f"{case}/{s['run_id']}"
            forecast = path.parent / "forecast.csv"
            predictions[name] = load_forecast(forecast)
            rows.append({"case": case, "method": "PINN-derived ODE", "run_id": s["run_id"],
                         "variant": s["variant"], "selected": selected[s["variant"]]["run_id"] == s["run_id"],
                         "prediction_key": name, "forecast_sha256": sha256(forecast)})
    folder = BASE / FOLDERS["baseline"]
    selected = json.loads((folder / "selected.json").read_text())
    for variant, choice in selected.items():
        name = f"baseline/{variant}"
        path = folder / f"forecast_{variant}.csv"
        predictions[name] = load_forecast(path)
        rows.append({"case": "baseline", "method": "least squares", "run_id": f"start{choice['start']}",
                     "variant": variant, "selected": True, "prediction_key": name,
                     "forecast_sha256": sha256(path)})
    # All forecasts, variants, seed choices and their hashes are recorded BEFORE
    # numerical test observations enter this process.
    OUTPUT.mkdir()
    freeze = {"rule": "all configuration and seed choices frozen before test scoring",
              "forecast_choices": rows,
              "manifest_sha256": {name: sha256(BASE / folder / "manifest.json") for name, folder in FOLDERS.items()},
              "subsequent_retuning_permitted_for_this_evaluation": False}
    save_json(OUTPUT / "forecast_freeze.json", freeze)
    record = json.loads((ROOT / "data/historical/split.json").read_text())
    test = ROOT / "data/historical" / record["test"]["file"]
    assert sha256(test) == record["test"]["sha256"]
    with test.open(newline="", encoding="utf-8") as f:
        obs = np.array([[float(r[n]) for n in ("Year", "Hare", "Lynx")] for r in csv.DictReader(f)])
    np.testing.assert_array_equal(obs[:, 0], np.arange(1916, 1921))
    score_rows = [{**row, **metrics(predictions[row["prediction_key"]], obs[:, 1:])} for row in rows]
    write_csv(OUTPUT / "heldout_metrics.csv", list(score_rows[0]), [list(row.values()) for row in score_rows])
    save_json(OUTPUT / "receipt.json", {"status": "scored_frozen_forecasts", "test_sha256": sha256(test),
              "freeze_sha256": sha256(OUTPUT / "forecast_freeze.json"),
              "metrics_sha256": sha256(OUTPUT / "heldout_metrics.csv"), "forecast_count": len(score_rows),
              "test_years": [1916, 1920], "units": "thousands of pelts", "test_used_for_model_choices": False})
    for row in score_rows:
        if row["selected"]:
            print(row["prediction_key"], {k: round(row[k], 3) for k in ("hare_rmse", "lynx_rmse", "hare_mae", "lynx_mae")})


if __name__ == "__main__":
    run()
