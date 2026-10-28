"""Build figures, Yash's historical report source and an executable evidence notebook."""
import csv
import json
import re
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lynx_hare.experiments import sha256

BASE = ROOT / "results/historical"
PRIMARY = BASE / "yash_pinn_v1"
WIDE = BASE / "yash_pinn_wider_v1"
PHYSICS = BASE / "yash_pinn_physics100_v1"
BASELINE = BASE / "yash_matching_baseline_v2"
EVAL = BASE / "yash_evaluation_v1"
FIG = EVAL / "figures"


def table(path):
    return np.genfromtxt(path, delimiter=",", names=True)


def selected(folder, variant="main"):
    run_id = json.loads((folder / "selected_runs.json").read_text())[variant]["run_id"]
    return folder / "runs" / run_id


def save(name):
    FIG.mkdir(exist_ok=True)
    for ext in ("png", "eps", "pdf"):
        plt.savefig(FIG / f"{name}.{ext}", bbox_inches="tight", dpi=160)
    for ext in ("eps", "pdf"):
        (ROOT / "report/graphs" / f"{name}.{ext}").write_bytes((FIG / f"{name}.{ext}").read_bytes())
    plt.close()


def figures():
    plt.rcParams.update({"font.size": 10, "axes.grid": True, "grid.alpha": 1,
                         "grid.color": "#eeeeee", "legend.framealpha": 1})
    train = table(ROOT / "data/historical/train_1900_1915.csv")
    test = table(ROOT / "data/historical/test_1916_1920.csv")  # frozen evaluation has already run
    folder = selected(PRIMARY)
    ode, network = table(folder / "ode_dense.csv"), table(folder / "network_train.csv")
    baseline = table(BASELINE / "ode_main.csv")
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.3))
    for ax, name in zip(axes, ("Hare", "Lynx")):
        ax.plot(ode["Year"][ode["Year"] <= 1915], ode[name][ode["Year"] <= 1915], label="PINN-derived ODE", color="#215e9c")
        ax.plot(network["Year"], network[name], "--", label="PINN network", color="#cc7722")
        ax.plot(baseline["Year"][baseline["Year"] <= 1915], baseline[name][baseline["Year"] <= 1915], ":", label="Least-squares ODE", color="#5b387e")
        ax.plot(train["Year"], train[name], "ko", ms=3, label="Training observations")
        ax.set(xlabel="Year", ylabel="Thousands of pelts", title=name)
    axes[0].legend(fontsize=8)
    fig.tight_layout(); save("yash_historical_fit")
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.3))
    for ax, name in zip(axes, ("Hare", "Lynx")):
        ax.axvspan(1915.5, 1920.1, color="#f1f1f1")
        for path in sorted((PRIMARY / "runs").glob("main_seed*/ode_dense.csv")):
            d = table(path)
            keep = d["Year"] >= 1913
            ax.plot(d["Year"][keep], d[name][keep], color="#a4b9cf", lw=1)
        keep = ode["Year"] >= 1913
        ax.plot(ode["Year"][keep], ode[name][keep], color="#215e9c", lw=2, label="Selected PINN-derived ODE")
        ax.plot(baseline["Year"][keep], baseline[name][keep], "--", color="#5b387e", label="Selected least squares")
        ax.plot(train["Year"][-3:], train[name][-3:], "ko", ms=3, label="Train")
        ax.plot(test["Year"], test[name], "ks", mfc="white", ms=4, label="Held out")
        ax.set(xlabel="Year", ylabel="Thousands of pelts", title=name, xlim=(1913, 1920.1))
    axes[0].legend(fontsize=7)
    fig.tight_layout(); save("yash_historical_forecast")
    h = table(folder / "training.csv")
    fig, ax = plt.subplots(figsize=(9, 3.3))
    for field, factor, label in (("total", 1, "Total"), ("data", 1, "Data"), ("physics", 10, "10 x physics"), ("ic", 10, "10 x IC")):
        ax.semilogy(h["step"], np.maximum(h[field]*factor, 1e-15), label=label)
    ax.axvline(5000, color="grey", ls=":", label="Adam / L-BFGS")
    ax.set(xlabel="Optimization step (L-BFGS uses closure evaluations)", ylabel="Weighted loss", title="Selected primary run: training losses")
    ax.legend(ncol=4, fontsize=8)
    fig.tight_layout(); save("yash_historical_loss")
    config = json.loads((PRIMARY / "config.json").read_text())
    wide_config = json.loads((WIDE / "config.json").read_text())
    fig, axes = plt.subplots(2, 3, figsize=(10, 5))
    for ax, name in zip(axes.ravel(), ("r", "K", "a", "b", "e", "m")):
        for i, (root, label, color) in enumerate(((PRIMARY, "Primary", "#215e9c"), (WIDE, "Wider box", "#cc7722"))):
            values = [json.loads(p.read_text())["parameters"][name] for p in sorted((root / "runs").glob("main_seed*/summary.json"))]
            ax.plot(np.full(len(values), i) + np.linspace(-0.06, 0.06, len(values)), values, "o", color=color)
        ax.axhline(config["bounds"][name][1], ls=":", color="#215e9c", lw=1)
        ax.axhline(wide_config["bounds"][name][1], ls=":", color="#cc7722", lw=1)
        ax.set(xticks=[0, 1], xticklabels=["Primary", "Wider box"], title=name)
    fig.suptitle("All main seeds; dotted lines mark upper bounds", y=1.01)
    fig.tight_layout(); save("yash_historical_bounds")
    cases = [(PRIMARY, "main", "Primary"), (PRIMARY, "log_errors", "Log errors"),
             (PRIMARY, "fitted_initial", "Fitted IC"), (WIDE, "main", "Wider bounds"),
             (PHYSICS, "main", "Physics weight 100")]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.5))
    for ax, name in zip(axes, ("Hare", "Lynx")):
        ax.axvspan(1915.5, 1920.1, color="#f1f1f1")
        for root, variant, label in cases:
            d = table(selected(root, variant) / "ode_dense.csv")
            ax.plot(d["Year"], d[name], label=label, lw=1.2)
        ax.plot(train["Year"], train[name], "ko", ms=2)
        ax.plot(test["Year"], test[name], "ks", mfc="white", ms=3)
        ax.set(xlabel="Year", ylabel="Thousands of pelts", title=name)
        ax.set_xticks(np.arange(1900, 1921, 5))
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=8, bbox_to_anchor=(0.5, -0.07))
    fig.tight_layout(); save("yash_historical_sensitivity")


