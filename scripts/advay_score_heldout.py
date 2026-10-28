"""Advay, phase 4: score every frozen forecast on 1916-1920, as declared in
docs/advay_scoring_plan.md. This is the only Advay script that opens the test file.
It fits nothing.

    python scripts/advay_score_heldout.py
"""
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results" / "historical"
DATA = ROOT / "data" / "historical"
OUT = BASE / "advay_evaluation_v1"
GRAPHS, TABLES = ROOT / "report" / "graphs", ROOT / "report" / "tables"
VARIANTS = ["main", "log_errors", "fitted_initial"]
PINN_SELECTED = {"main": "main_seed17", "log_errors": "log_errors_seed29",
                 "fitted_initial": "fitted_initial_seed17"}   # Yash's pre-scoring selection
HARE, LYNX, GREY, TEST_FILL = "#1f5fa8", "#c0392b", "#777777", "#eeeeee"
LS_C, PINN_C = "#1f5fa8", "#d9822b"
STYLE = {"font.size": 11, "axes.grid": True, "axes.axisbelow": True, "grid.color": "#dddddd",
         "legend.framealpha": 1.0, "savefig.bbox": "tight"}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    with open(path, newline="") as f:
        return np.array([[float(v) for v in r.values()] for r in csv.DictReader(f)])


