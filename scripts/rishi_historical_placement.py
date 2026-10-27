"""Where do the historical fits lie relative to the Hopf threshold?

Run: python scripts/rishi_historical_placement.py

Reads every saved parameter set (Yash's PINN seeds incl. sensitivity runs, and all 18
matched least-squares starts); it never opens the held-out test file. For each set it
computes sigma = K/K_H, the eigenvalues at E*, the e-folding time and the linear period
(Joel's closed forms), flags coefficients on their box bounds, measures the period and
lynx lag of the first century simulated from the fitted 1900 state, and for sigma > 1
the long-run cycle. For the two selected main fits it draws a bifurcation diagram in K.

Solvers: the 1900-1920 reconstruction check uses model.solve with the historical settings
(RK45, rtol 1e-8, atol 1e-10, max_step 0.1). Long-run runs use simulation.integrate
(RK45, rtol 1e-10, atol 1e-12). Outputs: results/simulations/historical/,
report/graphs/rishi_historical_*.
"""
import csv
import json
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lynx_hare.model import Parameters, NAMES, solve  # noqa: E402
from lynx_hare import simulation as sim, simulation_plots as plots  # noqa: E402

HIST = ROOT / "results" / "historical"
OUT = ROOT / "results" / "simulations" / "historical"
GRAPHS = ROOT / "report" / "graphs"
TRAIN = ROOT / "data" / "historical" / "train_1900_1915.csv"
VARIANT_NAME = {"main": "main", "log_errors": "log errors", "fitted_initial": "fitted initial state"}
BOUND_TOL = 0.005          # a coefficient within 0.5% of a box limit counts as "on the bound"
BURN_MIN, BURN_MAX = 3000.0, 60000.0


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def on_bounds(params, bounds):
    hits = []
    for k in NAMES:
        lo, hi = bounds[k]
        if params[k] <= lo * (1 + BOUND_TOL):
            hits.append(f"{k}=lower")
        elif params[k] >= hi * (1 - BOUND_TOL):
            hits.append(f"{k}=upper")
    return hits


def collect_fits():
    fits = []
    pinn_sets = [("yash_pinn_v1", "historical.json", ""),
                 ("yash_pinn_wider_v1", "historical_wider_bounds.json", ", wider bounds"),
                 ("yash_pinn_physics100_v1", "historical_physics100.json", ", physics weight 100")]
    for folder, cfg, suffix in pinn_sets:
        bounds = load_json(ROOT / "configs" / cfg)["bounds"]
        selected = {v["run_id"] for v in load_json(HIST / folder / "selected_runs.json").values()}
        for r in load_json(HIST / folder / "parameters_for_team.json"):
            variant = r["run_id"].rsplit("_seed", 1)[0]
            fits.append(dict(method="PINN", label=f"PINN {VARIANT_NAME[variant]}{suffix}",
                             run=f"{folder}/{r['run_id']}", params={k: r[k] for k in NAMES},
                             y0=r["ode_initial"], selected=r["run_id"] in selected, poor=False,
                             bounds=bounds, reported_sigma=r["sigma"]))
    base = HIST / "yash_matching_baseline_v2"
    bounds = load_json(base / "config.json")["bounds"]
    chosen = {v: d["start"] for v, d in load_json(base / "selected.json").items()}
    starts = [s for s in load_json(base / "starts.json") if s["valid"]]
    best = {v: min(s["training_mse"] for s in starts if s["variant"] == v) for v in chosen}
    for s in starts:
        v = s["variant"]
        fits.append(dict(method="Least squares", label=f"Least squares {VARIANT_NAME[v]}",
                         run=f"yash_matching_baseline_v2/{v}/start{s['start']}", params=s["parameters"],
                         y0=s["ode_initial"], selected=s["start"] == chosen[v],
                         poor=s["training_mse"] > 1.5 * best[v], bounds=bounds,
                         training_mse=s["training_mse"], reported_sigma=None))
    return fits


