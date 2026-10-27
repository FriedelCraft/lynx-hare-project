"""Builds and executes notebooks/rishi_simulations.ipynb.

Run: python scripts/build_rishi_notebook.py [--no-execute]

The notebook embeds src/lynx_hare/simulation.py and simulation_plots.py as code cells
(package-relative imports rewritten to absolute ones), so it shows the complete
implementation while staying identical to the canonical modules.
"""
import re
import sys
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "notebooks" / "rishi_simulations.ipynb"

cells = []
md = lambda s: cells.append(nbf.v4.new_markdown_cell(s.strip()))
code = lambda s: cells.append(nbf.v4.new_code_cell(s.strip()))

BLUE, GREEN, ORANGE, PURPLE = ("#e8f1fb", "#1f5fa8"), ("#e9f7ee", "#1e7a45"), ("#fff3e3", "#b8620a"), ("#f2ecfa", "#6a3ea1")


def box(colors, title, body):
    bg, border = colors
    md(f'<div style="background:{bg}; border-left:6px solid {border}; padding:12px 16px; '
       f'border-radius:6px; color:#1a1a1a;">\n\n<b style="color:{border}; font-size:1.1em;">{title}</b>'
       f'\n\n{body.strip()}\n\n</div>')


def embed(filename):
    src = (ROOT / "src" / "lynx_hare" / filename).read_text(encoding="utf-8")
    src = re.sub(r"^from \.model import", "from lynx_hare.model import", src, flags=re.M)
    src = re.sub(r"^from \. import (.+)$", r"from lynx_hare import \1", src, flags=re.M)
    code(f"# Generated from src/lynx_hare/{filename}\n" + src)


md("""
<div style="background:linear-gradient(90deg,#1f5fa8,#6a3ea1); padding:18px 22px; border-radius:8px; color:white;">
<h1 style="color:white; margin:0;">Section 3 &mdash; Numerical Simulations and Visualisation</h1>
<p style="margin:6px 0 0 0;">MAC F314 Mathematical Modelling &middot; Canadian lynx&ndash;snowshoe hare &middot; Owner: Rishi</p>
</div>
""")

box(BLUE, "What this section does", r"""
Section 2 (Joel) proves that the coexistence equilibrium $E^*$ of the Rosenzweig&ndash;MacArthur model loses stability at

$$K_H = b + 2H^*, \qquad H^* = \frac{mb}{ea-m},$$

where a complex pair of eigenvalues crosses the imaginary axis (Hopf bifurcation). Linear analysis is **local**: it describes
behaviour near $E^*$ at a single parameter value. This section tests the analytic claims numerically and **measures what
linearisation cannot give**: global behaviour, cycle size, period, predator lag and the shape of the bifurcation.

| Output | Question it answers |
|---|---|
| Fig. 1 | Is the solver accurate enough to trust? |
| Regime table | Do simulations reproduce Joel's validation targets A&ndash;F? |
| Fig. 2 | Does stability switch where the theory says? |
| Fig. 3 | Is the cycle a *stable* limit cycle (unlike Lotka&ndash;Volterra)? |
| Fig. 4 | Do the eigenvalues cross the imaginary axis exactly at $K_H$? |
| Fig. 5 | Is the cycle born at $K_H$ with zero size? (bifurcation diagram) |
| Fig. 6 | Does it grow like $\sqrt{K-K_H}$ with period $\to T_0$? (supercritical Hopf) |
""")

box(PURPLE, "Model, parameters and solver", r"""
$$\frac{dH}{dt} = rH\left(1-\frac{H}{K}\right) - \frac{aH}{b+H}P, \qquad \frac{dP}{dt} = e\frac{aH}{b+H}P - mP$$

$H, P$: hare and lynx index (thousand pelts); $t$ in years. **Illustrative, not fitted** (Section 2, &sect;1.8):
$r=1.5,\ a=4,\ b=30,\ e=0.4,\ m=0.8$, so $ea = 2m$ and

$$H^* = 30,\quad K_H = 90,\quad \omega_0 = \sqrt{rmb/K_H} \approx 0.632,\quad T_0 = 2\pi/\omega_0 \approx 9.94 \text{ yr}.$$

**Solver:** `scipy.integrate.solve_ivp`, RK45 (Dormand&ndash;Prince). Each step evaluates the right-hand side seven times and
combines the slopes into a 4th- and a 5th-order estimate; their difference estimates the local error. Steps whose error exceeds
`rtol`$\cdot|y|$ + `atol` are rejected and shrunk, small errors let the next step grow.

**Two solver settings, two jobs.** Fitting and the 1900&ndash;1920 forecasts (Yash, Advay) use `model.solve`:
RK45, `rtol = 1e-8`, `atol = 1e-10`, `max_step = 0.1` years, identical for both fitting methods (`configs/historical.json`).
The long-run simulations here run for thousands of years and use tighter tolerances: RK45, `rtol = 1e-10`,
`atol = 1e-12`, no step cap (`simulation.integrate`). Both call the same `model.rhs`.
Illustrative runs start at $(20, 5)$ with a 3000-year burn-in (20,000 years within one unit of $K_H$, where the
equilibrium is a weak focus and transients decay very slowly).

All values above live in `configs/simulations.json`. All trajectories use the team's single right-hand side `model.rhs`; analytic targets come from Joel's `stability.py`.
""")

