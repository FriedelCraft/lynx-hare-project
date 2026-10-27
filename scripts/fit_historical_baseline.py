"""Independent matched least-squares benchmark for Yash's historical PINN checks."""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lynx_hare.model import NAMES, Parameters, solve
from lynx_hare.data import write_csv
from lynx_hare.experiments import save_json, sha256
from lynx_hare.historical_pinn import validate_config
from run_historical_pinn import training_split, diagnostics, VARIANTS


def run(config_path, output, multistart=6):
    config_path, output = Path(config_path).resolve(), Path(output).resolve()
    config = json.loads(config_path.read_text())
    validate_config(config)
    if output.exists() or multistart < 1:
        raise ValueError("Choose a new output directory and at least one start")
    data, path = training_split()
    sources = [Path(__file__).resolve(), ROOT / "scripts/run_historical_pinn.py",
               ROOT / "src/lynx_hare/model.py", ROOT / "src/lynx_hare/data.py",
               ROOT / "src/lynx_hare/historical_pinn.py"]
    manifest = {"kind": "historical", "status": "running", "config_sha256": sha256(config_path),
                "training_sha256": sha256(path), "source_hashes": {str(p.relative_to(ROOT)): sha256(p) for p in sources},
                "multistart": multistart, "rng_seed": 91, "heldout_observations_read": False,
                "purpose": "Independent matching benchmark, not a claim that Advay has completed his baseline"}
    output.mkdir(parents=True)
    save_json(output / "manifest.json", manifest)
    save_json(output / "config.json", config)
    names = config["trainable"]
    all_rows, selected = [], {}
    for variant in config.get("variants", list(VARIANTS)):
        error_model, fit_initial = VARIANTS[variant]
        lo = np.array([config["bounds"][n][0] for n in names])
        hi = np.array([config["bounds"][n][1] for n in names])
        base = np.array([config["initial_guess"][n] for n in names])
        if fit_initial:
            lo, hi = np.r_[lo, data.initial_state*0.5], np.r_[hi, data.initial_state*1.5]
            base = np.r_[base, data.initial_state]
        rng = np.random.default_rng(91)

        def unpack(x):
            values = {**config["initial_guess"], **dict(zip(names, x[:len(names)]))}
            p = Parameters(**{name: float(value) for name, value in values.items()})
            return p, x[-2:] if fit_initial else data.initial_state

        def residual(x):
            try:
                p, initial = unpack(x)
                pred = solve(data.times, initial, p, **config["solver"])
                if error_model == "log":
                    if np.any(pred <= 0):
                        raise RuntimeError("Nonpositive log prediction")
                    return (np.log(pred) - np.log(data.observations)).ravel()
                return ((pred-data.observations)/data.scale).ravel()
            except RuntimeError:
                return np.full(data.observations.size, 1e6)

        candidates = []
        for start in range(multistart):
            x0 = base if start == 0 else rng.uniform(lo+1e-5, hi-1e-5)
            print(f"Least squares {variant} start {start}", flush=True)
            result = least_squares(residual, x0, bounds=(lo, hi), max_nfev=500,
                                   ftol=1e-10, xtol=1e-10, gtol=1e-10)
            p, initial = unpack(result.x)
            valid = np.isfinite(result.cost) and result.cost < 1e10
            row = {"variant": variant, "start": start, "initial_guess": x0.tolist(),
                   "parameters": p.to_dict(), "ode_initial": np.asarray(initial).tolist(),
                   "training_mse": float(np.mean(result.fun**2)), "cost": float(result.cost),
                   "success": bool(result.success), "valid": bool(valid), "status": int(result.status),
                   "message": result.message, "nfev": int(result.nfev), "optimality": float(result.optimality)}
            all_rows.append(row)
            if result.success and valid:
                candidates.append(row)
            save_json(output / "starts.json", all_rows)
            print(f"Finished {variant} start {start}: training MSE {row['training_mse']:.5g}", flush=True)
        if not candidates:
            raise RuntimeError(f"No valid converged least-squares start for {variant}")
        chosen = min(candidates, key=lambda r: r["cost"])
        p, initial = Parameters(**chosen["parameters"]), chosen["ode_initial"]
        years = np.arange(1900, 1921)
        states = solve(years-1900, initial, p, **config["solver"])
        t = np.linspace(0, 20, 401)
        smooth = solve(t, initial, p, **config["solver"])
        write_csv(output / f"forecast_{variant}.csv", ["Year", "Hare", "Lynx"], np.column_stack((years[16:], states[16:])))
        write_csv(output / f"ode_{variant}.csv", ["Year", "Hare", "Lynx"], np.column_stack((1900+t, smooth)))
        chosen["diagnostics"] = diagnostics(data, p, initial, config["solver"], names, error_model, fit_initial)
        selected[variant] = chosen
        save_json(output / "selected.json", selected)
    if sha256(config_path) != manifest["config_sha256"] or sha256(path) != manifest["training_sha256"]:
        raise RuntimeError("Inputs changed during baseline fitting")
    if any(sha256(ROOT / name) != digest for name, digest in manifest["source_hashes"].items()):
        raise RuntimeError("Source changed during baseline fitting")
    manifest.update(status="forecasts_frozen_unscored", output_hashes={str(p.relative_to(output)): sha256(p)
                    for p in output.rglob("*") if p.is_file() and p.name != "manifest.json"})
    save_json(output / "manifest.json", manifest)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--multistart", type=int, default=6)
    args = parser.parse_args()
    run(args.config, args.output, args.multistart)