def transient(p, y0, years=100.0):
    """Period and lynx lag of the oscillation simulated from the fitted 1900 state."""
    t = np.linspace(0, years, 20001)
    H, P = sim.integrate(p, y0, (0, years), t_eval=t).y
    hp, pp = sim.local_maxima(H), sim.local_maxima(P)
    if len(hp) < 2:
        return np.nan, np.nan
    lags = [t[pp][t[pp] > th][0] - th for th in t[hp] if np.any(t[pp] > th)]
    return float(np.mean(np.diff(t[hp]))), float(np.mean(lags)) if lags else np.nan


def burn_in(growth):
    return float(np.clip(30.0 / abs(growth), BURN_MIN, BURN_MAX)) if growth else BURN_MAX


def sweep_in_sigma(p, sigmas, y0):
    lin = sim.linear_summary(p)
    rows = []
    for s in sigmas:
        q = sim.with_K(p, s * lin["K_H"])
        g = sim.linear_summary(q)["growth_rate"]
        rows.append(sim.attractor_summary(q, y0, t_burn=burn_in(g), t_record=300.0, samples=15001))
    return dict(sigma=np.asarray(sigmas), Hmax=np.array([r["Hmax"] for r in rows]),
                Hmin=np.array([r["Hmin"] for r in rows]), Hstar=lin["Hstar"])


def check_reconstruction():
    """Rebuild Yash's saved 1900-1920 ODE path with model.solve and the historical settings."""
    cfg = load_json(ROOT / "configs" / "historical.json")["solver"]
    sel = load_json(HIST / "yash_pinn_v1" / "selected_runs.json")["main"]
    with open(HIST / "yash_pinn_v1" / "runs" / sel["run_id"] / "ode_dense.csv") as f:
        rows = np.array([[float(x) for x in r] for r in list(csv.reader(f))[1:]])
    t = rows[:, 0] - 1900.0
    y = solve(t, rows[0, 1:], Parameters(**sel["parameters"]), **cfg)
    return float(np.abs(y - rows[:, 1:]).max())


SIGMA_GRID = np.r_[np.linspace(0.5, 0.95, 10), np.linspace(1.025, 2.0, 40)]
ORDER = ["PINN main", "PINN log errors", "PINN fitted initial state", "PINN main, wider bounds",
         "PINN main, physics weight 100", "Least squares main", "Least squares log errors",
         "Least squares fitted initial state"]


