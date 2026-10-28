"""Advay, phase 3: check the baseline against Yash's matched least-squares benchmark
and draw the training fits. Uses training data and frozen forecasts only; the test
file is not opened and no held-out score is computed.

    python scripts/advay_compare_benchmark.py [results/historical/advay_baseline_v2]
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
from lynx_hare.data import read_training

MINE = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "results" / "historical" / "advay_baseline_v2"
YASH = ROOT / "results" / "historical" / "yash_matching_baseline_v2"
GRAPHS = ROOT / "report" / "graphs"
VARIANTS = ["main", "log_errors", "fitted_initial"]
TITLES = {"main": "Main (additive errors, observed 1900 state)",
          "log_errors": "Sensitivity: log errors", "fitted_initial": "Sensitivity: fitted 1900 state"}
HARE, LYNX, GREY, TEST_FILL = "#1f5fa8", "#c0392b", "#777777", "#eeeeee"
STYLE = {"font.size": 11, "axes.grid": True, "axes.axisbelow": True, "grid.color": "#dddddd",
         "legend.framealpha": 1.0, "savefig.bbox": "tight"}


def table(path):
    with open(path, newline="") as f:
        return np.array([[float(v) for v in r.values()] for r in csv.DictReader(f)])


def compare():
    mine = json.loads((MINE / "selected.json").read_text())
    yash = json.loads((YASH / "selected.json").read_text())
    out = {}
    for v in VARIANTS:
        a, b = mine[v], yash[v]
        fa, fb = table(MINE / f"forecast_{v}.csv"), table(YASH / f"forecast_{v}.csv")
        out[v] = {
            "training_cost": {"advay": a["cost"], "yash": b["cost"],
                              "relative_difference": (a["cost"] - b["cost"]) / b["cost"]},
            "parameters": {k: {"advay": a["parameters"][k], "yash": b["parameters"][k],
                               "ratio": a["parameters"][k] / b["parameters"][k]} for k in a["parameters"]},
            "forecast_max_abs_difference": {
                "hare": float(np.abs(fa[:, 1] - fb[:, 1]).max()),
                "lynx": float(np.abs(fa[:, 2] - fb[:, 2]).max())},
            "advay_sigma": a["sigma"], "advay_regime": a["regime"], "advay_at_bound": a["at_bound"],
        }
    (MINE / "benchmark_comparison.json").write_text(json.dumps(out, indent=2) + "\n")
    return out


def figure():
    data = read_training(ROOT / "data" / "historical" / "train_1900_1915.csv", 1900, 1915)
    fig, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
    for ax, v in zip(axes, VARIANTS):
        ode = table(MINE / f"ode_{v}.csv")
        ax.axvspan(1915.5, 1920.5, color=TEST_FILL, zorder=0)
        ax.plot(ode[:, 1], ode[:, 2], color=HARE, lw=2, label="Hare, fitted ODE")
        ax.plot(ode[:, 1], ode[:, 3], color=LYNX, lw=2, label="Lynx, fitted ODE")
        ax.plot(data.years, data.observations[:, 0], "o", color=HARE, mfc="white", ms=6, label="Hare, training data")
        ax.plot(data.years, data.observations[:, 1], "s", color=LYNX, mfc="white", ms=6, label="Lynx, training data")
        ax.set(ylabel="Thousands of pelts", title=TITLES[v], xlim=(1899.5, 1920.5))
        ax.text(1915.8, ax.get_ylim()[1] * 0.92, "forecast\n(scored in phase 4)", color=GREY, fontsize=9, va="top")
    fig.legend(*axes[0].get_legend_handles_labels(), loc="upper center", ncol=4, fontsize=9,
               bbox_to_anchor=(0.5, 1.03), frameon=False)
    axes[-1].set(xlabel="Year")
    axes[-1].set_xticks(np.arange(1900, 1921, 2))
    fig.tight_layout()
    for folder, exts in ((MINE / "figures", ("png", "eps", "pdf")), (GRAPHS, ("eps", "pdf"))):
        folder.mkdir(parents=True, exist_ok=True)
        for ext in exts:
            fig.savefig(folder / f"advay_baseline_fit.{ext}", dpi=200 if ext == "png" else None)
    plt.close(fig)


def sigma_figure():
    starts = json.loads((MINE / "starts.json").read_text())
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), sharey=True)
    for ax, v in zip(axes, VARIANTS):
        rows = [r for r in starts if r["variant"] == v and not r["failed_solve"]]
        best = min(r["cost"] for r in rows)
        cost = np.array([r["cost"] / best for r in rows])
        sig = np.array([r["sigma"] if r["sigma"] is not None else np.nan for r in rows])
        ok = np.isfinite(sig)
        ax.scatter(sig[ok], cost[ok], s=36, color="#333333", edgecolor="white", linewidth=1, zorder=3)
        ax.axvline(1, color=LYNX, lw=1.5, ls="--")
        ax.annotate(f"selected: σ = {sig[cost == 1][0]:.2f}", (sig[cost == 1][0], 1),
                    textcoords="offset points", xytext=(10, 8), fontsize=9)
        ax.set(xscale="log", yscale="log", xlabel="σ = K / K_H", title={"main": "Main", "log_errors": "Log errors", "fitted_initial": "Fitted 1900 state"}[v])
        ax.text(0.03, 0.95, f"{(~ok).sum()} starts without coexistence\nnot shown", transform=ax.transAxes,
                fontsize=9, va="top", color=GREY) if (~ok).any() else None
    axes[0].set_ylabel("Training cost / best cost")
    fig.tight_layout()
    for folder, exts in ((MINE / "figures", ("png", "eps", "pdf")), (GRAPHS, ("eps", "pdf"))):
        for ext in exts:
            fig.savefig(folder / f"advay_baseline_sigma.{ext}", dpi=200 if ext == "png" else None)
    plt.close(fig)


def main():
    plt.rcParams.update(STYLE)
    out = compare()
    figure()
    sigma_figure()
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
