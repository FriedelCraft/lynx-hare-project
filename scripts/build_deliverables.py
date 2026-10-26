"""Build measured prose, LaTeX tables and a notebook from completed experiment evidence."""
from pathlib import Path
import ast
import csv
import hashlib
import json
import shutil
import statistics
import sys
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/synthetic"


def read_csv(name):
    with (OUT / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write(path, content):
    path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def main():
    config = json.loads((ROOT / "configs/synthetic.json").read_text())
    selected = json.loads((OUT / "selected_run.json").read_text())
    runs = [json.loads(p.read_text()) for p in sorted((OUT / "runs").glob("*/summary.json"))]
    scores = read_csv("heldout_metrics.csv")
    recovery = read_csv("parameter_recovery.csv")
    spectrum = json.loads((OUT / "identifiability.json").read_text())
    total_seconds = sum(s["audit"]["elapsed_seconds"] for s in runs)
    clean_max = max(float(r["absolute_relative_error_percent"]) for r in recovery if r["case"] == "dense_clean" and r["estimated"] == "True")
    noisy_max = max(float(r["absolute_relative_error_percent"]) for r in recovery if r["case"] == "dense_noisy" and r["estimated"] == "True")
    annual_max = max(float(r["absolute_relative_error_percent"]) for r in recovery if r["case"] == "annual_noisy" and r["variant"] == "default" and r["estimated"] == "True")
    p = selected["parameters"]
    display_scores = [s for s in scores if s["selected"] == "True"]
    summary = f"""# Measured synthetic results

The complete reference run contains **{len(runs)} PINN fits** on one CPU thread.
Training took {total_seconds:.1f} seconds in total, excluding imports, baseline fitting,
plotting and notebook execution. The exact runtime versions and source hashes are in
`results/synthetic/manifest.json`. These are synthetic index trajectories, not historical data.

## Parameter recovery

All primary fits estimate r, a and m; K=60, b=20 and e=0.6 are fixed correctly for this
controlled experiment. Maximum absolute relative errors across the three default seeds
and the three estimated parameters were:

| Training observations | Maximum error |
|---|---:|
| 61 clean quarterly observations | {clean_max:.4f}% |
| 61 quarterly observations with 3% noise | {noisy_max:.3f}% |
| 16 annual observations with 3% noise | {annual_max:.3f}% |

This comparison holds the noise seed fixed within each case. It does not show that
annual observations are generally more informative than quarterly observations; the
finite noise realizations differ and the three rates are conditionally identifiable.

The selected default annual run is **{selected['run_id']}**, chosen using the smallest
weighted training objective. Its estimates are r={p['r']:.8f}, a={p['a']:.8f} and
m={p['m']:.8f}. All seeds and sensitivity variants are retained in `parameter_recovery.csv`.

## Held-out ODE forecasts

These scores use five years labelled 1916–1920. Parameters and the seed choice were
frozen before scoring. The ODE is integrated from 1900 using the same initial state and
RK45 settings for both methods. Values are in arbitrary synthetic abundance-index units.

| Method | Evaluation target | Hare RMSE | Lynx RMSE | Hare MAE | Lynx MAE |
|---|---|---:|---:|---:|---:|
"""
    for s in display_scores:
        summary += f"| {s['method']} | {s['target'].replace('_',' ')} | {float(s['hare_rmse']):.5f} | {float(s['lynx_rmse']):.5f} | {float(s['hare_mae']):.5f} | {float(s['lynx_mae']):.5f} |\n"
    summary += f"""
Against noisy observations, least squares has the lower hare error and the selected
PINN-derived ODE has the lower lynx error. Against latent truth the selected PINN-derived
ODE is closer for both species in this realization. This mixed result is not evidence
of general superiority. The experiment favors the mechanistic model because the same
equations generated the observations, three constants are known, and the initial state
is exact. No claim about historical predictive accuracy follows.

## Sensitivity and identifiability

The prespecified physics weights 1 and 100 and initial-guess factors 0.6 and 1.4 produce
the trajectories in `figures/sensitivity.png`. This is a diagnostic sweep, not a test-based
search for the best configuration. The local sensitivity condition number rises from
{spectrum['three_parameters']['condition_number']:.2f} when varying r,a,m to
{spectrum['six_parameters']['condition_number']:.2f} when all six parameters are varied
locally. That indicates more weakly constrained directions in the larger local problem;
it does not prove structural non-identifiability or establish six-parameter recovery.

The independent residual grid and network/ODE consistency figures check two failure
modes: satisfying physics only at the training grid and fitting observations with a
network whose inferred ODE follows a different trajectory. Neither diagnostic is a
formal error bound or a substitute for held-out validation.

## Practical limits

Three optimizer seeds on one noise draw do not quantify observation uncertainty. Bounds,
loss weights and fixed constants are provisional. The forecast contains only five test
points per species. The synthetic system omits ecology and the pelt-trading observation
mechanism. Real fitting requires the team's frozen equations, units, feasibility ranges,
data provenance and evaluation protocol. See `docs/team_handoff.md`.
"""
    write("docs/results_summary.md", summary)

    rows = []
    for case in ("dense_clean", "dense_noisy", "annual_noisy"):
        for name in config["trainable"]:
            values = [float(r["absolute_relative_error_percent"]) for r in recovery
                      if r["case"] == case and r["variant"] == "default" and r["parameter"] == name]
            rows.append((case.replace("_", " "), name, statistics.mean(values), max(values)))
    table = r"\begin{tabular}{llrr}" + "\n" + r"\toprule" + "\n" + r"Training case & Rate & Mean error (\%) & Max error (\%) \\" + "\n" + r"\midrule" + "\n"
    for case, name, mean, maximum in rows:
        table += f"{case} & ${name}$ & {mean:.4f} & {maximum:.4f} " + r"\\" + "\n"
    table += r"\bottomrule\end{tabular}"
    write("report/tables/recovery.tex", table)
    table = r"\begin{tabular}{llrrrr}" + "\n" + r"\toprule" + "\n" + r"Method & Target & H RMSE & P RMSE & H MAE & P MAE \\" + "\n" + r"\midrule" + "\n"
    for s in display_scores:
        method = "PINN ODE" if s["method"] == "PINN-derived ODE" else "Least squares"
        target = "Noisy" if s["target"] == "noisy_observations" else "Latent"
        table += f"{method} & {target} & {float(s['hare_rmse']):.4f} & {float(s['lynx_rmse']):.4f} & {float(s['hare_mae']):.4f} & {float(s['lynx_mae']):.4f} " + r"\\" + "\n"
    table += r"\bottomrule\end{tabular}"
    write("report/tables/metrics.tex", table)
    section = r"""
\section{Inverse inference with a physics informed neural network}
This section tests whether an inverse PINN can recover known parameters and produce
ODE forecasts under controlled observation noise. Every observation and result in this
section is synthetic. The year labels mirror the planned 1900--1915 training and
1916--1920 testing split; they are not historical pelt counts.

\subsection{Model and normalized approximation}
We use the Rosenzweig--MacArthur model \cite{rosenzweig1963},
\begin{align}
\dot H&=rH(1-H/K)-\frac{aHP}{b+H},\\
\dot P&=\frac{eaHP}{b+H}-mP.
\end{align}
Time is measured in years and both states are synthetic abundance indices. The primary
inverse task estimates $r,a,m$, with $K=60$, $b=20$ and $e=0.6$ fixed. These constants
equal their generating values only in the controlled synthetic study; this favorable
assumption must be revisited for historical observations.

Let $s_H,s_P$ be the maxima of the training observations and $T=15$ years. A network
with three hidden layers of 48 tanh units maps $x=2t/T-1$ to positive normalized states
$(u_\theta,v_\theta)=\operatorname{softplus}(N_\theta(x))+10^{-10}$, giving
$\widehat H=s_Hu_\theta$ and $\widehat P=s_Pv_\theta$. Unknown rates are bounded by
$q=\ell_q+(h_q-\ell_q)\operatorname{sigmoid}(\eta_q)$, using
$r\in[0.2,2.5]$, $a\in[0.3,4]$ and $m\in[0.1,1.2]$. These are numerical study bounds,
not biological conclusions.

\subsection{Physics residuals and optimization}
Following the data-plus-physics construction of PINNs \cite{raissi2019}, we form
\begin{align}
R_H&=\frac{du_\theta}{dt}-\frac{f_H(s_Hu_\theta,s_Pv_\theta;q)}{s_H},\\
R_P&=\frac{dv_\theta}{dt}-\frac{f_P(s_Hu_\theta,s_Pv_\theta;q)}{s_P},\\
L&=L_{\mathrm{data}}+10L_{\mathrm{physics}}+10L_{\mathrm{IC}},\qquad
L_{\mathrm{physics}}=\frac{1}{2N_c}\sum_{j=1}^{N_c}(R_H(t_j)^2+R_P(t_j)^2).
\end{align}
Data loss is the mean squared normalized observation error across both species; IC
loss is the two-state mean squared error at $t=0$. The first observation appears in
both terms, deliberately emphasizing the initial state. There are $N_c=161$ equally
spaced collocation points on $[0,15]$, including endpoints, and none in the forecast
interval. PyTorch automatic differentiation \cite{pytorchgrad} differentiates with
respect to elapsed time, accounting for the internal factor $2/T$.

Training uses float64, one CPU thread and fixed seeds. Xavier initialization and a
500-step data/IC warmup precede Adam (learning rate 0.002, at most 5000 joint steps,
gradient norm clipped at 10). Complete training losses are checked every 100 steps;
Adam stops after 15 checks without improvement exceeding $10^{-8}$ or at its cap.
The best state is refined with L-BFGS and strong-Wolfe line search, at most 600 iterations
and 750 closure evaluations, with gradient and change tolerances $10^{-10}$ and
$10^{-12}$. The saved state minimizes the recorded training objective. Closure logs
include line-search trials, so they need not be monotonic. An iteration cap does not
prove global convergence. An offset grid of 307 training-domain points diagnoses
residuals between collocation points after fitting.

\subsection{Synthetic validation and forecasting protocol}
The generating parameters are $(r,K,a,b,e,m)=(1,60,2,20,0.6,0.5)$, with
$(H_0,P_0)=(35,9)$. Multiplicative noise uses
$y_i^{\mathrm{obs}}=y_i^{\mathrm{true}}(1+0.03\epsilon_i)$,
$\epsilon_i\sim\mathcal N(0,1)$ independently per species and time. Values are clipped
below at $10^{-8}$ and the initial state is exact by design. Noise seed 314 is fixed.
We compare 61 clean quarterly, 61 noisy quarterly and 16 noisy annual training samples,
each with optimizer seeds 17, 29 and 43. These optimizer replicates condition on one
noise realization per case and are not uncertainty intervals.

All ODE integrations use SciPy RK45 \cite{scipysolve}, relative tolerance $10^{-8}$,
absolute tolerance $10^{-10}$ and maximum step 0.1 years. A six-start least-squares
benchmark uses the same unknowns, fixed values, bounds, state scaling, initial condition
and solver. It minimizes normalized training observation errors; an additional physics
penalty is unnecessary for its directly integrated trajectories. The default annual
PINN seed is selected by training loss only. Learned parameters are frozen and inserted
into the ODE solver, which integrates from 1900 through 1920. Neural network
extrapolation and test-state restarts are not used.

\subsection{Measured recovery and forecast results}
Absolute relative parameter error is $100|\widehat q/q_{\mathrm{true}}-1|$.
Table~\ref{tab:yash-recovery} reports mean and maximum errors across three seeds.
"""
    section += f"The largest clean-case error was {clean_max:.4f}\\%, compared with {noisy_max:.3f}\\% for dense noisy data and {annual_max:.3f}\\% for annual noisy data. "
    section += f"The selected annual estimate was $\\widehat r={p['r']:.6f}$, $\\widehat a={p['a']:.6f}$ and $\\widehat m={p['m']:.6f}$.\n"
    section += r"""
The smaller annual error in this realization does not establish a sampling-frequency
advantage. The finite noise realizations differ and the fixed constants are correct.
\begin{table}[htbp]\centering
\caption{Synthetic parameter recovery across optimizer seeds, conditional on correct fixed constants.}
\label{tab:yash-recovery}\input{tables/recovery}
\end{table}

Table~\ref{tab:yash-forecast} reports five-point held-out RMSE and MAE separately for each
species, against both noisy observations and latent generating truth. Least squares
has lower hare error against noisy observations, while the selected PINN has lower
lynx error. The selected PINN is closer to latent truth for both species in this
realization. This mixed result does not establish general superiority.
\begin{table}[htbp]\centering\small
\caption{Frozen ODE forecasts for five synthetic held-out years. H and P denote hare and lynx indices.}
\label{tab:yash-forecast}\input{tables/metrics}
\end{table}
\begin{figure}[htbp]\centering
\ReportGraphEPS[width=\linewidth]{forecast_comparison.eps}
\caption{Synthetic observations and ODE forecasts. The shaded period is held out.
Both methods integrate from the first training observation. The PINN seed is chosen
using training loss only.}\label{fig:yash-forecast}
\end{figure}
\begin{figure}[htbp]\centering
\ReportGraphEPS[width=0.88\linewidth]{parameter_recovery.eps}
\caption{Absolute relative recovery errors. Points are optimizer seeds, and black
marks are means. These are not confidence intervals.}\label{fig:yash-recovery}
\end{figure}

\subsection{Sensitivity and interpretation}
Prespecified annual-data runs vary physics weight from 10 to 1 or 100 and multiply
initial rate guesses by 0.6 or 1.4, holding seed 17 fixed. Their forecasts are shown in
Figure~\ref{fig:yash-sensitivity}; these variants do not select a configuration on test
errors. A local finite-difference sensitivity matrix of normalized training trajectories
with respect to log parameters gives condition numbers
"""
    section += f"{spectrum['three_parameters']['condition_number']:.2f} for varying $r,a,m$ and {spectrum['six_parameters']['condition_number']:.2f} for varying all six parameters locally.\n"
    section += r"""
The larger local problem contains less sensitive directions. This diagnostic is not
an all-six PINN fit or a proof of structural or global identifiability.
\begin{figure}[htbp]\centering
\ReportGraphEPS[width=\linewidth]{sensitivity.eps}
\caption{Sensitivity of synthetic forecasts to physics weight and initial guesses.
Configurations were declared before held-out scoring.}\label{fig:yash-sensitivity}
\end{figure}

The results rely on a correctly specified generating ODE, three known constants and
an exact initial state. Finite collocation and nonconvex training may still leave a
network/ODE mismatch, so residual checks and training-domain consistency plots are
provided with the code. Three seeds on one noise realization do not quantify measurement
uncertainty. Five held-out years and an idealized two-species system cannot address pelt
trading bias, missing ecology or unknown observation scales. Historical fitting must
use the team's agreed equations, units, feasible ranges and sealed test period.

\subsection{Reproducible handoff}
The repository supplies source code, configuration, an executed notebook, recovery
tables, all default-seed forecast scores, EPS/PNG figures, optimization logs and a
runtime/source-hash manifest. A three-column Year/Hare/Lynx CSV contains only the five
held-out synthetic predictions for Advay. The solver and least-squares implementation
are provisional scaffolding pending integration with Rishi and Advay. Yash's personal
AI assistance log separates assistant-run checks from checks Yash still needs to perform.
"""
    write("report/yash_pinn_section.tex", section)
    for extension in ("eps", "pdf"):
        for graph in (OUT / "figures").glob(f"*.{extension}"):
            dest = ROOT / "report/graphs" / graph.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(graph, dest)

    presentation = f"""# Yash presentation notes

Target: about two minutes. Use two slides and point to figures rather than reading formulas.

## Slide 1 How the inverse PINN works

Show the two model equations, a time → network → hare/lynx sketch, and
L = data error + 10 × physics error + 10 × initial-condition error.

**Speaking notes, about 60 seconds**

“My part tests whether a physics-informed neural network can recover model parameters
while fitting observations. I used synthetic data because our final historical data
and shared interfaces are not ready yet. The network takes scaled time and predicts
positive hare and lynx indices. Automatic differentiation computes their time derivatives.
The loss penalizes observation errors, violations of both differential equations, and
initial-condition errors. I estimate r, a and m within positive bounds, while fixing K,
b and e for this controlled test. I train with Adam and then L-BFGS, and repeat the fit
with three random seeds. The exact initial state and correct fixed constants are favorable
assumptions that we will need to revisit for the real data.”

## Slide 2 What the synthetic tests show

Show `parameter_recovery.png` beside `forecast_comparison.png`, with the words
**Synthetic data**, **ODE forecast**, and **Mixed comparison** clearly visible.

**Speaking notes, about 60 seconds**

“Across three seeds, the maximum parameter error was {clean_max:.4f} percent for clean
quarterly data and {annual_max:.3f} percent for the noisy annual case. These are optimizer
replicates on one noise realization, not confidence intervals. For forecasting, I freeze
the learned parameters and integrate the ODE through the five held-out years. I do not
extrapolate the neural network. Against noisy test observations, least squares has lower
hare error and the selected PINN has lower lynx error, so there is no overall win to
claim. I also vary loss weights and initial guesses and check local parameter sensitivity.
The current conclusion is that the implementation works on this controlled example.
The next empirical step is to use the team's agreed data and assumptions without
changing the method using the test period.”

## Questions to rehearse

- Why fix three parameters? To define a tractable controlled inverse test; correctness
  of those fixed values is a strong assumption, not something recovered by the PINN.
- Why scale both species? To avoid one index dominating the data loss through its units.
- Why use autograd? To differentiate the network through its internal time transformation.
- Why compare with least squares? It tests whether the neural approximation adds value
  beyond directly fitting this small ODE model; better performance is not assumed.
- Why use an ODE forecast? It tests the learned mechanistic parameters and avoids
  treating unconstrained neural extrapolation as a dynamical forecast.
- What is still provisional? Real measurements, observation conventions, parameter ranges
  and the final shared model and solver. Historical predictive performance is untested.
"""
    write("presentation/yash_pinn_notes.md", presentation)

    notebook = nbf.v4.new_notebook()
    cells = []
    md = lambda text: cells.append(nbf.v4.new_markdown_cell(text.strip()))
    code = lambda text: cells.append(nbf.v4.new_code_cell(text.strip()))
    md("""# Yash's inverse PINN for lynx and hare dynamics

**All observations in this notebook are synthetic.** Year labels reproduce the planned
1900–1915 training and 1916–1920 testing split. They are not historical pelt counts.

We implement an inverse PINN, recover known parameters under controlled noise, then
freeze those parameters and use an ODE solver for held-out predictions. The notebook
documents Yash's part and provisional integration aids, not the entire group's work.

<div style="border-left:4px solid #197278;padding-left:12px">Read the mathematical
explanations before running each code block. The default experiment driver reuses
completed runs with a matching configuration; fresh training requires a new result directory.</div>""")
    md("""## Setup and reproducible configuration

Use the environment in the README. Seeds, bounds, loss weights and solver tolerances
are explicit. This notebook locates the repository from either its root or the notebook
directory; it contains no machine-specific absolute paths.""")
    code("""from pathlib import Path
import sys, json, csv
ROOT = Path.cwd().resolve()
if not (ROOT / 'configs/synthetic.json').exists():
    ROOT = ROOT.parent
assert (ROOT / 'configs/synthetic.json').exists(), 'Run from the repository or notebooks folder'
sys.path.insert(0, str(ROOT / 'src'))
import numpy as np
import torch
from IPython.display import display, Markdown, Image
CONFIG = json.loads((ROOT / 'configs/synthetic.json').read_text())
display(Markdown('**Configuration**'))
print(json.dumps(CONFIG, indent=2))""")
    embedded_sources = {}
    modules = [
        ("model.py", "Complete program 1 Model and ODE solver",
         "The following cell defines both NumPy and Torch versions of the equations and the common RK45 solver. The solver checks inputs, integration success and nonnegative states."),
        ("data.py", "Complete program 2 Data and synthetic observations",
         "This cell validates the training-data contract, computes training-only scales, and generates controlled-noise observations. The first observation is exact in this synthetic experiment."),
        ("pinn.py", "Complete program 3 Inverse PINN and training",
         "The full network, bounded unknown parameters, automatic residuals, loss terms, Adam warmup/joint optimization, L-BFGS refinement and checkpoint selection appear below. Training receives no held-out observations or generating truth."),
        ("baseline.py", "Complete program 4 Matching baseline and identifiability",
         "Least squares fits the same unknowns with the shared solver, fixed constants, bounds and initial condition. Finite differences of log parameters provide a local sensitivity diagnostic."),
        ("figures.py", "Complete program 5 Publication figures",
         "These functions build every scientific figure from saved numerical evidence and export matching PNG, EPS and vector PDF formats. The PDF companions let PDF engines compile the EPS-referenced report without a system EPS converter."),
        ("experiments.py", "Complete program 6 Experiment and evaluation pipeline",
         "This cell contains the complete driver for the declared recovery cases, sensitivity runs, training-only seed selection, frozen ODE forecasts and held-out scoring. It resumes matching saved runs to avoid unnecessary retraining. For fresh training, first move the existing results/synthetic directory aside.")
    ]
    for filename, heading, explanation in modules:
        source = (ROOT / "src/lynx_hare" / filename).read_text(encoding="utf-8")
        parsed = ast.parse(source)
        excluded_lines = set()
        for node in ast.walk(parsed):
            if isinstance(node, ast.ImportFrom) and node.level > 0:
                excluded_lines.update(range(node.lineno, node.end_lineno + 1))
        for node in parsed.body:
            if isinstance(node, ast.If) and isinstance(node.test, ast.Compare) and "__name__" in ast.unparse(node.test):
                excluded_lines.update(range(node.lineno, node.end_lineno + 1))
        inline = "\n".join(line for i, line in enumerate(source.splitlines(), 1) if i not in excluded_lines)
        ast.parse(inline)
        embedded_sources[filename] = hashlib.sha256((ROOT / "src/lynx_hare" / filename).read_bytes()).hexdigest()
        md(f"## {heading}\n\n{explanation}\n\nThis code cell is generated from `src/lynx_hare/{filename}`. The notebook includes the implementation directly, with internal package imports removed because earlier cells define those functions.")
        code(inline)
    md(r"""## Model and scaling

$$\dot H=rH(1-H/K)-\frac{aHP}{b+H},\qquad \dot P=\frac{eaHP}{b+H}-mP.$$

The inverse task estimates **r, a, m**. Correct K, b and e are fixed for this synthetic
test and are not learned. Numerical normalization uses only the maximum training value
for each species: u=H/s_H and v=P/s_P. The network receives x=2t/T−1, T=15 years, and
returns softplus-positive states. These are numerical normalizations of the dimensional
ODE, not a replacement for Arnav's eventual model derivation.

Every unknown uses a positive bounded sigmoid transform. The Torch and NumPy right-hand
sides implement identical equations; a test compares them at independent states.""")
    code("""print('Estimated:', CONFIG['trainable'])
print('Fixed:', {k: v for k, v in CONFIG['initial_guess'].items() if k not in CONFIG['trainable']})
print('Solver:', CONFIG['solver'])
print('Network and training implementation:', ROOT / 'src/lynx_hare/pinn.py')""")
    md(r"""## Residuals and training algorithm

$$R_H=\frac{du_\theta}{dt}-\frac{f_H(s_Hu_\theta,s_Pv_\theta;q)}{s_H},\qquad
R_P=\frac{dv_\theta}{dt}-\frac{f_P(s_Hu_\theta,s_Pv_\theta;q)}{s_P}.$$
$$L=L_{data}+10L_{physics}+10L_{IC},\quad L_{physics}=\frac1{2N_c}\sum_j(R_H^2+R_P^2).$$

Autograd differentiates with respect to elapsed t and handles the internal time scale.
Residuals have units of inverse years. The first training row also defines the IC loss.

1. Scale training observations; create 161 collocation points only in [0,15].
2. Initialize a three-hidden-layer tanh network, positive states and bounded unknowns.
3. Warm up on data and IC for 500 steps, then jointly optimize with Adam.
4. Stop at the cap or training plateau, then refine with L-BFGS.
5. Retain the best recorded training objective. Never select using the test data.
6. Freeze parameters; integrate the ODE from the first training state and score test years.

The driver below runs all declared cases or resumes the supplied reference results.
No cloud service, external tracker, remote dataset or Git push is invoked.""")
    code("""OUT = run(ROOT)
manifest = json.loads((OUT / 'manifest.json').read_text())
print('Synthetic runs:', manifest['run_count'])
print('Selected using training loss:', manifest['selected_run'])
print('Versions:', manifest['versions'])""")
    md("""## Training data contract

The generator uses the known parameters in the configuration, multiplicative 3% Gaussian
noise (seed 314), and an exact initial state. The first row is not noised. The training
loader masks years after 1915 before calculating normalization. Historical data must
be supplied under an agreed observation convention; these indices are not populations.""")
    code("""training = read_training(ROOT / 'data/synthetic/annual_train.csv')
print('Training years:', training.years.astype(int))
print('Species scales from training only:', training.scale)
print('Initial state:', training.initial_state)
assert training.years.max() == 1915
assert len(training.years) == 16
print((ROOT / 'data/synthetic/provenance.json').read_text())""")
    md("""## Parameter recovery over seeds

Recovery error is 100|estimate/truth−1| for each unknown. Three optimizer seeds are used
for each clean/noisy dense case and the annual noisy case. Noise is held fixed within
each case. Variation across optimizer seeds is not an observation uncertainty interval.""")
    code("""def table(path, columns=None):
    with Path(path).open(newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    columns = columns or list(rows[0])
    body = '| ' + ' | '.join(columns) + ' |\\n| ' + ' | '.join(['---'] * len(columns)) + ' |\\n'
    for row in rows:
        values = []
        for name in columns:
            value = row[name]
            try:
                value = f'{float(value):.6g}'
            except ValueError:
                pass
            values.append(value)
        body += '| ' + ' | '.join(values) + ' |\\n'
    display(Markdown(body))
table(OUT / 'parameter_recovery.csv', ['case','seed','variant','parameter','estimated','truth','learned','absolute_relative_error_percent'])
display(Image(filename=str(OUT / 'figures/parameter_recovery.png')))""")
    md("""## Loss curves and mechanistic consistency

The curves show the weighted total and unweighted loss components. Adam steps are
followed by L-BFGS closure evaluations, which include line-search trials. The warmup
is omitted from this trace. Low loss is not by itself proof of convergence. Compare
the network with the ODE using its learned parameters, then inspect residuals on an
offset grid inside the training interval.""")
    code("""for name in ('training_losses', 'network_ode_consistency', 'residual_check'):
    display(Image(filename=str(OUT / 'figures' / f'{name}.png')))
selected = json.loads((OUT / 'selected_run.json').read_text())
audit = json.loads((OUT / 'runs' / selected['run_id'] / 'summary.json').read_text())
print('Training objective:', audit['audit']['training_objective'])
print('Adam stopping reason:', audit['audit']['adam_stop'])
print('L-BFGS iterations / evaluations:', audit['audit']['lbfgs_iterations'], audit['audit']['lbfgs_closure_evaluations'])
print('Independent residual RMS:', audit['residual_check_rms'])""")
    md("""## Frozen ODE forecasts and matching baseline

All forecasts integrate from the same first training observation. The PINN network is
not extrapolated past 1915. The baseline fits the same three unknowns and fixed values
with six starts and the same scaling, initial state, bounds and RK45 settings.

RMSE and MAE are separate for hare and lynx. Noisy-observation scores answer a different
question from latent-truth scores. The selected default annual seed minimizes its
training objective; every default seed's held-out score remains visible.""")
    code("""table(OUT / 'heldout_metrics.csv')
display(Image(filename=str(OUT / 'figures/forecast_comparison.png')))
print('Handoff forecast (synthetic units):')
print((OUT / 'predictions_for_advay.csv').read_text())""")
    md("""## Loss weights, initial guesses and local identifiability

Sensitivity variants fix optimizer seed 17 and change physics weight from 10 to 1 or
100, or multiply the unknown initial guesses by 0.6 or 1.4. These configurations were
prespecified and are not a test-based search.

The singular values of the scaled trajectory Jacobian with respect to log parameters
compare the primary three-parameter local problem with locally varying all six
parameters. This is not an all-six PINN fit or a proof of structural identifiability.""")
    code("""print((OUT / 'identifiability.json').read_text())
for name in ('sensitivity', 'identifiability'):
    display(Image(filename=str(OUT / 'figures' / f'{name}.png')))""")
    md("""## Findings and limits

The following summary is generated from the saved experiment outputs. It distinguishes
measured results from assumptions, mixed comparisons and work still needed for real
observations. The complete method and team integration instructions are in `docs/`.""")
    code("""display(Markdown((ROOT / 'docs/results_summary.md').read_text()))""")
    md("""## Handoff and acknowledgement

Send Advay `predictions_for_advay.csv`, `selected_run.json`, the seed-wise metrics and
training logs. Confirm equations/scaling with Arnav, parameter constraints with Joel,
and the solver contract with Rishi. Real fitting must use new outputs and replace the
synthetic results and provenance. The present package does not invent teammate work.

The report source is `report/yash_pinn_section.tex`, with generated tables and EPS figures.
Presentation notes are in `presentation/yash_pinn_notes.md`. The AI assistance log records
assistant-generated work and automated checks; Yash should add his own manual checks.

References: [Rosenzweig–MacArthur (1963)](https://doi.org/10.1086/282272),
[Raissi et al. (2019)](https://doi.org/10.1016/j.jcp.2018.10.045),
[PyTorch autograd](https://docs.pytorch.org/docs/stable/generated/torch.autograd.grad.html),
[SciPy solve_ivp](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html).""")
    notebook.cells = cells
    notebook.metadata = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                         "language_info": {"name": "python", "version": "3.12"},
                         "embedded_source_sha256": embedded_sources}
    (ROOT / "notebooks").mkdir(exist_ok=True)
    notebook_path = ROOT / "notebooks/yash_pinn.ipynb"
    if notebook_path.exists():
        existing = nbf.read(notebook_path, as_version=4)
        if [(c.cell_type, c.source) for c in existing.cells] == [(c.cell_type, c.source) for c in notebook.cells]:
            notebook = existing  # Preserve execution evidence when only report assets changed.
    nbf.write(notebook, notebook_path)
    print(f"Built measured summary, report, presentation notes and {len(cells)}-cell notebook")


if __name__ == "__main__":
    main()
