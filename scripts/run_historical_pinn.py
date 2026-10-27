"""Train historical PINNs and freeze forecasts without reading held-out observations.

Usage: python scripts/run_historical_pinn.py --config configs/historical.json
       --output results/historical/yash_pinn_v1
Advay performs final scoring after both methods' forecasts and choices are frozen.
"""
import argparse
import hashlib
import importlib.metadata
import json
import platform
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lynx_hare.data import read_training, write_csv
from lynx_hare.experiments import save_json, sha256
from lynx_hare.historical_pinn import fit_historical, validate_config
from lynx_hare.model import NAMES, solve

VARIANTS = {"main": ("additive", False), "log_errors": ("log", False),
            "fitted_initial": ("additive", True)}


def training_split(root=ROOT):
    """Validate the frozen training file; never open the test or master table."""
    folder = root / "data" / "historical"
    record = json.loads((folder / "split.json").read_text())
    part = record["train"]
    if part["file"] != "train_1900_1915.csv" or part["years"] != [1900, 1915] or part["rows"] != 16:
        raise ValueError("Unexpected split; explicitly revise the protocol before fitting")
    path = folder / part["file"]
    if hashlib.sha256(path.read_bytes()).hexdigest() != part["sha256"]:
        raise ValueError("Training file hash does not match Advay's split record")
    data = read_training(path, 1900, 1915)
    if data.years.tolist() != list(range(1900, 1916)):
        raise ValueError("Historical training requires exactly 1900-1915")
    return data, path


def diagnostics(data, parameters, initial, solver, names, error_model, fit_initial):
    """Training-only local sensitivity to log parameters (and optionally log IC)."""
    def trajectory(p, y0):
        y = solve(data.times, y0, p, **solver)
        return np.log(y) if error_model == "log" else y / data.scale

    from lynx_hare.model import Parameters
    eps, columns = 1e-4, []
    labels = list(names)
    for name in names:
        plus, minus = parameters.to_dict(), parameters.to_dict()
        plus[name] *= np.exp(eps)
        minus[name] *= np.exp(-eps)
        columns.append(((trajectory(Parameters(**plus), initial)
                         - trajectory(Parameters(**minus), initial)) / (2 * eps)).ravel())
    if fit_initial:
        for i, label in enumerate(("H0", "P0")):
            plus, minus = np.array(initial), np.array(initial)
            plus[i] *= np.exp(eps)
            minus[i] *= np.exp(-eps)
            columns.append(((trajectory(parameters, plus) - trajectory(parameters, minus)) / (2 * eps)).ravel())
            labels.append(label)
    singular = np.linalg.svd(np.column_stack(columns), compute_uv=False)
    condition = float(singular[0] / singular[-1]) if singular[-1] > 0 else None
    denominator = parameters.e * parameters.a - parameters.m
    Hstar = parameters.m * parameters.b / denominator if denominator > 0 else None
    feasible = Hstar is not None and Hstar < parameters.K
    KH = parameters.b + 2 * Hstar if feasible else None
    return {"names": labels, "singular_values": singular.tolist(), "condition_number": condition,
            "finite_difference_log_step": eps,
            "coexistence_feasible": feasible, "K_H": KH,
            "sigma": parameters.K / KH if feasible else None,
            "interpretation": "Local finite-difference training diagnostic; neither structural identifiability nor confidence intervals"}