code(r"""
import sys
from pathlib import Path
ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display

from lynx_hare.model import Parameters, rhs        # shared model (Arnav / group contract)
from lynx_hare import stability as st              # Joel's closed forms
""")

box(GREEN, "Implementation 1 &mdash; simulation layer (`src/lynx_hare/simulation.py`)", r"""
Algorithms in this module:

- **`integrate`**: RK45 with the declared tolerances; fails loudly if the solver does.
- **`attractor_summary`**: integrate to $T_\text{burn} + T_\text{rec}$, **discard** $t < T_\text{burn}$, and on the recorded window
  return $\min/\max$ of $H$ and $P$. If $H$ still oscillates, the period is the mean gap between successive hare maxima, and
  the lag is the mean delay from each hare maximum to the next lynx maximum.
- **`bifurcation_sweep`**: `attractor_summary` over a grid of $K$; equal max and min means an equilibrium, a gap means a cycle.
- **`amplitude_law`**: half-amplitude $A$ and period at $K = K_H + \Delta K$; least-squares line through $(\ln\Delta K, \ln A)$.
- **Lotka&ndash;Volterra helpers** and a fixed-step **Euler** method for the solver-accuracy check.
""")
embed("simulation.py")

box(GREEN, "Implementation 2 &mdash; figures (`src/lynx_hare/simulation_plots.py`)", r"""
Each function draws one publication figure. EPS cannot store transparency, so no figure uses `alpha`.
Phase portraits show both nullclines, $E^*$ (filled = stable, open = unstable) and a normalised direction field.
""")
embed("simulation_plots.py")

code(r"""
plt.rcParams.update(STYLE)
BASE = Parameters(K=150.0, **ILLUSTRATIVE)
KH = st.hopf_threshold(BASE)
print(f"H* = {st.coexistence_prey(BASE):.4f}   K_H = {KH:.4f}   T_0 = {st.onset_period(BASE):.3f} years")
""")

box(ORANGE, "Step 1 &mdash; Can we trust the solver? (Figure 1)", r"""
**Test A: a conserved quantity.** For Lotka&ndash;Volterra $\dot H = \alpha H - \beta HP,\ \dot P = \delta HP - \gamma P$, the function
$V(H,P) = \delta H - \gamma \ln H + \beta P - \alpha \ln P$ satisfies $\dot V = 0$. Along an exact solution $V$ is constant,
so any change in a numerical solution is **pure numerical error**. We compare RK45 with Euler, $y_{n+1} = y_n + h f(y_n)$.

**Test B:** re-solve with tolerances 100 times tighter. **Test C:** populations stay positive (the axes are invariant).
""")
code(r"""
fig, check = solver_validation()
plt.show()

pF = with_K(BASE, 150.0)
t = np.linspace(0, 200, 8001)
a = integrate(pF, Y0, (0, 200), t_eval=t).y
b = integrate(pF, Y0, (0, 200), t_eval=t, rtol=1e-12, atol=1e-14).y
print(f"max |V - V0|: RK45 {check['max_drift_rk45']:.1e},  Euler {check['max_drift_euler']:.1e}")
print(f"relative change with 100x tighter tolerances: {np.abs(a - b).max() / np.abs(b).max():.1e}")
print(f"smallest state value at K = 150: {a.min():.3f}  (> 0)")
""")
box(GREEN, "Reading Figure 1", r"""
RK45 keeps $V$ constant to about $10^{-10}$, so its orbit is closed as the theory requires. Euler's $V$ creeps up and its orbit
spirals outward, **inventing** behaviour the model does not have. Without an accurate solver we could not tell a real limit
cycle from a numerical artefact.
""")