def report():
    with (EVAL / "heldout_metrics.csv").open() as f:
        rows = list(csv.DictReader(f))
    selected_rows = [r for r in rows if r["selected"] == "True"]
    summary = json.loads((selected(PRIMARY) / "summary.json").read_text())
    params = summary["parameters"]
    metric_lines = []
    labels = {("primary", "main"): "PINN primary", ("primary", "log_errors"): "PINN log errors",
              ("primary", "fitted_initial"): "PINN fitted IC", ("wider_bounds", "main"): "PINN wider bounds",
              ("physics100", "main"): "PINN physics 100", ("baseline", "main"): "LS primary",
              ("baseline", "log_errors"): "LS log errors", ("baseline", "fitted_initial"): "LS fitted IC"}
    for row in selected_rows:
        label = labels[(row["case"], row["variant"])]
        metric_lines.append(label + " & " + " & ".join(f"{float(row[k]):.3f}" for k in ("hare_rmse", "lynx_rmse", "hare_mae", "lynx_mae")) + r" \\")
    bounds = json.loads((PRIMARY / "config.json").read_text())["bounds"]
    parameter_lines = [f"${name}$ & {bounds[name][0]:g}--{bounds[name][1]:g} & {params[name]:.5g}" + r" \\" for name in ("r", "K", "a", "b", "e", "m")]
    source = r"""\section{Historical inverse PINN study}
This is Yash's contribution, using the historical pelt series supplied by Advay. It
extends the separately preserved synthetic recovery experiment; its individual scope is retained alongside the combined group deliverables. The Stan compilation contains annual Hudson's Bay Company
hare and lynx pelt returns \cite{carpenter2018}. We train on 1900--1915 (16 pairs) and
evaluate once on frozen forecasts for 1916--1920 (five pairs). Counts are thousands of
pelts, treated as abundance indices rather than censuses. Annual totals are approximated
as point samples. No observation scale factor is fitted. Alternative source compilations
disagree; all results here are conditional on the Stan series.

\subsection{Model and protocol}
With $t=\mathrm{Year}-1900$, the shared dimensional model is
\begin{align*}
\dot H&=rH(1-H/K)-aHP/(b+H), & \dot P&=eaHP/(b+H)-mP.
\end{align*}
All six positive coefficients are inferred. Bounds below are exploratory numerical
choices, not measured biological ranges. No coexistence constraint is imposed and $e$
is not constrained below one because these are effective coefficients in pelt units.
The starting vector is $(r,K,a,b,e,m)=(0.8,150,2,30,0.6,0.6)$. The shared historical configuration records this protocol and its exploratory bounds. The local least-squares
benchmark uses the identical config, data split, scaling and solver.
\begin{center}\begin{tabular}{lrr}\toprule
Coefficient & Bounds & Selected primary estimate\\\midrule
PARAMETER_ROWS
\bottomrule\end{tabular}\end{center}

\subsection{Network, loss and optimization}
The inverse PINN \cite{raissi2019} uses three hidden layers of 48 tanh units, float64,
softplus-positive normalized outputs, and sigmoid-bounded coefficients. Species scales
are training maxima $(s_H,s_P)=(77.4,59.4)$; network time is $2t/15-1$.
For $u_\theta=(H_\theta/s_H,P_\theta/s_P)$, automatic differentiation evaluates
$R_\theta=\partial_tu_\theta-f(u_\theta\odot s;p)/s$. The loss is
\[
L=\operatorname{mean}(u_\theta-y/s)^2+
10\operatorname{mean}R_\theta^2+
10\operatorname{mean}(u_\theta(0)-y_0/s)^2.
\]
The initial observation is $y_0=(30,4)$. There are 161 collocation times in $[0,15]$.
Optimization uses 500 data/IC warmup steps, up to 5000 joint Adam steps at learning rate
0.002 (gradient norm clipped at 10), then up to 600 L-BFGS iterations with strong-Wolfe
line search. Training loss is logged every 100 Adam steps; plateau stopping uses
15 checks and minimum improvement $10^{-8}$. The best recorded weighted training
objective determines the saved state. Seeds are 17, 29 and 43, with one CPU thread and
deterministic Torch operations. Each variant selects its own lowest-loss seed; objectives
from different observation models are not used to select the primary analysis.
\begin{figure}[htbp]\centering
\ReportGraphEPS[width=\linewidth]{yash_historical_fit.eps}
\caption{Training observations, learned network and re-integrated ODE. A small local
physics residual does not guarantee identical long-horizon ODE and network trajectories.}
\end{figure}

\subsection{Frozen forecasts and matched benchmark}
The selected primary seed is 17. Forecasts use the learned coefficients in the shared
RK45 solver with rtol $10^{-8}$, atol $10^{-10}$ and maximum step 0.1 year. Integration
starts from $(30,4)$ in 1900 and proceeds through 1920, with no restart from a test state.
The neural network is never extrapolated for forecasting. Its starting-state discrepancy
is $(0.10060,-0.00723)$ thousand pelts; the ODE still starts at the exact observation.
The primary ODE training normalized MSE is ODE_MSE. The matched primary least-squares
fit uses six starts (RNG seed 91), bounded \texttt{least\_squares}, up to 500 function
evaluations and ftol=xtol=gtol=$10^{-10}$. Each start and its convergence status is retained.
This independent benchmark was subsequently reproduced by Advay on the same configuration; the combined report documents the chronology. PINN and least squares differ in soft versus
exact IC enforcement and in the PINN's added physics penalty.
\begin{figure}[htbp]\centering
\ReportGraphEPS[width=\linewidth]{yash_historical_forecast.eps}
\caption{Frozen forecasts. Thin pale lines are the three primary PINN seeds, not confidence
bands. Shading marks held-out years; observations were used for scoring only after all
forecast and seed choices were frozen.}
\end{figure}
\begin{center}\small\begin{tabular}{lrrrr}\toprule
& \multicolumn{2}{c}{RMSE} & \multicolumn{2}{c}{MAE}\\
Method & Hare & Lynx & Hare & Lynx\\\midrule
METRIC_ROWS
\bottomrule\end{tabular}\end{center}
All scores are thousands of pelts on the same five held-out years. The primary PINN has
slightly lower hare RMSE than primary least squares, but higher lynx RMSE. Hare MAE is
essentially tied. These results do not establish an overall PINN advantage.
\begin{figure}[htbp]\centering
\ReportGraphEPS[width=0.95\linewidth]{yash_historical_loss.eps}
\caption{Selected primary training loss components. L-BFGS abscissae count closure
evaluations after Adam; they are not directly comparable computational steps.}
\end{figure}

\subsection{Sensitivity and practical identifiability}
All sensitivities were specified before any test scoring and are reported regardless
of outcome. The main three seeds were repeated with log observation residuals, and
separately with trainable initial states in $[0.5,1.5]$ times the 1900 observations. The
first data point stays in the data loss. The fitted-IC PINN's ODE starts at approximately
$(34.7477,3.7841)$; the network and ODE initial states are separately recorded. The benchmark
repeats both observation/IC sensitivities with six starts each. Log residuals worsen hare
forecast error for both methods, especially the PINN. None of these scores changes the
predeclared primary choice.

To check arbitrary box limits, each lower bound was halved and each upper bound doubled,
and the main PINN was repeated for all three seeds. A further seed-17 run increased physics
weight from 10 to 100. In total there are 13 PINN runs and 18 least-squares starts.
The wider-box fits move $K$ from about 498 to about 986 and $b$ from about 300 to about 600,
close to the expanded limits; $a$ also shifts substantially. Similar results across seeds
therefore do not demonstrate uniquely recovered biological parameters. The wider-box
forecast changes are smaller than these coefficient shifts.
\begin{figure}[htbp]\centering
\ReportGraphEPS[width=\linewidth]{yash_historical_bounds.eps}
\caption{Primary versus wider-box parameter estimates over three seeds. Several effective
coefficients track the numerical bounds; narrow seed spread is not parameter certainty.}
\end{figure}
\begin{figure}[htbp]\centering
\ReportGraphEPS[width=\linewidth]{yash_historical_sensitivity.eps}
\caption{All selected PINN variants. The log-error fit shows appreciable model/ODE forecast
sensitivity. Variants were retained rather than chosen using held-out errors.}
\end{figure}

\clearpage
The local trajectory sensitivity matrix uses central differences with respect to log
parameters (step $10^{-4}$), normalized using the declared observation loss. Its selected
primary condition number is approximately CONDITION. This is a local diagnostic, not
a proof of structural identifiability or a confidence interval. For feasible coexistence,
$H^*=mb/(ea-m)$, $K_H=b+2H^*$ and $\sigma=K/K_H$; the selected primary fit gives
$\sigma=SIGMA$. This fitted ODE lies on the cycling side of Joel's threshold, conditional
on the model and protocol. It does not prove that the historical ecological system has
a stable limit cycle. All seeds' values and feasibility flags are exported to the team.

\subsection{Reproducibility and limitations}
\path{configs/historical.json} records every primary choice; the two sensitivity
configs record the expanded box and physics weight. Run manifests hash sources, config,
training data, forecasts and diagnostics. A forecast-freeze record is written before the
test observations are read. \path{scripts/run_historical_pinn.py} accepts only the
training table; \path{scripts/score_historical.py} handles final scoring. Existing
synthetic recovery results are preserved as a separate controlled validation.

Six effective coefficients are fitted from roughly two noisy cycles; boundary hits,
source disagreement, annual season totals, unknown catchability and the small test window
limit interpretation. PINN physics is a soft constraint, and the log-loss variant exposes
an appreciable network/ODE discrepancy. Seed spread is optimization sensitivity only.
Forecast skill on five points cannot establish general superiority, causal mechanisms
or absolute animal populations. This report and notebook concern Yash's component; the accompanying combined notebook and report integrate all five contributions.
"""
    source = source.replace("PARAMETER_ROWS", "\n".join(parameter_lines)).replace("METRIC_ROWS", "\n".join(metric_lines))
    source = source.replace("ODE_MSE", f"{summary['training_ode_normalized_mse']:.5f}")
    source = source.replace("CONDITION", f"{summary['diagnostics']['condition_number']:.1f}").replace("SIGMA", f"{summary['diagnostics']['sigma']:.3f}")
    (ROOT / "report/yash_historical_section.tex").write_text(source, encoding="utf-8")
    preamble = (ROOT / "report/main.tex").read_text().split(r"\title{")[0]
    main = preamble + r"""\title{Historical Inverse PINN Study of Lynx and Hare Pelt Dynamics}
\author{Yash}\date{27 October 2026}
\begin{document}\maketitle
\input{yash_historical_section}
\bibliographystyle{plain}\bibliography{references}
\end{document}
"""
    (ROOT / "report/yash_historical_main.tex").write_text(main, encoding="utf-8")


