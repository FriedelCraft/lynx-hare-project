"""Advay, phase 1 step 2: raw plots and quality checks for the historical pelt data.

Every number that could feed a modelling decision (scales, lag, outlier thresholds)
is computed from the 1900-1915 training rows only. The 1916-1920 rows appear in the
plots, shaded and labelled, but are never used to compute a statistic.
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
DATA = ROOT / "data" / "historical"
OUT = ROOT / "results" / "historical" / "data_checks"
GRAPHS = ROOT / "report" / "graphs"
TRAIN_END = 1915

HARE, LYNX, GREY, TEST_FILL = "#1f5fa8", "#c0392b", "#777777", "#eeeeee"
STYLE = {"font.size": 11, "axes.grid": True, "axes.axisbelow": True, "grid.color": "#dddddd",
         "legend.framealpha": 1.0, "savefig.bbox": "tight"}


def load(path):
    rows = [r for r in open(path) if not r.startswith("#")]
    reader = csv.DictReader([r.replace(" ", "") for r in rows])
    table = [(int(r["Year"]), float(r["Hare"]), float(r["Lynx"])) for r in reader]
    return np.array(table)


def save(fig, stem):
    for folder, exts in ((OUT / "figures", ("png", "eps", "pdf")), (GRAPHS, ("eps", "pdf"))):
        folder.mkdir(parents=True, exist_ok=True)
        for ext in exts:
            fig.savefig(folder / f"{stem}.{ext}", dpi=200 if ext == "png" else None)
    plt.close(fig)


def integrity(d):
    years = d[:, 0].astype(int)
    return {
        "n_rows": len(d),
        "years": [int(years[0]), int(years[-1])],
        "consecutive_years": bool(np.all(np.diff(years) == 1)),
        "duplicate_years": int(len(years) - len(set(years))),
        "missing_values": int(np.isnan(d[:, 1:]).sum()),
        "nonpositive_values": int((d[:, 1:] <= 0).sum()),
    }


def local_peaks(years, x, prominence):
    """Interior local maxima that exceed both neighbours and stand `prominence` above
    the lower of the two nearest troughs (filters one-year wiggles)."""
    peaks = []
    for i in range(1, len(x) - 1):
        if x[i] > x[i - 1] and x[i] >= x[i + 1]:
            left, right = x[: i + 1].min(), x[i:].min()
            if x[i] - max(left, right) >= prominence * x.max():
                peaks.append(int(years[i]))
    return peaks


def outliers(years, x, threshold=3.5):
    """Robust z-scores of year-to-year log growth rates (median/MAD). Large cyclic
    swings are expected, so only extreme jumps relative to the series' own typical
    growth are flagged."""
    g = np.diff(np.log(x))
    med = np.median(g)
    mad = np.median(np.abs(g - med)) * 1.4826
    z = (g - med) / mad
    flagged = [{"from": int(years[i]), "to": int(years[i + 1]),
                "log_growth": round(float(g[i]), 3), "robust_z": round(float(z[i]), 2)}
               for i in np.flatnonzero(np.abs(z) > threshold)]
    return {"max_abs_robust_z": round(float(np.abs(z).max()), 2),
            "threshold": threshold, "flagged": flagged,
            "growth_range": [round(float(g.min()), 3), round(float(g.max()), 3)]}


def cross_correlation(h, p, max_lag=4):
    """corr(H_t, P_{t+k}); positive k with the peak means lynx lags hare by k years."""
    out = {}
    for k in range(-max_lag, max_lag + 1):
        a, b = (h[: len(h) - k], p[k:]) if k >= 0 else (h[-k:], p[: len(p) + k])
        out[k] = float(np.corrcoef(a, b)[0, 1])
    return out


def summary_stats(x):
    return {"min": float(x.min()), "max": float(x.max()), "mean": round(float(x.mean()), 2),
            "max_over_min": round(float(x.max() / x.min()), 2),
            "coefficient_of_variation": round(float(x.std(ddof=1) / x.mean()), 3)}


def fig_series(d):
    years, h, p = d.T
    train = years <= TRAIN_END
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.3), gridspec_kw={"width_ratios": [1.6, 1]})
    a = ax[0]
    a.axvspan(TRAIN_END + 0.5, years[-1] + 0.5, color=TEST_FILL, zorder=0)
    a.text(TRAIN_END + 0.8, 80, "held out\n1916–1920", color=GREY, va="top", fontsize=10)
    a.plot(years, h, "-o", color=HARE, lw=2, ms=5, label="Hare")
    a.plot(years, p, "-s", color=LYNX, lw=2, ms=5, label="Lynx")
    a.set(xlabel="Year", ylabel="Pelts traded (thousands)", ylim=(0, 85),
          xlim=(years[0] - 0.5, years[-1] + 0.5), title="Hudson's Bay Company pelt counts")
    a.set_xticks(np.arange(1900, 1921, 2))
    a.legend(loc="upper left", bbox_to_anchor=(0.27, 1.0))
    b = ax[1]
    b.plot(h[~train | (years == TRAIN_END)], p[~train | (years == TRAIN_END)], "--o",
           color=GREY, mfc="white", lw=1.2, ms=5, label="1916–1920 (held out)")
    b.plot(h[train], p[train], "-o", color="#333333", lw=1.5, ms=5, label="1900–1915 (train)")
    for y in (1900, 1903, 1904, 1910, 1913, 1915, 1920):
        i = int(y - years[0])
        b.annotate(str(y), (h[i], p[i]), textcoords="offset points", xytext=(6, 4), fontsize=9)
    b.set(xlabel="Hare (thousands of pelts)", ylabel="Lynx (thousands of pelts)",
          title="Phase plane: counter-clockwise loops")
    b.set_ylim(0, 72)
    handles, labels = b.get_legend_handles_labels()
    b.legend(handles[::-1], labels[::-1], loc="upper right", fontsize=9)
    fig.tight_layout()
    save(fig, "advay_raw_series")


def fig_lag(xc, best):
    lags = np.array(sorted(xc))
    vals = np.array([xc[k] for k in lags])
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    colors = [LYNX if k == best else "#9aa7b8" for k in lags]
    ax.bar(lags, vals, width=0.6, color=colors, edgecolor="white", linewidth=2)
    ax.axhline(0, color="#444444", lw=1)
    ax.text(lags[0] - 0.3, 0.85, f"peak r = {xc[best]:.2f} at lag {best} yr", fontsize=10)
    ax.set(xlabel="Lag k (years): correlation of Hare(t) with Lynx(t + k)",
           ylabel="Pearson r", ylim=(-1, 1), title="Lynx lags hare (training years 1900–1915)")
    ax.set_xticks(lags)
    fig.tight_layout()
    save(fig, "advay_lag")


def fig_sources(d, alt):
    years = d[:, 0]
    alt = alt[(alt[:, 0] >= years[0]) & (alt[:, 0] <= years[-1])]
    fig, ax = plt.subplots(1, 2, figsize=(12, 3.8), sharex=True)
    for a, col, name, color in ((ax[0], 1, "Hare", HARE), (ax[1], 2, "Lynx", LYNX)):
        a.plot(years, d[:, col], "-o", color=color, lw=2, ms=5, label="Stan case study (used)")
        a.set_ylim(0, 85)
        a.plot(alt[:, 0], alt[:, col], "--s", color=GREY, mfc="white", lw=1.5, ms=5,
               label="tsibbledata pelt (cross-check)")
        r = np.corrcoef(d[:, col], alt[:, col])[0, 1]
        a.set(xlabel="Year", ylabel="Thousands of pelts", title=f"{name}: two compilations, r = {r:.2f}")
        a.set_xticks(np.arange(1900, 1921, 4))
    handles, labels = ax[0].get_legend_handles_labels()
    fig.legend(handles, ["Stan case study (used)", "tsibbledata pelt (cross-check)"],
               loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.06), frameon=False)
    fig.tight_layout()
    save(fig, "advay_source_comparison")


def main():
    plt.rcParams.update(STYLE)
    d = load(DATA / "pelts_1900_1920.csv")
    alt = load(DATA / "raw" / "tsibbledata_lynxhare.csv")
    tr = d[d[:, 0] <= TRAIN_END]
    years, h, p = tr.T

    xc = cross_correlation(h, p)
    best = max(xc, key=xc.get)
    hare_peaks = local_peaks(years, h, 0.25)
    lynx_peaks = local_peaks(years, p, 0.25)

    result = {
        "note": "All statistics use training rows 1900-1915 only, except 'integrity', "
                "which checks the whole file for format errors.",
        "integrity": integrity(d),
        "training": {
            "rows": len(tr),
            "hare": summary_stats(h), "lynx": summary_stats(p),
            "normalisation_scales": {"hare_max": float(h.max()), "lynx_max": float(p.max())},
            "hare_peaks": hare_peaks, "lynx_peaks": lynx_peaks,
            "peak_lags_years": [l - hh for hh, l in zip(hare_peaks, lynx_peaks)],
            "hare_peak_spacing_years": list(np.diff(hare_peaks).astype(int).tolist()),
            "cross_correlation": {str(k): round(v, 3) for k, v in xc.items()},
            "best_lag_years": int(best),
            "outliers_hare": outliers(years, h),
            "outliers_lynx": outliers(years, p),
        },
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "summary.json").write_text(json.dumps(result, indent=2) + "\n")

    fig_series(d)
    fig_lag(xc, best)
    fig_sources(d, alt)
    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
