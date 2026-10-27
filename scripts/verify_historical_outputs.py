"""Verify frozen historical evidence and independently reconstruct exported ODEs."""
import csv
import json
import sys
from pathlib import Path

import numpy as np
import nbformat

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lynx_hare.model import Parameters, solve
from lynx_hare.experiments import sha256, metrics
from score_historical import BASE, OUTPUT as EVAL, FOLDERS, frozen, load_forecast


def verify():
    count = 0
    for case, name in FOLDERS.items():
        folder = BASE / name
        m = frozen(folder)
        config = json.loads((folder / "config.json").read_text())
        config_path = ROOT / "configs" / (
            "historical_wider_bounds.json" if case == "wider_bounds" else
            "historical_physics100.json" if case == "physics100" else "historical.json")
        assert json.loads(config_path.read_text()) == config
        assert sha256(config_path) == m["config_sha256"]
        if case == "baseline":
            for variant, summary in json.loads((folder / "selected.json").read_text()).items():
                reconstructed = solve(np.arange(21), summary["ode_initial"], Parameters(**summary["parameters"]), **config["solver"])
                np.testing.assert_allclose(load_forecast(folder / f"forecast_{variant}.csv"), reconstructed[16:], rtol=1e-11, atol=1e-11)
            continue
        summaries = []
        for path in sorted((folder / "runs").glob("*/summary.json")):
            s = json.loads(path.read_text())
            assert s["audit"]["train_years"] == list(range(1900, 1916))
            reconstructed = solve(np.arange(21), s["audit"]["ode_initial"], Parameters(**s["parameters"]), **config["solver"])
            np.testing.assert_allclose(load_forecast(path.parent / "forecast.csv"), reconstructed[16:], rtol=1e-11, atol=1e-11)
            for key in config["trainable"]:
                lo, hi = config["bounds"][key]
                assert lo <= s["parameters"][key] <= hi
            summaries.append(s)
            count += 1
        selected = json.loads((folder / "selected_runs.json").read_text())
        for variant, choice in selected.items():
            eligible = [s for s in summaries if s["variant"] == variant]
            best = min(eligible, key=lambda s: s["audit"]["training_objective"])
            assert choice["run_id"] == best["run_id"]
        assert len(summaries) == m["run_count"]
    freeze = json.loads((EVAL / "forecast_freeze.json").read_text())
    for case, name in FOLDERS.items():
        assert sha256(BASE / name / "manifest.json") == freeze["manifest_sha256"][case]
    receipt = json.loads((EVAL / "receipt.json").read_text())
    assert sha256(EVAL / "heldout_metrics.csv") == receipt["metrics_sha256"]
    assert sha256(EVAL / "forecast_freeze.json") == receipt["freeze_sha256"]
    test = ROOT / "data/historical/test_1916_1920.csv"
    assert sha256(test) == receipt["test_sha256"]
    obs = np.loadtxt(test, delimiter=",", skiprows=1)[:, 1:]
    with (EVAL / "heldout_metrics.csv").open() as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        folder = BASE / FOLDERS[row["case"]]
        path = folder / (f"forecast_{row['variant']}.csv" if row["case"] == "baseline" else f"runs/{row['run_id']}/forecast.csv")
        for key, value in metrics(load_forecast(path), obs).items():
            assert abs(float(row[key])-value) < 1e-10
    notebook = nbformat.read(ROOT / "notebooks/yash_historical_pinn.ipynb", as_version=4)
    code = [c for c in notebook.cells if c.cell_type == "code"]
    for cell in code:
        assert cell.execution_count is not None
        assert not any(o.output_type == "error" for o in cell.outputs)
    for name, digest in notebook.metadata.embedded_source_sha256.items():
        assert sha256(ROOT / "src/lynx_hare" / name) == digest
    graphs = list((ROOT / "report/graphs").glob("yash_historical_*.eps"))
    assert len(graphs) == 5
    assert all(p.with_suffix(".pdf").exists() for p in graphs)
    result = {"status": "passed", "PINN_runs": count, "baseline_variants": 3,
              "scored_forecasts": len(rows), "executed_notebook_code_cells": len(code),
              "graph_pairs": len(graphs), "independent_ODE_reconstruction": True,
              "independent_metric_recomputation": True, "training_only_seed_selection": True}
    (EVAL / "verification.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    verify()