box(BLUE, "Step 2 &mdash; Reproducing Section 2's validation targets", r"""
For each regime: eigenvalues of the Jacobian (at $E_1 = (K,0)$ for A, where $E^*$ is infeasible; at $E^*$ otherwise), then a
simulation from $(20,5)$ with a 3000-year burn-in and 400 recorded years.
""")
code(r"""
rows = regime_table(BASE)
pd.DataFrame([{
    "regime": r["label"], "K": r["K"], "class": r["regime"],
    "eigenvalues": ", ".join(f"{z.real:+.3f}{z.imag:+.3f}i" for z in r["eig"]),
    "H range": f"[{r['Hmin']:.1f}, {r['Hmax']:.1f}]", "P range": f"[{r['Pmin']:.2f}, {r['Pmax']:.2f}]",
    "period (yr)": round(r["period"], 2), "lynx lag (yr)": round(r["lag"], 2)} for r in rows]).set_index("regime")
""")
box(GREEN, "Reading the regime table", r"""
Every row reproduces Joel's Table 2: A $\to (25,0)$; B and C settle on $(30, 11.25)$ and $(30, 14.56)$; E has
$H\in[15.8, 50.9]$, $T = 10.25$ yr; F has $H \in [1.1, 134.3]$, $T = 13.91$ yr. At **D** ($K = K_H$) a residual oscillation
of about $\pm 1.5$ remains after 3000 years: at the Hopf point decay is only algebraic ($\sim t^{-1/2}$), so this is a slow
transient, **not** a cycle. The lynx lag grows from about a quarter-period (2.5 yr) at onset to 4.5 yr at $K = 150$.
""")

box(BLUE, "Step 3 &mdash; Time series and phase portraits (Figure 2)", r"""
Regimes **B** (well below $K_H$), **C** (just below), **E** (just above), **F** (well above). Prey nullcline: the hump
$P = \frac{r}{a}(1-\frac{H}{K})(b+H)$ with peak at $H = \frac{K-b}{2}$; predator nullcline: the line $H = H^* = 30$.
Graphical criterion: $E^*$ is stable iff the vertical line meets the hump **right of its peak**.
""")
code(r"""
fig = regimes(BASE)
plt.show()
for K in (60, 85, 95, 150):
    p = with_K(BASE, K)
    tr, det = st.coexistence_trace_det(p)
    print(f"K = {K:3d}: trace = {tr:+.4f}, det = {det:.4f}  ->  {st.regime(p)}")
""")
box(GREEN, "Reading Figure 2", r"""
- **B ($K=60$):** line right of the peak; oscillations die within a few decades and the orbit spirals into $E^*$.
- **C ($K=85$):** still right of the peak but barely; the trace is only $-0.044$, so decay takes centuries (e-fold about 45 yr).
- **E ($K=95$):** line just left of the peak; $E^*$ is unstable and the orbit settles on a cycle of period about 10 years.
- **F ($K=150$):** a large cycle; hares boom to 134 thousand and crash to about 1 thousand, lynx follow 4.5 years later.

The switch from decay to sustained cycling happens at $K_H = 90$, as Section 2 predicts. The flow is counter-clockwise.
""")

box(ORANGE, "Step 4 &mdash; Is the cycle a stable limit cycle? (Figure 3)", r"""
Lotka&ndash;Volterra has a different closed orbit for every start (neutral stability). A **stable limit cycle** is an isolated
orbit approached from both sides. At $K = 150$ we start inside (next to the unstable $E^*$) and outside, and track hare peaks.
""")
code(r"""
fig, last = limit_cycle_attracts(BASE)
plt.show()
for name, peaks in last.items():
    print(f"{name:28s} last three hare peaks: {np.round(peaks, 4)}")
""")
box(GREEN, "Reading Figure 3", r"""
The inside orbit spirals **out**, the outside one spirals **in**, and both peak sequences converge to the same value (134.277).
So after a disturbance the populations return to the *same* cycle, the key improvement over Lotka&ndash;Volterra.
This is numerical evidence for one parameter set; the general statement is Cheng's uniqueness theorem cited in Section 2.
""")