def compute():
    """All numbers and figure inputs; writes nothing."""
    with open(TRAIN) as f:
        train = np.array([[float(x) for x in r] for r in list(csv.reader(f))[1:]])
    data_range = (float(train[:, 1].min()), float(train[:, 1].max()))
    recon = check_reconstruction()
    print(f"model.solve reconstruction of Yash's selected PINN path: max abs difference {recon:.2e}")

    fits = collect_fits()
    table = []
    for f in fits:
        p = Parameters(**f["params"])
        lin = sim.linear_summary(p)
        f.update(lin)
        if f["reported_sigma"] is not None:
            assert abs(f["reported_sigma"] - lin["sigma"]) < 1e-9 * lin["sigma"], f["run"]
        f["transient_period"], f["transient_lag"] = transient(p, f["y0"])
        f["cycle"] = None
        if f["selected"] and lin["feasible"] and lin["sigma"] > 1:
            a = sim.attractor_summary(p, f["y0"], t_burn=burn_in(lin["growth_rate"]), t_record=400.0)
            f["cycle"] = a
        f["bound_hits"] = on_bounds(f["params"], f["bounds"])
        lam = lin["eigenvalues"][np.argmax(lin["eigenvalues"].imag)]
        table.append({
            "label": f["label"], "run": f["run"], "selected": f["selected"], "poor_local_minimum": f["poor"],
            **{k: round(f["params"][k], 4) for k in NAMES},
            "H0": round(f["y0"][0], 3), "P0": round(f["y0"][1], 3),
            "Hstar": round(lin["Hstar"], 3), "K_H": round(lin["K_H"], 3), "sigma": round(lin["sigma"], 4),
            "regime": lin["regime"], "eigenvalue": f"{lam.real:+.4f}{lam.imag:+.4f}i",
            "efold_years": round(lin["efold_years"], 1), "linear_period": round(lin["linear_period"], 2),
            "first_century_period": round(f["transient_period"], 2), "first_century_lag": round(f["transient_lag"], 2),
            "cycle_H_range": "" if f["cycle"] is None else f"[{f['cycle']['Hmin']:.2f}, {f['cycle']['Hmax']:.1f}]",
            "cycle_P_range": "" if f["cycle"] is None else f"[{f['cycle']['Pmin']:.2f}, {f['cycle']['Pmax']:.1f}]",
            "cycle_period": "" if f["cycle"] is None else round(f["cycle"]["period"], 2),
            "parameters_on_bounds": " ".join(f["bound_hits"]),
            "training_mse": round(f.get("training_mse", np.nan), 6),
        })
    panels = []
    for label in ("PINN main", "Least squares main"):
        f = next(x for x in fits if x["label"] == label and x["selected"])
        sw = sweep_in_sigma(Parameters(**f["params"]), SIGMA_GRID, f["y0"])
        rng = None if f["cycle"] is None else (f["cycle"]["Hmin"], f["cycle"]["Hmax"])
        panels.append(dict(title=f"Selected {label} fit", fit_sigma=f["sigma"], fit_range=rng, **sw))

    groups = {}
    for f in fits:
        if not f["poor"]:
            groups.setdefault(f["label"], []).append(f["sigma"])
    summary = {
        "inputs": ["results/historical/yash_pinn_v1", "results/historical/yash_pinn_wider_v1",
                   "results/historical/yash_pinn_physics100_v1", "results/historical/yash_matching_baseline_v2"],
        "test_file_opened": False,
        "reconstruction_max_abs_difference": recon,
        "sigma_range_by_group_excluding_poor_minima": {k: [min(v), max(v)] for k, v in groups.items()},
        "selected": {f["label"]: {k: table[i][k] for k in ("sigma", "regime", "eigenvalue", "efold_years",
                                                         "linear_period", "first_century_period",
                                                         "first_century_lag", "cycle_H_range", "cycle_period",
                                                         "parameters_on_bounds")}
                     for i, f in enumerate(fits) if f["selected"]},
        "training_hare_range": data_range,
    }
    return dict(fits=fits, table=table, panels=panels, data_range=data_range, summary=summary)


def figures(res):
    sig = plots.historical_sigma([dict(label=f["label"], sigma=f["sigma"], selected=f["selected"], poor=f["poor"])
                                  for f in res["fits"]], ORDER)
    bif = plots.historical_bifurcation(res["panels"], res["data_range"])
    return sig, bif


def main():
    plt.rcParams.update(plots.STYLE)
    res = compute()
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "fits.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(res["table"][0]))
        w.writeheader()
        w.writerows(res["table"])
    for pn in res["panels"]:
        with open(OUT / f"sweep_{pn['title'].split()[1].lower()}_main.csv", "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["sigma", "Hmax", "Hmin"])
            w.writerows(zip(pn["sigma"], pn["Hmax"], pn["Hmin"]))
    sig, bif = figures(res)
    plots.save(sig, "rishi_historical_sigma", OUT / "figures", GRAPHS)
    plots.save(bif, "rishi_historical_bifurcation", OUT / "figures", GRAPHS)
    plt.close("all")
    (OUT / "summary.json").write_text(json.dumps(res["summary"], indent=2, default=float))
    print(json.dumps(res["summary"], indent=2, default=float))


if __name__ == "__main__":
    main()
