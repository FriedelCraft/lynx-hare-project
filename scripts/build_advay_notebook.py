"""Builds and executes notebooks/advay_data_validation.ipynb.

Run: python scripts/build_advay_notebook.py [--no-execute]

The notebook explains and reruns Advay's work package: data checks, the least-squares
baseline (one demonstration start live; the full 240-start run is loaded from its frozen
results) and the held-out evaluation (loaded from the frozen scoring run, then
recomputed in the notebook as a check).
"""
import sys
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "notebooks" / "advay_data_validation.ipynb"

cells = []
md = lambda s: cells.append(nbf.v4.new_markdown_cell(s.strip()))
code = lambda s: cells.append(nbf.v4.new_code_cell(s.strip()))

BLUE, GREEN, ORANGE, RED = ("#e8f1fb", "#1f5fa8"), ("#e9f7ee", "#1e7a45"), ("#fff3e3", "#b8620a"), ("#fdecea", "#b03a2e")


def box(colors, title, body):
    bg, border = colors
    md(f'<div style="background:{bg}; border-left:6px solid {border}; padding:12px 16px; '
       f'border-radius:6px; color:#1a1a1a;">\n\n<b style="color:{border}; font-size:1.1em;">{title}</b>'
       f'\n\n{body.strip()}\n\n</div>')


md("""
<div style="background:linear-gradient(90deg,#1f5fa8,#1e7a45); padding:18px 22px; border-radius:8px; color:white;">
<h1 style="color:white; margin:0;">Data, Least-Squares Baseline and Validation</h1>
<p style="margin:6px 0 0 0;">MAC F314 Mathematical Modelling &middot; Canadian lynx&ndash;snowshoe hare &middot; Owner: Advay</p>
</div>
""")

box(BLUE, "What this notebook does", r"""
1. **Data.** Loads the Hudson's Bay Company pelt counts (1900–1920), checks them and explains what they mean.
2. **Least squares.** Fits the shared Rosenzweig–MacArthur model to 1900–1915 by bounded nonlinear least squares.
3. **Validation.** Scores frozen forecasts from least squares and Yash's PINN on the held-out years 1916–1920.

Every choice that could be influenced by the held-out years was committed to git **before** those years were opened:
`docs/advay_baseline_protocol.md` and `docs/advay_scoring_plan.md`.
""")

code("""
import json, csv, sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import Image, display

ROOT = Path.cwd() if (Path.cwd() / "src").exists() else Path.cwd().parent
sys.path.insert(0, str(ROOT / "src"))
from lynx_hare.data import read_training
from lynx_hare.model import Parameters, solve
from lynx_hare import historical_ls as hls, stability as st

DATA, RES = ROOT / "data" / "historical", ROOT / "results" / "historical"
config = json.loads((ROOT / "configs" / "historical.json").read_text())
print("Project root:", ROOT)
""")

md("## 1. The data")
box(GREEN, "Source and meaning", r"""
Annual **thousands of pelts traded** by the Hudson's Bay Company, from the Stan case study (Carpenter, 2018). They are trade counts, **not censuses**.

**Assumption O1:** pelts are proportional to abundance, with unknown constant factors. The model states $H,P$ are defined directly in pelt units:

$$Y_{H,i} = H(t_i) + \varepsilon_{H,i}, \qquad Y_{P,i} = P(t_i) + \varepsilon_{P,i}, \qquad t_i = \text{Year}_i - 1900.$$

So $K,b,a,e$ are *effective* coefficients in pelt units. Only $r$, $m$ and the dimensionless groups have a biological reading.
""")

code("""
split = json.loads((DATA / "split.json").read_text())
train = read_training(DATA / split["train"]["file"], 1900, 1915)   # only the training file
print("Training rows:", len(train.years), " years", int(train.years[0]), "-", int(train.years[-1]))
print("Scale (training maxima):", train.scale, "  initial state:", train.initial_state)
print("Train file sha256 matches split record:",
      __import__("hashlib").sha256((DATA / split["train"]["file"]).read_bytes()).hexdigest() == split["train"]["sha256"])
""")