box(BLUE, "Step 5 &mdash; Eigenvalues of J(E*) versus K (Figure 4)", r"""
$\det J^* > 0$ for every feasible $K$, so the real part of the eigenvalues has the sign of the trace. Prediction: it changes sign
at exactly $K_H = 90$ with $|\operatorname{Im}\lambda| = \omega_0 \approx 0.632$; below $K \approx 42.5$ the eigenvalues are real (node).
""")
code(r"""
fig, info = eigenvalues_vs_K(BASE, np.linspace(30.5, 200, 800))
plt.show()
print(f"numerical trace zero: K = {hopf_crossing(BASE, 60, 120):.10f}   closed form K_H = {KH:.10f}")
print(f"node -> focus at K = {info['node_to_focus_K']:.1f}")
""")
box(GREEN, "Reading Figure 4", r"""
$\operatorname{Re}\lambda$ is negative below 90, zero at 90 and positive above, crossing with nonzero slope (transversality);
$|\operatorname{Im}\lambda| = \omega_0$ at the crossing, so a **complex pair** crosses the imaginary axis: the Hopf condition.
""")

box(ORANGE, "Step 6 &mdash; Numerical bifurcation diagram (Figure 5)", r"""
**Algorithm:** for each $K$ on a grid from 32 to 200, start at $(20,5)$, integrate past the burn-in, **discard** the transient,
and record $\max$ and $\min$ of $H$ and $P$ over 300 further years. Equal max and min: an equilibrium. A gap: a cycle.
""")
code(r"""
sw = CONFIG["bifurcation_sweep"]
sweep = bifurcation_sweep(BASE, np.linspace(sw["K_min"], sw["K_max"], sw["points"]), t_record=sw["record_years"])
fig = bifurcation(BASE, sweep)
plt.show()
below = sweep["K"] < KH - 1
print(f"largest max-min of H for K < 89: {np.max(sweep['Hmax'][below] - sweep['Hmin'][below]):.1e}")
print(f"cycle minimum at K = 200: H = {sweep['Hmin'][-1]:.3f}, P = {sweep['Pmin'][-1]:.3f}")
""")

box(ORANGE, "Step 7 &mdash; Amplitude law and period (Figure 6)", r"""
A **supercritical** Hopf bifurcation predicts a cycle born with zero size whose half-amplitude grows like
$A \approx c\sqrt{K-K_H}$ (slope $\tfrac12$ on a log&ndash;log plot; Section 2: $c \approx 7.8$), and whose period tends to
$T_0 = 2\pi/\omega_0$ as $K \to K_H^+$. A subcritical one would instead jump to a large cycle.
""")
code(r"""
al = CONFIG["amplitude_law"]
law = amplitude_law(BASE, np.geomspace(al["dK_min"], al["dK_max"], al["points"]), t_record=al["record_years"])
fig = amplitude_and_period(law)
plt.show()
print(f"log-log slope s = {law['slope']:.3f}  (prediction 0.5)")
print(f"A = {law['coefficient_sqrt']:.2f} * sqrt(K - K_H)  (Section 2: about 7.8)")
print(f"period at K - K_H = 0.5: {law['period'][0]:.3f} yr  ->  T_0 = {law['onset_period']:.3f} yr")
""")
box(GREEN, "Reading Figures 5 and 6", r"""
- **Below $K_H$** max and min coincide on the equilibrium: no cycle.
- **At $K_H$** the branches split and the cycle is born with **zero** size.
- **Above $K_H$** it grows continuously, with slope $\approx 0.507$: the $\sqrt{K-K_H}$ law of a **supercritical** Hopf bifurcation,
  consistent with Joel's computed $\ell_1 < 0$. The period starts at $T_0 \approx 9.94$ yr and lengthens with $K$.
- **Paradox of enrichment:** the minimum branches sink toward zero (hare minimum about 0.1 thousand at $K = 200$).
  The ODE never reaches zero, but a real, finite population at such troughs would risk extinction.
""")