def write_csv(path, header, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def forecasts():
    """Every forecast in the plan, hash-checked. Returns list of dicts."""
    items = []
    for folder, method, label in (("advay_baseline_v2", "least squares", "LS-Advay"),
                                  ("yash_matching_baseline_v2", "least squares", "LS-Yash")):
        manifest = json.loads((BASE / folder / "manifest.json").read_text())
        assert manifest["status"] == "forecasts_frozen_unscored", folder
        hashes = {k.replace("\\", "/"): v for k, v in manifest["output_hashes"].items()}
        for v in VARIANTS:
            name = f"forecast_{v}.csv"
            path = BASE / folder / name
            if sha256(path) != hashes[name]:
                raise SystemExit(f"Hash mismatch: {path}")
            items.append({"label": label, "method": method, "variant": v, "run": "selected",
                          "case": folder, "path": path, "sha256": hashes[name]})
    freeze = json.loads((BASE / "yash_evaluation_v1" / "forecast_freeze.json").read_text())
    folders = {"primary": ("yash_pinn_v1", "PINN"), "wider_bounds": ("yash_pinn_wider_v1", "PINN-wider"),
               "physics100": ("yash_pinn_physics100_v1", "PINN-physics100")}
    for c in freeze["forecast_choices"]:
        if c["case"] not in folders:
            continue
        folder, label = folders[c["case"]]
        path = BASE / folder / "runs" / c["run_id"] / "forecast.csv"
        if sha256(path) != c["forecast_sha256"]:
            raise SystemExit(f"Hash mismatch: {path}")
        items.append({"label": label, "method": "PINN-derived ODE", "variant": c["variant"],
                      "run": c["run_id"], "case": c["case"], "path": path, "sha256": c["forecast_sha256"],
                      "yash_selected": c["selected"]})
    return items


def references():
    train = read(DATA / "train_1900_1915.csv")
    years = np.arange(1916, 1921)
    return {"Persistence (1915 value)": np.column_stack([years, np.tile(train[-1, 1:], (5, 1))]),
            "Training mean": np.column_stack([years, np.tile(train[:, 1:].mean(0), (5, 1))])}


def metrics(pred, obs):
    d = pred - obs
    return {"hare_rmse": float(np.sqrt(np.mean(d[:, 0] ** 2))), "lynx_rmse": float(np.sqrt(np.mean(d[:, 1] ** 2))),
            "hare_mae": float(np.mean(np.abs(d[:, 0]))), "lynx_mae": float(np.mean(np.abs(d[:, 1])))}


def verdict(a, b, err_a, err_b, species):
    """Declared rule: 'better' only if smaller RMSE and MAE and smaller |error| in >= 3 of 5 years."""
    i = 0 if species == "hare" else 1
    wins_a = int(np.sum(np.abs(err_a[:, i]) < np.abs(err_b[:, i])))
    if a[f"{species}_rmse"] < b[f"{species}_rmse"] and a[f"{species}_mae"] < b[f"{species}_mae"] and wins_a >= 3:
        return "LS better", wins_a
    if b[f"{species}_rmse"] < a[f"{species}_rmse"] and b[f"{species}_mae"] < a[f"{species}_mae"] and 5 - wins_a >= 3:
        return "PINN better", wins_a
    return "similar", wins_a


def save_fig(fig, stem):
    for folder, exts in ((OUT / "figures", ("png", "eps", "pdf")), (GRAPHS, ("eps", "pdf"))):
        folder.mkdir(parents=True, exist_ok=True)
        for ext in exts:
            fig.savefig(folder / f"{stem}.{ext}", dpi=200 if ext == "png" else None)
    plt.close(fig)


def trajectories(variant):
    ls = read(BASE / "advay_baseline_v2" / f"ode_{variant}.csv")[:, 1:]          # Year, Hare, Lynx
    pinn = read(BASE / "yash_pinn_v1" / "runs" / PINN_SELECTED[variant] / "ode_dense.csv")
    return ls, pinn


def panel(ax, k, train, test, ls, pinn, title):
    color = HARE if k == 1 else LYNX
    ax.axvspan(1915.5, 1920.5, color=TEST_FILL, zorder=0)
    ax.plot(ls[:, 0], ls[:, k], color=LS_C, lw=2, label="Least squares (Advay)")
    ax.plot(pinn[:, 0], pinn[:, k], color=PINN_C, lw=2, ls="--", label="PINN-derived ODE (Yash)")
    ax.plot(train[:, 0], train[:, k], "o", color="#333333", mfc="white", ms=5, label="Training data")
    ax.plot(test[:, 0], test[:, k], "o", color="#111111", ms=6, label="Held-out data")
    ax.set(title=title, ylabel="Thousands of pelts", xlim=(1899.5, 1920.5))


def top_legend(fig, ax):
    fig.legend(*ax.get_legend_handles_labels(), loc="upper center", ncol=4, fontsize=9,
               bbox_to_anchor=(0.5, 1.03), frameon=False)


def main():
    if OUT.exists():
        raise SystemExit("Output exists; scoring is done once per declared plan")
    plt.rcParams.update(STYLE)
    items = forecasts()
    test_path = DATA / "test_1916_1920.csv"
    split = json.loads((DATA / "split.json").read_text())
    if sha256(test_path) != split["test"]["sha256"]:
        raise SystemExit("Test file hash mismatch")
    test = read(test_path)                       # <- the only read of held-out data
    train = read(DATA / "train_1900_1915.csv")
    years = test[:, 0]
    OUT.mkdir(parents=True)

    rows, yearly, pred = [], [], {}
    for it in items:
        f = read(it["path"])
        assert np.allclose(f[:, 0], years), it["path"]
        m = metrics(f[:, 1:], test[:, 1:])
        key = (it["label"], it["variant"], it["run"])
        pred[key] = f[:, 1:]
        rows.append([it["label"], it["method"], it["variant"], it["run"], it.get("yash_selected", ""),
                     m["hare_rmse"], m["hare_mae"], m["lynx_rmse"], m["lynx_mae"], it["sha256"]])
    for name, f in references().items():
        m = metrics(f[:, 1:], test[:, 1:])
        pred[(name, "reference", "-")] = f[:, 1:]
        rows.append([name, "reference", "-", "-", "", m["hare_rmse"], m["hare_mae"], m["lynx_rmse"], m["lynx_mae"], ""])
    header = ["label", "method", "variant", "run", "yash_selected", "hare_rmse", "hare_mae",
              "lynx_rmse", "lynx_mae", "forecast_sha256"]
    write_csv(OUT / "metrics.csv", header, rows)
    by = {(r[0], r[2], r[3]): dict(zip(header, r)) for r in rows}

    # Headline and sensitivity pairs, as declared.
    pairs = {}
    for v in VARIANTS:
        ls_key, pinn_key = ("LS-Advay", v, "selected"), ("PINN", v, PINN_SELECTED[v])
        e_ls, e_pinn = pred[ls_key] - test[:, 1:], pred[pinn_key] - test[:, 1:]
        for y, a, b in zip(years, e_ls, e_pinn):
            yearly.append([v, int(y), *a, *b])
        pairs[v] = {"status": "headline" if v == "main" else "sensitivity",
                    "least_squares": {k: by[ls_key][k] for k in ("hare_rmse", "hare_mae", "lynx_rmse", "lynx_mae")},
                    "pinn": {k: by[pinn_key][k] for k in ("hare_rmse", "hare_mae", "lynx_rmse", "lynx_mae")},
                    "pinn_run": PINN_SELECTED[v]}
        for sp in ("hare", "lynx"):
            pairs[v][f"{sp}_verdict"], pairs[v][f"{sp}_ls_closer_years"] = verdict(
                pairs[v]["least_squares"], pairs[v]["pinn"], e_ls, e_pinn, sp)
    write_csv(OUT / "yearly_errors.csv", ["variant", "Year", "ls_hare_err", "ls_lynx_err",
                                          "pinn_hare_err", "pinn_lynx_err"], yearly)
    (OUT / "comparison.json").write_text(json.dumps(pairs, indent=2) + "\n")

    # Cross-check with Yash's evaluation.
    with open(BASE / "yash_evaluation_v1" / "heldout_metrics.csv", newline="") as f:
        yash = list(csv.DictReader(f))
    label = {"primary": "PINN", "wider_bounds": "PINN-wider", "physics100": "PINN-physics100", "baseline": "LS-Yash"}
    checks, worst = [], 0.0
    for r in yash:
        key = (label[r["case"]], r["variant"], "selected" if r["case"] == "baseline" else r["run_id"])
        mine = by[key]
        diff = max(abs(float(r[k]) - mine[k]) for k in ("hare_rmse", "hare_mae", "lynx_rmse", "lynx_mae"))
        worst = max(worst, diff)
        checks.append({"case": r["case"], "run": r["run_id"], "variant": r["variant"], "max_abs_diff": diff})
    (OUT / "crosscheck_yash.json").write_text(json.dumps(
        {"tolerance": 1e-9, "max_abs_diff": worst, "all_match": worst <= 1e-9, "rows": checks}, indent=2) + "\n")

    # Figures.
    ls, pinn = trajectories("main")
    fig, ax = plt.subplots(2, 1, figsize=(10, 7.5), sharex=True)
    panel(ax[0], 1, train, test, ls, pinn, "Hare")
    panel(ax[1], 2, train, test, ls, pinn, "Lynx")
    ax[1].set(xlabel="Year")
    ax[1].set_xticks(np.arange(1900, 1921, 2))
    fig.tight_layout()
    top_legend(fig, ax[0])
    save_fig(fig, "advay_heldout_overlay")

    fig, axes = plt.subplots(3, 2, figsize=(12, 10), sharex=True)
    names = {"main": "main", "log_errors": "log errors", "fitted_initial": "fitted 1900 state"}
    for i, v in enumerate(VARIANTS):
        ls, pinn = trajectories(v)
        panel(axes[i, 0], 1, train, test, ls, pinn, f"Hare, {names[v]}")
        panel(axes[i, 1], 2, train, test, ls, pinn, f"Lynx, {names[v]}")
        for a in axes[i]:
            a.set_xlim(1909.5, 1920.5)
    for a in axes[-1]:
        a.set(xlabel="Year")
    fig.tight_layout()
    top_legend(fig, axes[0, 0])
    save_fig(fig, "advay_heldout_variants")

    show = [("LS-Advay", "main", "selected", "Least squares", LS_C),
            ("PINN", "main", "main_seed17", "PINN-derived ODE", PINN_C),
            ("Persistence (1915 value)", "-", "-", "Persistence", "#8c8c8c"),
            ("Training mean", "-", "-", "Training mean", "#c4c4c4")]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    for ax, sp in zip(axes, ("hare", "lynx")):
        x = np.arange(2)
        w = 0.2
        for j, (lab, v, run, name, c) in enumerate(show):
            vals = [by[(lab, v, run)][f"{sp}_rmse"], by[(lab, v, run)][f"{sp}_mae"]]
            bars = ax.bar(x + (j - 1.5) * w, vals, w, color=c, edgecolor="white", linewidth=2, label=name)
            for b, val in zip(bars, vals):
                ax.annotate(f"{val:.1f}", (b.get_x() + b.get_width() / 2, val), textcoords="offset points",
                            xytext=(0, 2), ha="center", fontsize=8, color="#333333")
        ax.set_xticks(x, ["RMSE", "MAE"])
        ax.set(title=f"{sp.capitalize()}, 1916–1920 (main variant)")
    axes[0].set_ylabel("Error (thousands of pelts)")
    axes[0].legend(fontsize=9, loc="upper left")
    fig.tight_layout()
    save_fig(fig, "advay_heldout_metrics")

    # LaTeX table: headline + sensitivities + references.
    def line(name, d):
        return f"{name} & {d['hare_rmse']:.2f} & {d['hare_mae']:.2f} & {d['lynx_rmse']:.2f} & {d['lynx_mae']:.2f} \\\\"
    tex = [r"\begin{tabular}{llrrrr}", r"\hline",
           r"Variant & Method & Hare RMSE & Hare MAE & Lynx RMSE & Lynx MAE \\", r"\hline"]
    for v in VARIANTS:
        tag = {"main": "Main (headline)", "log_errors": "Log errors", "fitted_initial": "Fitted 1900 state"}[v]
        tex.append(line(f"{tag} & Least squares", pairs[v]["least_squares"]))
        tex.append(line(f" & PINN-derived ODE ({PINN_SELECTED[v].split('_')[-1]})", pairs[v]["pinn"]))
    tex.append(r"\hline")
    for name in ("Persistence (1915 value)", "Training mean"):
        tex.append(line(f"Reference & {name}", by[(name, "-", "-")]))
    tex += [r"\hline", r"\end{tabular}"]
    TABLES.mkdir(exist_ok=True)
    (TABLES / "advay_heldout_metrics.tex").write_text("\n".join(tex) + "\n")

    manifest = {"plan": "docs/advay_scoring_plan.md", "test_sha256": sha256(test_path),
                "inputs": {str(it["path"].relative_to(ROOT)): it["sha256"] for it in items},
                "script_sha256": sha256(Path(__file__)),
                "outputs": {p.name: sha256(p) for p in sorted(OUT.iterdir()) if p.is_file()}}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(pairs, indent=2))
    print("crosscheck max abs diff vs Yash:", worst)


if __name__ == "__main__":
    main()
