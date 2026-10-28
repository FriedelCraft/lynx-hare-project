"""Training-only diagnostic: evaluate the selected PINN parameters on the least-squares
training objective, to see how close each PINN reaches the least-squares optimum.
Does not open the test file.

    python scripts/advay_pinn_training_fit.py
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lynx_hare.data import read_training
from lynx_hare.model import Parameters
from lynx_hare import historical_ls as hls
from lynx_hare import stability as st

BASE = ROOT / "results" / "historical"


def main():
    config = json.loads((ROOT / "configs" / "historical.json").read_text())
    data = read_training(ROOT / "data" / "historical" / "train_1900_1915.csv", 1900, 1915)
    selected = json.loads((BASE / "yash_pinn_v1" / "selected_runs.json").read_text())
    ls = json.loads((BASE / "advay_baseline_v2" / "selected.json").read_text())
    out = {}
    for variant, run in selected.items():
        summary = json.loads((BASE / "yash_pinn_v1" / "runs" / run["run_id"] / "summary.json").read_text())
        problem = hls.Problem(data, config, variant)
        p = Parameters(**run["parameters"])
        y0 = summary["audit"]["ode_initial"]
        x = np.log([getattr(p, n) for n in problem.names] + (list(y0) if problem.fit_initial else []))
        cost = 0.5 * float(np.sum(problem.residual(x) ** 2))
        out[variant] = {"pinn_run": run["run_id"], "pinn_training_cost": cost,
                        "ls_training_cost": ls[variant]["cost"], "ratio": cost / ls[variant]["cost"],
                        "pinn_sigma": float(st.stability_margin(p)), "ls_sigma": ls[variant]["sigma"]}
    (BASE / "advay_evaluation_v1" / "pinn_training_fit.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
