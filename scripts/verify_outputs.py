"""Audit saved numerical evidence and notebook execution without retraining."""
from pathlib import Path
import csv
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import nbformat
import numpy as np
from lynx_hare.model import Parameters, solve
from lynx_hare.experiments import sha256, metrics, save_json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/synthetic"


def main():
    config = json.loads((ROOT / "configs/synthetic.json").read_text())
    manifest = json.loads((OUT / "manifest.json").read_text())
    selected = json.loads((OUT / "selected_run.json").read_text())
    assert manifest["config_sha256"] == sha256(ROOT / "configs/synthetic.json")
    for name, digest in manifest["model_source_hashes"].items():
        assert digest == sha256(ROOT / "src/lynx_hare" / name), f"Source changed: {name}"
    summaries = [json.loads(p.read_text()) for p in (OUT / "runs").glob("*/summary.json")]
    assert len(summaries) == manifest["run_count"] == 13
    eligible = [s for s in summaries if s["case"] == "annual_noisy" and s["variant"] == "default"]
    assert len(eligible) == 3
    assert selected["run_id"] == min(eligible, key=lambda s: s["audit"]["training_objective"])["run_id"]
    for s in summaries:
        audit = s["audit"]
        assert max(audit["train_years"]) == 1915 and min(audit["train_years"]) == 1900
        assert set(audit["trainable"]) == {"r", "a", "m"}
        assert audit["fixed"] == {"K": 60.0, "b": 20.0, "e": 0.6}
        assert np.isfinite(audit["training_objective"])
        path = OUT / "runs" / s["run_id"] / "forecast.csv"
        assert s["forecast_sha256"] == sha256(path)
        exported = np.loadtxt(path, delimiter=",", skiprows=1)
        assert np.all(np.isfinite(exported)) and np.all(exported[:, 1:] > 0)
        rebuilt = solve(exported[:, 0]-1900, config["initial_state"], Parameters(**s["parameters"]), **config["solver"])
        np.testing.assert_allclose(exported[:, 1:], rebuilt, rtol=1e-12, atol=1e-12)
    with (OUT / "parameter_recovery.csv").open(newline="") as f:
        recovery = list(csv.DictReader(f))
    assert max(float(r["absolute_relative_error_percent"]) for r in recovery
               if r["case"] == "dense_clean" and r["estimated"] == "True") < 1.0
    noisy_train = np.loadtxt(ROOT / "data/synthetic/annual_train.csv", delimiter=",", skiprows=1)
    noisy_test = np.loadtxt(ROOT / "data/synthetic/annual_test.csv", delimiter=",", skiprows=1)
    latent = np.loadtxt(ROOT / "data/synthetic/annual_truth.csv", delimiter=",", skiprows=1)
    with (OUT / "heldout_metrics.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            path = OUT / "least_squares_forecast.csv" if row["method"] == "least_squares" else OUT / "runs" / row["run_id"] / "forecast.csv"
            forecast = np.loadtxt(path, delimiter=",", skiprows=1)[16:, 1:]
            reference = noisy_test[:, 1:] if row["target"] == "noisy_observations" else latent[16:, 1:]
            for name, value in metrics(forecast, reference).items():
                assert abs(float(row[name]) - value) < 1e-12
    handoff = np.loadtxt(OUT / "predictions_for_advay.csv", delimiter=",", skiprows=1)
    np.testing.assert_array_equal(handoff[:, 0], np.arange(1916, 1921))
    assert handoff.shape == (5, 3)
    for extension in ("png", "eps"):
        files = list((OUT / "figures").glob(f"*.{extension}"))
        assert len(files) == 7 and all(p.stat().st_size > 1000 for p in files)
    notebook = nbformat.read(ROOT / "notebooks/yash_pinn.ipynb", as_version=4)
    nbformat.validate(notebook)
    for name, digest in notebook.metadata.get("embedded_source_sha256", {}).items():
        assert digest == sha256(ROOT / "src/lynx_hare" / name), f"Notebook embedded source is stale: {name}"
    code = [c for c in notebook.cells if c.cell_type == "code"]
    assert all(c.execution_count is not None for c in code)
    assert not any(o.output_type == "error" for c in code for o in c.outputs)
    report = {"status": "passed", "runs_verified": len(summaries), "executed_notebook_code_cells": len(code),
              "figures_per_format": 7, "forecast_rows": len(handoff),
              "checks": ["source/configuration hashes", "seed selection from training loss", "training-only years",
                         "correct fixed/estimated rates", "finite positive forecasts", "independent ODE reconstruction",
                         "clean-data recovery", "independently recomputed held-out scores", "handoff schema",
                         "EPS and PNG presence", "notebook schema and error-free execution"]}
    save_json(OUT / "verification.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
