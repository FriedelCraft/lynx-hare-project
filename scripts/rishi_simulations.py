"""Numerical simulations for Rishi's section. Run: python scripts/rishi_simulations.py

Uses the shared src/lynx_hare/model.py (rhs) and Joel's src/lynx_hare/stability.py,
reproduces Joel's validation targets, and writes figures, tables and a JSON summary to
results/simulations/ plus EPS/PDF copies to report/graphs/rishi_*.

Illustrative parameters (NOT fitted): H, P in thousands of pelts, t in years.
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
from lynx_hare.model import Parameters  # noqa: E402
from lynx_hare import simulation as sim, simulation_plots as plots, stability as st  # noqa: E402

OUT = ROOT / "results" / "simulations"
FIG = OUT / "figures"
GRAPHS = ROOT / "report" / "graphs"
TARGETS = ROOT / "results" / "stability" / "validation_targets.json"


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def close(a, b, rel=1e-3, abs_=1e-3):
    if a is None or b is None or (np.isnan(a) and np.isnan(b)):
        return True
    return abs(a - b) <= max(abs_, rel * abs(b))


def main():
    plt.rcParams.update(plots.STYLE)
    OUT.mkdir(parents=True, exist_ok=True)
    base = Parameters(K=150.0, **sim.ILLUSTRATIVE)
    KH = st.hopf_threshold(base)
    summary = {"params": sim.ILLUSTRATIVE, "solver": {"method": "RK45", "rtol": sim.RTOL, "atol": sim.ATOL},
               "initial_state": sim.Y0, "burn_in": sim.T_BURN, "burn_in_near_hopf": sim.T_BURN_NEAR_HOPF,
               "Hstar": st.coexistence_prey(base), "K_H": KH, "T0": st.onset_period(base)}

    # Fig 1: solver accuracy
    fig, check = plots.solver_validation()
    plots.save(fig, "rishi_solver_validation", FIG, GRAPHS); plt.close(fig)
    pF = sim.with_K(base, 150.0)
    t = np.linspace(0, 200, 8001)
    a = sim.integrate(pF, sim.Y0, (0, 200), t_eval=t).y
    b = sim.integrate(pF, sim.Y0, (0, 200), t_eval=t, rtol=1e-12, atol=1e-14).y
    check["relative_change_with_100x_tighter_tolerance"] = float(np.abs(a - b).max() / np.abs(b).max())
    check["min_state_K150"] = float(a.min())
    summary["solver_check"] = check
    print("solver check:", check)

    # Table 2 reproduction
    rows = sim.regime_table(base)
    targets = {r["label"]: r for r in json.loads(TARGETS.read_text())["regimes"]}
    table, all_ok = [], True
    for r in rows:
        tg = targets[r["label"]]
        ok = all(close(r[k], tg[k], rel=5e-3, abs_=5e-2) for k in ("Hmin", "Hmax", "Pmin", "Pmax", "period", "lag"))
        all_ok &= ok
        table.append(dict(label=r["label"], K=r["K"], regime=r["regime"],
                          eigenvalues=" ".join(f"{z.real:+.4f}{z.imag:+.4f}i" for z in r["eig"]),
                          Hmin=round(r["Hmin"], 3), Hmax=round(r["Hmax"], 3),
                          Pmin=round(r["Pmin"], 3), Pmax=round(r["Pmax"], 3),
                          period=round(r["period"], 3), lag=round(r["lag"], 3), matches_joel=ok))
        print(f"{r['label']} K={r['K']:>5g}  H[{r['Hmin']:.2f},{r['Hmax']:.2f}] P[{r['Pmin']:.2f},{r['Pmax']:.2f}]"
              f"  T={r['period']:.2f} lag={r['lag']:.2f}  {'OK' if ok else 'MISMATCH'}")
    write_csv(OUT / "regime_table.csv", table)
    summary["regimes_match_joel_targets"] = bool(all_ok)

    # Fig 2-4
    fig = plots.regimes(base)
    plots.save(fig, "rishi_regimes", FIG, GRAPHS); plt.close(fig)
    fig, peaks = plots.limit_cycle_attracts(base)
    plots.save(fig, "rishi_limit_cycle", FIG, GRAPHS); plt.close(fig)
    summary["limit_cycle_last_peaks"] = peaks
    fig, eig = plots.eigenvalues_vs_K(base, np.linspace(30.5, 200, 800))
    plots.save(fig, "rishi_eigenvalues", FIG, GRAPHS); plt.close(fig)
    summary["hopf_crossing_numerical"] = sim.hopf_crossing(base, 60.0, 120.0)
    summary.update(eig)

    # Fig 5: bifurcation sweep
    sweep = sim.bifurcation_sweep(base, np.linspace(32, 200, 113))
    fig = plots.bifurcation(base, sweep)
    plots.save(fig, "rishi_bifurcation", FIG, GRAPHS); plt.close(fig)
    write_csv(OUT / "bifurcation.csv", [{k: float(v[i]) for k, v in sweep.items()} for i in range(len(sweep["K"]))])
    below = sweep["K"] < KH - 1
    summary["max_spread_below_KH"] = float(np.max(sweep["Hmax"][below] - sweep["Hmin"][below]))
    summary["cycle_min_at_K200"] = {"H": float(sweep["Hmin"][-1]), "P": float(sweep["Pmin"][-1])}

    # Fig 6: amplitude law and period
    law = sim.amplitude_law(base, np.geomspace(0.5, 8.0, 12))
    fig = plots.amplitude_and_period(law)
    plots.save(fig, "rishi_amplitude_period", FIG, GRAPHS); plt.close(fig)
    write_csv(OUT / "amplitude_law.csv", [dict(dK=float(d), half_amplitude=float(a), period=float(p))
                                          for d, a, p in zip(law["dK"], law["amplitude"], law["period"])])
    summary["amplitude_law"] = {k: law[k] for k in ("slope", "coefficient", "coefficient_sqrt", "onset_period")}
    summary["period_closest_to_onset"] = float(law["period"][0])

    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=float))
    print(json.dumps({k: summary[k] for k in ("hopf_crossing_numerical", "node_to_focus_K",
                                              "max_spread_below_KH", "cycle_min_at_K200",
                                              "amplitude_law", "period_closest_to_onset")}, indent=2))
    if not all_ok:
        raise SystemExit("Regime table does not match Joel's validation targets")


if __name__ == "__main__":
    main()