def notebook():
    cells = []
    md = lambda s: cells.append(nbf.v4.new_markdown_cell(s.strip()))
    code = lambda s: cells.append(nbf.v4.new_code_cell(s.strip()))
    md("""# Yash: historical inverse PINN study
Real Hudson's Bay Company pelt indices from Advay's Stan compilation, **not synthetic data**.
Training: 1900-1915. Frozen evaluation: 1916-1920. Counts are thousands of pelts, not animal censuses.

This notebook includes the complete model and inverse-PINN training implementations, explains the protocol,
and independently reconstructs the saved forecasts. Default execution audits and displays completed runs;
it does **not** pretend to retrain them. Reproduction commands below create new output directories.
The old synthetic notebook remains the separate controlled recovery study.
""")
    code("""import sys, json, hashlib, csv
from pathlib import Path
import numpy as np
import torch
from IPython.display import display, Image, HTML
from html import escape
def show_table(rows):
    names=list(rows[0])
    header='<tr>'+''.join('<th>'+escape(str(n))+'</th>' for n in names)+'</tr>'
    body=''.join('<tr>'+''.join('<td>'+escape(str(row[n]))+'</td>' for n in names)+'</tr>' for row in rows)
    display(HTML('<table>'+header+body+'</table>'))
ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
assert (ROOT / 'src/lynx_hare/model.py').exists(), 'Run in the repository root or notebooks/'
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
BASE = ROOT / 'results/historical'
config = json.loads((ROOT / 'configs/historical.json').read_text())
show_table([{'parameter':n,'initial_guess':config['initial_guess'][n],'bounds':config['bounds'][n]} for n in config['initial_guess']])
""")
    md("""## Complete scientific implementation
The following executable cells mirror the canonical modules. Relative imports are rewritten to their
package names so the cells run in Jupyter. The packaged modules and runner remain the canonical route
for batch reproduction; all source hashes are recorded in the notebook metadata and run manifests.

The model uses logistic hare growth and Holling-II predation. The data contract validates positive,
ordered observations and computes scales from training rows only. Positive states, bounded parameters,
automatic-differentiation residuals, deterministic Adam/L-BFGS training and optional fitted initial
states are implemented below. No generating truth enters historical fitting.
""")
    hashes = {}
    for name in ("model.py", "data.py", "pinn.py", "historical_pinn.py"):
        path = ROOT / "src/lynx_hare" / name
        hashes[name] = sha256(path)
        source = path.read_text()
        source = re.sub(r"^from \.model import", "from lynx_hare.model import", source, flags=re.M)
        source = re.sub(r"^from \.pinn import", "from lynx_hare.pinn import", source, flags=re.M)
        code(f"# Complete implementation: src/lynx_hare/{name}\n" + source)
    md("""## Frozen data and loss
The primary residual is `(prediction-observation)/training_max`, with one equal contribution per species.
The physics residual differentiates normalized states with respect to physical time, retaining both time
and state scaling. Weights are data=1, physics=10, IC=10. The network has 3 x 48 tanh units; outputs use
softplus and all six parameters use positive sigmoid bounds. The primary ODE initial state is (30,4).
The PINN's initial-state constraint is soft, and its discrepancy is explicitly reported.

Seeds 17,29,43 are selected by weighted **training** loss within each variant. Log errors and fitted
initial states are separate declared sensitivities. Wider bounds and physics weight 100 are retained
as sensitivity results, not promoted after scoring. The local benchmark uses the exact same primary
config; it is an independent check, not a claim that Advay has completed his own fitting task.
""")
    code("""from run_historical_pinn import training_split
data, train_path = training_split(ROOT)
validate_config(config)
assert data.years.tolist() == list(range(1900,1916))
show_table([{'species':n,'scale':float(data.scale[i]),'observed_initial':float(data.initial_state[i])} for i,n in enumerate(['Hare','Lynx'])])
from score_historical import frozen
for folder in ['yash_pinn_v1','yash_pinn_wider_v1','yash_pinn_physics100_v1','yash_matching_baseline_v2']:
    assert frozen(BASE/folder)['status'] == 'forecasts_frozen_unscored'
print('All frozen output and scientific-source hashes verified.')
""")
    md("""## Independent ODE reconstruction and seed diagnostics
Forecasts use RK45 from 1900 through 1920 with the learned parameters, never neural-network extrapolation.
The code below reconstructs every saved five-year forecast without reading held-out observations.
Local sensitivity condition numbers describe this fitted model only; seed spread is not a confidence interval.
""")
    code("""from lynx_hare.model import Parameters as ModelParameters, solve as solve_model
summaries=[]
for dirname in ['yash_pinn_v1','yash_pinn_wider_v1','yash_pinn_physics100_v1']:
    for path in sorted((BASE/dirname/'runs').glob('*/summary.json')):
        s=json.loads(path.read_text())
        predicted=solve_model(np.arange(21), s['audit']['ode_initial'], ModelParameters(**s['parameters']), **config['solver'])
        exported=np.loadtxt(path.parent/'forecast.csv',delimiter=',',skiprows=1)
        np.testing.assert_allclose(predicted[16:],exported[:,1:],rtol=1e-11,atol=1e-11)
        summaries.append({'case':dirname,'run':s['run_id'],**s['parameters'],
                          'sigma':s['diagnostics']['sigma'],'condition':s['diagnostics']['condition_number'],
                          'ODE_training_MSE':s['training_ode_normalized_mse'],
                          'IC_difference':s['audit']['network_minus_observed_initial']})
show_table(summaries)
print('All 13 PINN forecast files independently reconstructed.')
""")
    md("""## Final evaluation and figures
All model choices and forecasts were frozen before evaluation. Scores are RMSE and MAE for each species
in original pelt units, on the same five test years. Primary hare RMSE is slightly better for the PINN,
while primary lynx RMSE is worse. The table contains **all** declared sensitivity outcomes.
No method or variant is selected using this table. Boundary sensitivity prevents claims of uniquely
identified biological coefficients; a fitted sigma above one describes the fitted ODE, not proof of a
real ecological limit cycle. The report discusses the small test sample, source differences and soft-physics mismatch.
""")
    code("""with (BASE/'yash_evaluation_v1/heldout_metrics.csv').open() as f:
    scores=list(csv.DictReader(f))
show_table([{k:r[k] for k in ['case','variant','hare_rmse','lynx_rmse','hare_mae','lynx_mae']} for r in scores if r['selected']=='True'])
receipt=json.loads((BASE/'yash_evaluation_v1/receipt.json').read_text())
assert receipt['test_used_for_model_choices'] is False
assert hashlib.sha256((BASE/'yash_evaluation_v1/heldout_metrics.csv').read_bytes()).hexdigest() == receipt['metrics_sha256']
for stem in ['fit','forecast','loss','bounds','sensitivity']:
    display(Image(filename=str(BASE/f'yash_evaluation_v1/figures/yash_historical_{stem}.png')))
""")
    md("""## Batch reproduction
The source modules above contain the complete neural training algorithm. The runner saves each seed's
training history, parameters, initial states, ODE forecasts, network states, residuals and hashes. The
following commands deliberately use **new** directories. Match the runner/scorer directory constants
for a separate reproduction; never overwrite or retune the existing scored iteration.

```text
python scripts/run_historical_pinn.py --config configs/historical.json --output results/historical/reproduction_primary
python scripts/run_historical_pinn.py --config configs/historical_wider_bounds.json --output results/historical/reproduction_wide
python scripts/run_historical_pinn.py --config configs/historical_physics100.json --output results/historical/reproduction_physics100
python scripts/fit_historical_baseline.py --config configs/historical.json --output results/historical/reproduction_baseline
```

Full export, independent baseline, scoring and figure/report-building programs are in `scripts/` in
the same package. `docs/yash_historical_handoff.md` describes the team handoff and interpretation.
The complete dataset, original raw copies and provenance are under `data/historical/`.
""")
    nb = nbf.v4.new_notebook(cells=cells)
    nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nb.metadata["embedded_source_sha256"] = hashes
    nbf.write(nb, ROOT / "notebooks/yash_historical_pinn.ipynb")


if __name__ == "__main__":
    if not (EVAL / "receipt.json").exists():
        raise ValueError("Score frozen forecasts before displaying test observations")
    figures()
    report()
    notebook()
    print("Built historical figures, LaTeX source and notebook")