box(ORANGE, "Step 8 &mdash; Where do the historical fits lie? (Figures 7 and 8)", r"""
The fitting sections estimated all six coefficients from the 1900&ndash;1915 pelt indices (thousands of pelts) with a PINN
(13 runs: three error models &times; three seeds, wider bounds, physics weight 100) and matched least squares (18 starts).
For **every** saved parameter set we compute, with Joel's closed forms:

- the stability margin $\sigma = K/K_H$ ($\sigma < 1$: $E^*$ stable, oscillations damp; $\sigma > 1$: limit cycle);
- the eigenvalues $\mu \pm i\omega$ at $E^*$, the **e-folding time** $1/|\mu|$ and the **linear period** $2\pi/\omega$;
- the period and lynx lag of the first century simulated from the fitted 1900 state (Advay's check: about 10 yr, 1&ndash;2 yr);
- which coefficients sit within 0.5% of a box limit.

Only saved parameters and the training file are read; the test file is never opened. First we confirm the parameters are
read correctly: re-integrating Yash's selected fit with `model.solve` and the historical settings must reproduce his saved path.
The bifurcation sweeps take several minutes.
""")
code(r"""
import runpy
placement = runpy.run_path(str(ROOT / "scripts" / "rishi_historical_placement.py"))
res = placement["compute"]()
print(f"model.solve reconstruction difference: {res['summary']['reconstruction_max_abs_difference']:.1e}")
cols = ["label", "sigma", "regime", "eigenvalue", "efold_years", "linear_period",
        "first_century_period", "first_century_lag", "cycle_H_range", "cycle_period", "parameters_on_bounds"]
display(pd.DataFrame([r for r in res["table"] if r["selected"]])[cols].set_index("label"))
for k, (lo, hi) in res["summary"]["sigma_range_by_group_excluding_poor_minima"].items():
    print(f"{k:38s} sigma in [{lo:.3f}, {hi:.3f}]")
""")
code(r"""
fig_sigma, fig_bif = placement["figures"](res)
plt.show()
""")
box(GREEN, "Reading Figures 7 and 8", r"""
- **Same behaviour over the data window.** Every well-fitting set oscillates with a period of about 10 years and a lynx lag of
  1.3&ndash;2 years, matching the data.
- **Different side of the threshold.** PINN fits give $\sigma \approx 1.32$&ndash;$1.48$; least squares gives 1.07 (main),
  0.99 (fitted initial state) and 0.55 (log errors).
- **Why the data cannot decide.** $|\mu|$ is only 0.0002&ndash;0.019 per year, so the e-folding time is 53&ndash;5600 years.
  Over 16 training years oscillations change by a factor $e^{16\mu} \approx 0.74$&ndash;$1.16$: a slowly damped focus and a slowly
  growing spiral give almost the same two cycles.
- **Bounds matter.** $b$ sits on its upper limit in nearly every fit; widening the box moves the PINN's $\sigma$ from 1.36 to 1.48.
- **Long run (Figure 8).** The least-squares fit's eventual cycle ($H$ 5.6&ndash;85, period 10.8 yr) resembles the data; the PINN
  fit's is much larger ($H$ 0.1&ndash;247, period 18.5 yr), so its 1900&ndash;1920 trajectory is an early part of a slowly growing spiral.

**Conclusion:** the fitted model sits close to the Hopf threshold and reproduces the observed period and lag, but these data do
not establish whether the real system is on a stable limit cycle or a slowly damped oscillation.
""")

box(PURPLE, "Summary and handoff", r"""
| Claim | Numerical evidence | Where |
|---|---|---|
| Solver accurate | LV invariant kept to $10^{-10}$ (Euler drifts 0.15); tolerance change $10^{-9}$; positivity | Fig. 1 |
| Section 2 targets | All six regimes, eigenvalues, periods and lags reproduced | table |
| Stability switch at $K_H$ | Decay at $K = 60, 85$; cycles at $K = 95, 150$ | Fig. 2 |
| Stable limit cycle | Inside and outside starts reach the same loop | Fig. 3 |
| Hopf at $K_H = b + 2H^*$ | Trace zero at $K = 90.0000000000$, $|\operatorname{Im}\lambda| = \omega_0$ | Fig. 4 |
| Supercritical Hopf; enrichment | Amplitude $\propto (K-K_H)^{0.507}$, period $\to T_0$, troughs $\to 0$ | Figs. 5, 6 |
| Historical fits | Period ~10 yr, lag 1.3&ndash;2 yr for every good fit; $\sigma$ 0.55&ndash;1.48 depending on method, error model and bounds | Figs. 7, 8 |

**Solvers:** fitting and 1900&ndash;1920 forecasts use `model.solve` (rtol 1e-8, atol 1e-10, max_step 0.1); long-run runs here use
`simulation.integrate` (rtol 1e-10, atol 1e-12).

**Limitations:** the illustrative runs use unfitted parameters; simulation is evidence, not proof; near $K_H$ results depend on
burn-in length; fitted $\sigma$ depends on the box bounds and the error model.
""")

nb = nbf.v4.new_notebook()
nb["cells"] = cells
nb["metadata"]["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
NB.parent.mkdir(exist_ok=True)

if "--no-execute" not in sys.argv:
    from nbclient import NotebookClient
    NotebookClient(nb, timeout=3600, kernel_name="python3",
                   resources={"metadata": {"path": str(NB.parent)}}).execute()
nbf.write(nb, NB)
print("wrote", NB.relative_to(ROOT))