md("### Checks on the training years (from `scripts/advay_data_checks.py`)")
code("""
checks = json.loads((RES / "data_checks" / "summary.json").read_text())
t = checks["training"]
print("Integrity:", checks["integrity"])
print("Hare peaks:", t["hare_peaks"], " Lynx peaks:", t["lynx_peaks"])
print("Best lag (lynx after hare):", t["best_lag_years"], "years, r =", t["cross_correlation"][str(t["best_lag_years"])])
print("Outliers flagged:", t["outliers_hare"]["flagged"], t["outliers_lynx"]["flagged"])
display(Image(str(RES / "data_checks" / "figures" / "advay_raw_series.png"), width=900))
""")

box(ORANGE, "Two compilations disagree", r"""
The tsibbledata `pelt` series covers the same records but differs year by year (hare correlation 0.32). All results are conditional on the Stan series.
""")
code("""display(Image(str(RES / "data_checks" / "figures" / "advay_source_comparison.png"), width=900))""")

md("## 2. Least-squares baseline")
box(BLUE, "The fitting problem", r"""
With $\\theta=(r,K,a,b,e,m)$, solve

$$\\dot H = rH\\Big(1-\\frac{H}{K}\\Big) - \\frac{aHP}{b+H}, \\qquad \\dot P = \\frac{eaHP}{b+H} - mP$$

from the observed 1900 state with RK45 (rtol $10^{-8}$, atol $10^{-10}$, max step 0.1 yr), and minimise

$$C(\\theta) = \\tfrac12 \\sum_{i=1900}^{1915} \\Big[\\Big(\\tfrac{\\hat H_i - Y_{H,i}}{77.4}\\Big)^2 + \\Big(\\tfrac{\\hat P_i - Y_{P,i}}{59.4}\\Big)^2\\Big]$$

within the shared bounds in `configs/historical.json`.

**Algorithm**
1. Work in $x = \\log\\theta$, because the bounds span up to 600-fold.
2. From each start, run SciPy's bounded trust-region reflective least squares.
3. Use 80 starts per variant: the config guess, 39 Latin-hypercube points uniform in $\\log\\theta$, and 39 uniform in $\\theta$.
4. Keep the lowest training cost.

The two sensitivity variants change one assumption each: log residuals; or fitted $(H_0,P_0)$.
""")

md("### Two starts, live: why many starts are needed (the full 240-start run takes about 20 minutes and is loaded below)")
code("""
problem = hls.Problem(train, config, "main")
settings = {"diff_step": 1e-4, "max_nfev": 2000, "ftol": 1e-10, "xtol": 1e-10, "gtol": 1e-10}
starts = hls.starting_points(problem, 40, 20261027 + 100, "linear")   # v2's ordinary-scale starts (main variant)
for i in (2, 29):
    fit = hls.fit_start(problem, starts[i], settings)
    print(f"start {i:2d}: training cost {fit.cost:.4f}  ",
          {k: round(v, 3) for k, v in problem.unpack(fit.x)[0].to_dict().items()})
print("Start 29 stops in a local minimum about 9x worse than start 2, which reaches the best fit.")
""")

code("""
sel = json.loads((RES / "advay_baseline_v2" / "selected.json").read_text())
rows = []
for v, s in sel.items():
    p = s["parameters"]
    rows.append([v, round(s["cost"], 4), *[round(p[k], 3) for k in ("r", "K", "a", "b", "e", "m")],
                 round(s["sigma"], 3), s["regime"], f'{s["starts_near_best"]}/{s["starts_ok"]}', s["at_bound"]])
print(f'{"variant":15s} {"cost":>7s} {"r":>6s} {"K":>7s} {"a":>6s} {"b":>6s} {"e":>6s} {"m":>6s} {"sigma":>6s}  regime  near-best  at bound')
for r in rows:
    print(f"{r[0]:15s} {r[1]:7.4f} {r[2]:6.3f} {r[3]:7.1f} {r[4]:6.2f} {r[5]:6.1f} {r[6]:6.3f} {r[7]:6.3f} {r[8]:6.3f}  {r[9]}  {r[10]}  {r[11]}")
display(Image(str(RES / "advay_baseline_v2" / "figures" / "advay_baseline_fit.png"), width=800))
""")

box(RED, "What the fit can and cannot tell us", r"""
- **Well defined.** Every start within 1% of the best cost found the same parameters, and Yash's independent least-squares code reaches the same optimum.
- **Saturation not identified.** $b$ hits its upper bound (300 ≫ max hare 77.4), so $aH/(b+H)\\approx (a/b)H$. Only $a/b$ is well determined.
- **Cycle vs damped is undecided.** $\\sigma = K/K_H$ is 1.07, 0.99 or 0.55 depending on the observation assumption, yet all three fit the peak timing.
""")
code("""
ident = sel["main"]["identifiability"]
print("Approx. log-parameter standard errors:", {k: round(v, 2) for k, v in ident["approx_log_parameter_se"].items()})
print("Strongest correlations:", [(c["pair"], round(c["abs_corr"], 3)) for c in ident["strongest_correlations"][:3]])
display(Image(str(RES / "advay_baseline_v2" / "figures" / "advay_baseline_sigma.png"), width=900))
""")

