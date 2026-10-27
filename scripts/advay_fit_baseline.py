"""Advay, phase 3: least-squares baseline on the shared historical config.

Reads only data/historical/train_1900_1915.csv (hash-checked against split.json),
fits every declared variant from many starts, selects the lowest training cost per
variant, and freezes ODE forecasts for 1916-1920. It never opens the test or master
file and computes no held-out score.

    python scripts/advay_fit_baseline.py --output results/historical/advay_baseline_v1
"""
import argparse
import hashlib
import importlib.metadata
import json
import platform
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lynx_hare.data import read_training, write_csv
from lynx_hare import historical_ls as hls

# Declared in docs/advay_baseline_protocol.md before the first run.
PROTOCOL = {
    "starts_per_variant": 40,
    "start_design": "start 0 = config initial_guess; starts 1-39 = Latin hypercube in log-parameter space within the config bounds",
    "seed": 20261027,
    "parameterisation": "x = log(theta); bounds = log(config bounds)",
    "optimizer": {"method": "trf", "x_scale": "jac", "diff_step": 1e-4, "max_nfev": 2000,
                  "ftol": 1e-10, "xtol": 1e-10, "gtol": 1e-10},
    "selection": "lowest training cost among starts that finished without a failed ODE solve; per variant",
    "near_best_tolerance": 0.01,
    "variants": ["main", "log_errors", "fitted_initial"],
    "primary_variant": "main",
}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def training_data():
    folder = ROOT / "data" / "historical"
    part = json.loads((folder / "split.json").read_text())["train"]
    path = folder / part["file"]
    if part["file"] != "train_1900_1915.csv" or sha256(path) != part["sha256"]:
        raise SystemExit("Training file does not match the frozen split record")
    data = read_training(path, 1900, 1915)
    assert data.years.tolist() == list(range(1900, 1916))
    return data, path


def _one(args):
    config, variant, index, x0 = args
    data, _ = training_data()
    problem = hls.Problem(data, config, variant)
    fit = hls.fit_start(problem, np.asarray(x0), PROTOCOL["optimizer"])
    row = hls.describe(problem, fit)
    row.update(variant=variant, start=index, x0=np.exp(x0).tolist(), x=fit.x.tolist())
    print(f"{variant:15s} start {index:2d}  cost {fit.cost:.6f}  status {fit.status}", flush=True)
    return row


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=ROOT / "configs" / "historical.json")
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    if args.output.exists():
        ap.error("Choose a new output directory; existing evidence is never overwritten")
    config = json.loads(args.config.read_text())
    if config.get("kind") != "historical" or "truth" in config:
        ap.error("Need the historical config")
    data, train_path = training_data()

    sources = [Path(__file__), ROOT / "src/lynx_hare/historical_ls.py",
               ROOT / "src/lynx_hare/model.py", ROOT / "src/lynx_hare/data.py",
               ROOT / "src/lynx_hare/stability.py"]
    manifest = {
        "kind": "historical", "owner": "Advay", "status": "running",
        "purpose": "Advay's least-squares baseline on the shared config (independent of Yash's matched benchmark)",
        "heldout_observations_read": False,
        "protocol": PROTOCOL,
        "config": str(args.config.relative_to(ROOT)), "config_sha256": sha256(args.config),
        "training_file": str(train_path.relative_to(ROOT)), "training_sha256": sha256(train_path),
        "source_hashes": {str(p.resolve().relative_to(ROOT)): sha256(p) for p in sources},
        "versions": {"python": platform.python_version(),
                     **{k: importlib.metadata.version(k) for k in ("numpy", "scipy")}},
    }
    args.output.mkdir(parents=True)
    save_json(args.output / "manifest.json", manifest)
    save_json(args.output / "config.json", config)

    jobs = []
    for variant in PROTOCOL["variants"]:
        problem = hls.Problem(data, config, variant)
        seed = PROTOCOL["seed"] + PROTOCOL["variants"].index(variant)
        for i, x0 in enumerate(hls.starting_points(problem, PROTOCOL["starts_per_variant"], seed)):
            jobs.append((config, variant, i, x0.tolist()))
    with ProcessPoolExecutor(args.workers) as pool:
        rows = list(pool.map(_one, jobs))
    save_json(args.output / "starts.json", rows)

    selected, team = {}, {}
    for variant in PROTOCOL["variants"]:
        problem = hls.Problem(data, config, variant)
        mine = [r for r in rows if r["variant"] == variant]
        ok = [r for r in mine if not r["failed_solve"] and np.isfinite(r["cost"])]
        best = min(ok, key=lambda r: r["cost"])
        near = [r for r in ok if r["cost"] <= best["cost"] * (1 + PROTOCOL["near_best_tolerance"])]
        fit = hls.fit_start(problem, np.asarray(best["x"]), PROTOCOL["optimizer"])  # re-polish for Jacobian
        if fit.cost > best["cost"] * (1 + 1e-9):
            raise RuntimeError("Re-polish increased the cost; check determinism")
        p, y0 = problem.unpack(fit.x)
        years, states = hls.forecast(p, y0, config, 1900, config["forecast_end_year"], config["train_end_year"])
        write_csv(args.output / f"forecast_{variant}.csv", ["Year", "Hare", "Lynx"],
                  [[int(y), *s] for y, s in zip(years, states)])
        t, traj = hls.dense(p, y0, config, config["forecast_end_year"] - 1900)
        write_csv(args.output / f"ode_{variant}.csv", ["t", "Year", "Hare", "Lynx"],
                  [[ti, 1900 + ti, *s] for ti, s in zip(t, traj)])
        spread = {k: [min(r["parameters"][k] for r in near), max(r["parameters"][k] for r in near)]
                  for k in p.to_dict()}
        sig = [r["sigma"] for r in near if r["sigma"] is not None]
        selected[variant] = {
            **hls.describe(problem, fit), "start": best["start"],
            "starts_total": len(mine), "starts_ok": len(ok), "starts_near_best": len(near),
            "near_best_parameter_range": spread,
            "near_best_sigma_range": [min(sig), max(sig)] if sig else None,
            "sigma_all_ok_starts": [r["sigma"] for r in ok],
            "identifiability": hls.local_identifiability(problem, fit),
        }
        team[variant] = {"parameters": p.to_dict(), "initial_state": y0.tolist(),
                         "sigma": selected[variant]["sigma"], "regime": selected[variant]["regime"],
                         "near_best_sigma_range": selected[variant]["near_best_sigma_range"],
                         "at_bound": selected[variant]["at_bound"]}
    save_json(args.output / "selected.json", selected)
    save_json(args.output / "parameters_for_team.json",
              {"note": "Effective coefficients in thousands of pelts (O1). r, m in 1/year.",
               "primary_variant": PROTOCOL["primary_variant"], "variants": team})

    manifest["status"] = "forecasts_frozen_unscored"
    manifest["output_hashes"] = {p.name: sha256(p) for p in sorted(args.output.iterdir())
                                 if p.name != "manifest.json"}
    save_json(args.output / "manifest.json", manifest)
    for v, s in selected.items():
        print(f"{v:15s} cost {s['cost']:.6f}  near-best {s['starts_near_best']}/{s['starts_ok']}  "
              f"sigma {s['sigma']}  at_bound {s['at_bound']}")


if __name__ == "__main__":
    main()
