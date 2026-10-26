"""Reproduce synthetic data, training, frozen predictions, evaluation and figures."""
import argparse
import csv
import hashlib
import importlib.metadata
import json
import platform
import sys
from pathlib import Path
import numpy as np
import torch
from .data import TrainingData, synthetic, write_csv
from .model import Parameters, NAMES, solve
from .pinn import fit_pinn
from .baseline import fit_least_squares, sensitivity_spectrum


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def metrics(predicted, observed):
    difference = np.asarray(predicted) - np.asarray(observed)
    return {"hare_rmse": float(np.sqrt(np.mean(difference[:, 0] ** 2))),
            "lynx_rmse": float(np.sqrt(np.mean(difference[:, 1] ** 2))),
            "hare_mae": float(np.mean(abs(difference[:, 0]))),
            "lynx_mae": float(np.mean(abs(difference[:, 1])))}


def run(root, quick=False):
    root = Path(root).resolve()
    config = json.loads((root / "configs/synthetic.json").read_text())
    output = root / "results" / ("smoke" if quick else "synthetic")
    output.mkdir(parents=True, exist_ok=True)
    old_manifest = output / "manifest.json"
    if old_manifest.exists():
        previous = json.loads(old_manifest.read_text())
        for name in ("model.py", "data.py", "pinn.py", "baseline.py"):
            if previous["model_source_hashes"].get(name) != sha256(root / "src/lynx_hare" / name):
                raise RuntimeError(f"Scientific source {name} changed; move prior results aside before retraining")
    # Quick output is isolated so it cannot overwrite the full experiment evidence.
    settings = {"warmup_steps": 30, "adam_steps": 50, "lbfgs_steps": 10} if quick else {}
    seeds = config["seeds"][:1] if quick else config["seeds"]
    data_dir = root / "data/synthetic"
    annual_times = np.arange(21, dtype=float)
    annual_truth, annual_obs = synthetic(config, annual_times)
    dense_times = np.linspace(0, 15, 61)
    dense_truth, dense_noisy = synthetic(config, dense_times)
    write_csv(data_dir / "annual_train.csv", ["Year", "Hare", "Lynx"],
              np.column_stack((1900 + annual_times[:16], annual_obs[:16])))
    write_csv(data_dir / "annual_test.csv", ["Year", "Hare", "Lynx"],
              np.column_stack((1900 + annual_times[16:], annual_obs[16:])))
    write_csv(data_dir / "annual_truth.csv", ["Year", "Hare", "Lynx"],
              np.column_stack((1900 + annual_times, annual_truth)))
    write_csv(data_dir / "dense_clean_train.csv", ["Year", "Hare", "Lynx"],
              np.column_stack((1900 + dense_times, dense_truth)))
    write_csv(data_dir / "dense_noisy_train.csv", ["Year", "Hare", "Lynx"],
              np.column_stack((1900 + dense_times, dense_noisy)))
    save_json(data_dir / "provenance.json", {
        "kind": "synthetic", "historical_data": False,
        "generator": "Rosenzweig-MacArthur ODE, RK45", "truth": config["truth"],
        "initial_state": config["initial_state"], "noise_fraction": config["noise_fraction"],
        "noise_model": "independent multiplicative Gaussian; clipped at 1e-8; first row exact",
        "seed": config["data_seed"], "units": "arbitrary abundance indices; time in years",
        "years": "1900-1920 labels mimic planned split; these are NOT historical pelt counts",
        "train_end": 1915, "test_start": 1916, "solver": config["solver"]})
    cases = {
        "dense_clean": TrainingData(1900 + dense_times, dense_truth, 1900),
        "dense_noisy": TrainingData(1900 + dense_times, dense_noisy, 1900),
        "annual_noisy": TrainingData(np.arange(1900, 1916), annual_obs[:16], 1900)}
    jobs = [(case, seed, {}, 1.0, None) for case in cases for seed in seeds]
    if not quick:
        jobs += [("annual_noisy", 17, {"physics_weight": w}, 1.0, f"physics_{w:g}") for w in (1.0, 100.0)]
        jobs += [("annual_noisy", 17, {}, f, f"initial_{f:g}") for f in (0.6, 1.4)]
    summaries, parameter_rows = [], []
    dense_plot_times = np.linspace(0, 20, 401)
    for case, seed, overrides, factor, suffix in jobs:
        run_id = f"{case}_seed{seed}" + (f"_{suffix}" if suffix else "")
        folder = output / "runs" / run_id
        if (folder / "summary.json").exists():
            summary = json.loads((folder / "summary.json").read_text())
            if summary["config_sha256"] != sha256(root / "configs/synthetic.json"):
                raise RuntimeError(f"Stale cached run {run_id}; use a new results folder after changing config")
            print(f"Using completed run: {run_id}", flush=True)
        else:
            print(f"Training {run_id}", flush=True)
            model, history, audit = fit_pinn(cases[case], config, seed,
                                             {**settings, **overrides}, initial_factor=factor)
            learned = model.inferred()
            # Inference and ODE forecasts are frozen before any held-out evaluation.
            forecast = solve(annual_times, cases[case].initial_state, learned, **config["solver"])
            smooth = solve(dense_plot_times, cases[case].initial_state, learned, **config["solver"])
            with torch.no_grad():
                train_grid = np.linspace(0, 15, 301)
                network = model(torch.tensor(train_grid[:, None], dtype=torch.float64)).numpy() * cases[case].scale
            folder.mkdir(parents=True, exist_ok=True)
            write_csv(folder / "training.csv", list(history[0]), [list(row.values()) for row in history])
            write_csv(folder / "forecast.csv", ["Year", "Hare", "Lynx"], np.column_stack((annual_times + 1900, forecast)))
            write_csv(folder / "ode_dense.csv", ["Year", "Hare", "Lynx"], np.column_stack((dense_plot_times + 1900, smooth)))
            write_csv(folder / "network_train.csv", ["Year", "Hare", "Lynx"], np.column_stack((train_grid + 1900, network)))
            # Check residual at a separate offset grid, still entirely in the training interval.
            check_times = torch.tensor(np.linspace(0.017, 14.983, 307)[:, None], dtype=torch.float64)
            residual = model.residuals(check_times).detach().numpy()
            write_csv(folder / "residual_check.csv", ["Year", "Hare_residual", "Lynx_residual"],
                      np.column_stack((check_times.numpy().ravel() + 1900, residual)))
            torch.save({"state_dict": model.state_dict(), "audit": audit}, folder / "checkpoint.pt")
            summary = {"run_id": run_id, "case": case, "seed": seed, "variant": suffix or "default",
                       "parameters": learned.to_dict(), "audit": audit,
                       "config_sha256": sha256(root / "configs/synthetic.json"),
                       "training_normalized_ode_mse": float(np.mean(((forecast[:16] - annual_obs[:16]) / cases[case].scale) ** 2)) if case == "annual_noisy" else None,
                       "residual_check_rms": np.sqrt(np.mean(residual ** 2, axis=0)).tolist(),
                       "forecast_sha256": sha256(folder / "forecast.csv")}
            save_json(folder / "summary.json", summary)
            print(f"Finished {run_id}: loss={audit['training_objective']:.3g}, {audit['elapsed_seconds']:.1f}s", flush=True)
        summaries.append(summary)
        # Recovery is evaluation against generating truth, never a training input.
        for name in NAMES:
            parameter_rows.append([run_id, case, seed, summary["variant"], name, name in config["trainable"],
                                   config["truth"][name], summary["parameters"][name],
                                   100 * abs(summary["parameters"][name] / config["truth"][name] - 1)])
    write_csv(output / "parameter_recovery.csv",
              ["run_id", "case", "seed", "variant", "parameter", "estimated", "truth", "learned", "absolute_relative_error_percent"], parameter_rows)
    eligible = [s for s in summaries if s["case"] == "annual_noisy" and s["variant"] == "default"]
    selected = min(eligible, key=lambda s: s["audit"]["training_objective"])
    selected_id = selected["run_id"]
    save_json(output / "selected_run.json", {"run_id": selected_id,
              "rule": "lowest weighted training objective among default annual seeds; no test data used",
              "parameters": selected["parameters"], "forecast_sha256": selected["forecast_sha256"]})
    baseline_file = output / "least_squares.json"
    if baseline_file.exists():
        baseline = json.loads(baseline_file.read_text())
        base_params = Parameters(**baseline["parameters"])
    else:
        print("Fitting matching multistart least-squares baseline", flush=True)
        base_params, logs = fit_least_squares(cases["annual_noisy"], config, multistart=2 if quick else 6)
        baseline = {"parameters": base_params.to_dict(), "starts": logs, "seed": 91,
                    "trainable": config["trainable"], "fixed": {k: config["initial_guess"][k] for k in NAMES if k not in config["trainable"]}}
        save_json(baseline_file, baseline)
    baseline_forecast = solve(annual_times, cases["annual_noisy"].initial_state, base_params, **config["solver"])
    write_csv(output / "least_squares_forecast.csv", ["Year", "Hare", "Lynx"],
              np.column_stack((annual_times + 1900, baseline_forecast)))
    # Only here is the held-out truth/observation array used for scoring frozen forecasts.
    score_rows = []
    for s in eligible:
        predicted = np.loadtxt(output / "runs" / s["run_id"] / "forecast.csv", delimiter=",", skiprows=1)[:, 1:]
        for target, obs in (("noisy_observations", annual_obs), ("latent_truth", annual_truth)):
            score_rows.append({"method": "PINN-derived ODE", "run_id": s["run_id"], "target": target,
                               "selected": s["run_id"] == selected_id, **metrics(predicted[16:], obs[16:])})
    for target, obs in (("noisy_observations", annual_obs), ("latent_truth", annual_truth)):
        score_rows.append({"method": "least_squares", "run_id": "least_squares", "target": target,
                           "selected": True, **metrics(baseline_forecast[16:], obs[16:])})
    write_csv(output / "heldout_metrics.csv", list(score_rows[0]), [list(r.values()) for r in score_rows])
    # Handoff contains only the five forecast years, in original synthetic evaluation units.
    chosen = np.loadtxt(output / "runs" / selected_id / "forecast.csv", delimiter=",", skiprows=1)
    write_csv(output / "predictions_for_advay.csv", ["Year", "Hare", "Lynx"], chosen[16:])
    save_json(output / "identifiability.json", {
        "three_parameters": sensitivity_spectrum(cases["annual_noisy"], Parameters(**selected["parameters"]), config, config["trainable"]),
        "six_parameters": sensitivity_spectrum(cases["annual_noisy"], Parameters(**selected["parameters"]), config, NAMES),
        "interpretation": "Local finite-difference diagnostic at learned parameters, not a proof of global or structural identifiability"})
    save_json(output / "manifest.json", {
        "kind": "synthetic", "quick": quick, "python": sys.version, "platform": platform.platform(),
        "versions": {p: importlib.metadata.version(p) for p in ("torch", "numpy", "scipy", "matplotlib")},
        "config_sha256": sha256(root / "configs/synthetic.json"), "selected_run": selected_id,
        "run_count": len(summaries), "seeds": seeds, "solver": config["solver"],
        "training_source_hashes": {p.name: sha256(p) for p in data_dir.glob("*train.csv")},
        "model_source_hashes": {p.name: sha256(p) for p in (root / "src/lynx_hare").glob("*.py")},
        "heldout_rule": "Only final scoring and display read years 1916-1920; no seed, loss-weight or initialization selected on test errors"})
    from .figures import make_figures
    make_figures(root, output, annual_truth, annual_obs, summaries, score_rows)
    print(f"Completed: {output}; selected {selected_id} using training objective only", flush=True)
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="API smoke run, not scientific evidence")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    run(args.root, quick=args.quick)


if __name__ == "__main__":
    main()