md("## 3. Held-out evaluation, 1916–1920")
box(BLUE, "Scoring rules (declared before opening the test file)", r"""
- RMSE and MAE for **each species separately**, in thousands of pelts.
- A method is called **better** only if both of its errors are smaller **and** it is closer in at least 3 of the 5 years; otherwise **similar**.
- Reference forecasts, built from training data only: hold the 1915 value; use the training mean.
""")

code("""
metrics = list(csv.DictReader(open(RES / "advay_evaluation_v1" / "metrics.csv")))
comparison = json.loads((RES / "advay_evaluation_v1" / "comparison.json").read_text())
show = [("LS-Advay", "main"), ("PINN", "main_seed17"), ("Persistence (1915 value)", "-"), ("Training mean", "-")]
for m in metrics:
    if (m["label"], m["run"] if m["label"] == "PINN" else m["variant"]) in show or (m["label"] == "LS-Advay" and m["variant"] == "main"):
        if m["label"] == "PINN" and m["run"] != "main_seed17":
            continue
        print(f'{m["label"]:26s} hare RMSE {float(m["hare_rmse"]):6.2f} MAE {float(m["hare_mae"]):6.2f} | '
              f'lynx RMSE {float(m["lynx_rmse"]):6.2f} MAE {float(m["lynx_mae"]):6.2f}')
for v, c in comparison.items():
    print(f'{v:15s} ({c["status"]}): hare {c["hare_verdict"]}, lynx {c["lynx_verdict"]}')
""")

md("### Independent recomputation in this notebook")
code("""
test = np.array([[float(x) for x in r.values()] for r in csv.DictReader(open(DATA / "test_1916_1920.csv"))])
def score(path):
    f = np.array([[float(x) for x in r.values()] for r in csv.DictReader(open(path))])
    d = f[:, 1:] - test[:, 1:]
    return np.sqrt((d**2).mean(0)), np.abs(d).mean(0)
for name, path in [("Least squares, main", RES / "advay_baseline_v2" / "forecast_main.csv"),
                   ("PINN, main seed 17", RES / "yash_pinn_v1" / "runs" / "main_seed17" / "forecast.csv")]:
    rmse, mae = score(path)
    print(f"{name:22s} RMSE hare {rmse[0]:.3f} lynx {rmse[1]:.3f} | MAE hare {mae[0]:.3f} lynx {mae[1]:.3f}")
display(Image(str(RES / "advay_evaluation_v1" / "figures" / "advay_heldout_overlay.png"), width=850))
display(Image(str(RES / "advay_evaluation_v1" / "figures" / "advay_heldout_metrics.png"), width=900))
""")

box(GREEN, "Conclusions", r"""
- **Both methods forecast the 1916–1920 crash and recovery** to within about 3–4 thousand pelts. Holding the 1915 value gives lynx RMSE 37.
- **Headline:** hare similar; lynx better with least squares (closer in all 5 years).
- **Why they differ:** the PINN's parameters fit the training years 1.9–3.4× worse than the least-squares optimum, and they cycle more strongly (σ ≈ 1.35).
- **Five test points** cannot establish a winner, or whether the real system has a limit cycle.
""")
box(ORANGE, "Limitations", r"""
- A 5-point test window starting at the 1915 lynx peak.
- Trade counts rather than censuses, with constant catchability assumed.
- Two source compilations disagree.
- The 1900 observation is treated as exact in the main analysis.
- K, a and b are not identifiable, and b sits on its bound.
- Results are sensitive to the error model.
- The model is a closed two-species system with constant parameters.
""")

nb = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}})

if __name__ == "__main__":
    NB.parent.mkdir(exist_ok=True)
    if "--no-execute" not in sys.argv:
        from nbclient import NotebookClient
        NotebookClient(nb, timeout=600, kernel_name="python3", resources={"metadata": {"path": str(NB.parent)}}).execute()
    nbf.write(nb, NB)
    print("Wrote", NB)