def run(config_path, output, root=ROOT):
    config_path, output = Path(config_path).resolve(), Path(output).resolve()
    config = json.loads(config_path.read_text())
    validate_config(config)
    variants = config.get("variants", list(VARIANTS))
    if not variants or len(set(variants)) != len(variants) or not set(variants) <= set(VARIANTS):
        raise ValueError("Declare distinct supported variants")
    if (config["start_year"], config["train_end_year"], config["forecast_end_year"]) != (1900, 1915, 1920):
        raise ValueError("Runner implements the declared 1900-1915/1916-1920 split")
    if output.exists():
        raise ValueError("Use a new output directory to preserve prior evidence")
    data, train_path = training_split(root)
    source_paths = [root / "src/lynx_hare" / (name + ".py")
                    for name in ("model", "data", "pinn", "historical_pinn", "experiments")]
    source_paths.append(Path(__file__).resolve())
    manifest = {"kind": "historical", "status": "running", "config": config,
                "config_sha256": sha256(config_path), "training_sha256": sha256(train_path),
                "source_hashes": {str(p.relative_to(root)): sha256(p) for p in source_paths},
                "python": sys.version, "platform": platform.platform(),
                "versions": {name: importlib.metadata.version(name) for name in ("torch", "numpy", "scipy")},
                "heldout_observations_read": False,
                "selection_rule": "minimum weighted training objective among seeds within each variant"}
    output.mkdir(parents=True)
    save_json(output / "manifest.json", manifest)
    save_json(output / "config.json", config)
    years = np.arange(1900, 1921)
    dense_time = np.linspace(0, 20, 401)
    train_grid = torch.tensor(np.linspace(0, 15, 301)[:, None], dtype=torch.float64)
    check_grid = torch.tensor(np.linspace(0.017, 14.983, 307)[:, None], dtype=torch.float64)
    summaries, selected = [], {}
    for variant in variants:
        error_model, fit_initial = VARIANTS[variant]
        variant_runs = []
        for seed in config["seeds"]:
            run_id = f"{variant}_seed{seed}"
            print(f"Training {run_id}", flush=True)
            model, history, audit = fit_historical(data, config, seed, error_model, fit_initial)
            params, initial = model.inferred(), np.array(audit["ode_initial"])
            states = solve(years - 1900, initial, params, **config["solver"])
            smooth = solve(dense_time, initial, params, **config["solver"])
            with torch.no_grad():
                network = model(train_grid).numpy() * data.scale
            residual = model.residuals(check_grid).detach().numpy()
            folder = output / "runs" / run_id
            folder.mkdir(parents=True)
            write_csv(folder / "training.csv", list(history[0]), [list(row.values()) for row in history])
            write_csv(folder / "forecast.csv", ["Year", "Hare", "Lynx"], np.column_stack((years[16:], states[16:])))
            write_csv(folder / "ode_dense.csv", ["Year", "Hare", "Lynx"], np.column_stack((1900 + dense_time, smooth)))
            write_csv(folder / "network_train.csv", ["Year", "Hare", "Lynx"], np.column_stack((1900 + train_grid.numpy().ravel(), network)))
            write_csv(folder / "residual_check.csv", ["Year", "Hare_residual", "Lynx_residual"],
                      np.column_stack((1900 + check_grid.numpy().ravel(), residual)))
            residual_train = states[:16] - data.observations
            summary = {"run_id": run_id, "variant": variant, "parameters": params.to_dict(), "audit": audit,
                       "residual_check_rms": np.sqrt(np.mean(residual ** 2, axis=0)).tolist(),
                       "training_ode_normalized_mse": float(np.mean((residual_train / data.scale) ** 2)),
                       "training_ode_rmse": np.sqrt(np.mean(residual_train ** 2, axis=0)).tolist(),
                       "diagnostics": diagnostics(data, params, initial, config["solver"], config["trainable"], error_model, fit_initial),
                       "bound_fractions": {k: (params.to_dict()[k] - config["bounds"][k][0]) /
                                           (config["bounds"][k][1] - config["bounds"][k][0]) for k in config["trainable"]},
                       "forecast_sha256": sha256(folder / "forecast.csv")}
            save_json(folder / "summary.json", summary)
            torch.save({"state_dict": model.state_dict(), "audit": audit}, folder / "checkpoint.pt")
            summaries.append(summary)
            variant_runs.append(summary)
            print(f"Finished {run_id}: training loss {audit['training_objective']:.5g}", flush=True)
        chosen = min(variant_runs, key=lambda r: r["audit"]["training_objective"])
        selected[variant] = {"run_id": chosen["run_id"], "parameters": chosen["parameters"],
                             "forecast_sha256": chosen["forecast_sha256"]}
        name = "predictions_for_advay.csv" if variant == "main" else f"predictions_{variant}.csv"
        (output / name).write_bytes((output / "runs" / chosen["run_id"] / "forecast.csv").read_bytes())
    save_json(output / "selected_runs.json", selected)
    save_json(output / "parameters_for_team.json", [{"run_id": r["run_id"], **r["parameters"],
              "sigma": r["diagnostics"]["sigma"], "coexistence_feasible": r["diagnostics"]["coexistence_feasible"],
              "ode_initial": r["audit"]["ode_initial"]} for r in summaries])
    if sha256(config_path) != manifest["config_sha256"] or sha256(train_path) != manifest["training_sha256"]:
        raise RuntimeError("Configuration or training data changed during fitting; forecasts cannot be frozen")
    if any(sha256(root / path) != digest for path, digest in manifest["source_hashes"].items()):
        raise RuntimeError("Scientific source changed during fitting; use a fresh run directory")
    manifest.update(status="forecasts_frozen_unscored", run_count=len(summaries), selected_runs=selected,
                    output_hashes={str(p.relative_to(output)): sha256(p) for p in output.rglob("*")
                                   if p.is_file() and p.name not in ("manifest.json", "checkpoint.pt")})
    save_json(output / "manifest.json", manifest)
    print(f"Frozen forecasts: {output}; held-out scoring remains with Advay", flush=True)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.config, args.output)
