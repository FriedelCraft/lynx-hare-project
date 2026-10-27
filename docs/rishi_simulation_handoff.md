# Rishi → team handoffs (numerical simulations)

## What is in this branch

| Path | What |
|---|---|
| `configs/simulations.json` | Parameter configuration: illustrative parameters with units, regimes, solver tolerances, initial state, burn-ins, sweep grids |
| `src/lynx_hare/simulation.py` | RK45 wrapper with declared tolerances, attractor summary (range, period, lag), regime table, bifurcation sweep, amplitude law, Lotka–Volterra solver check |
| `src/lynx_hare/simulation_plots.py` | Publication figures (EPS-safe, no transparency) |
| `scripts/rishi_simulations.py` | Runs everything, checks Joel's targets, writes `results/simulations/` and `report/graphs/rishi_*` (about 9 min on one CPU) |
| `scripts/build_rishi_notebook.py` | Builds and executes `notebooks/rishi_simulations.ipynb` from the two modules |
| `notebooks/rishi_simulations.ipynb` | Executed notebook: Markdown explanation, equations and algorithm before each code cell |
| `tests/test_simulation.py` | Solver accuracy, positivity, shared-RHS use, Joel's targets B/E/F, Hopf crossing |
| `report/rishi_simulation_section.tex` | Section for the report (`\input{rishi_simulation_section}` after Joel's section) |
| `report/rishi_main.tex`, `rishi_main.pdf` | Standalone build of Joel's and Rishi's sections together, so cross-references resolve |
| `report/graphs/rishi_*.{eps,pdf}` | Five report figures, EPS plus PDF companion (same convention as Joel and Yash) |
| `report/references.bib` | One entry appended (`dormand1980`); nothing existing changed |

No existing source file or config was modified, so Yash's hash checks and Joel's tests are unaffected.
Every trajectory uses the shared `model.rhs`; every analytic target comes from Joel's `stability.py`.

## Results (illustrative parameters r=1.5, a=4, b=30, e=0.4, m=0.8; H* = 30, K_H = 90)

| Check | Result |
|---|---|
| Solver: Lotka–Volterra invariant drift over 100 time units | RK45 3.7e−10; Euler (h = 0.01) 0.15 |
| Solver: tolerances 100× tighter at K = 150 | relative change 8e−10 |
| Joel's Table 2, regimes A–F (ranges, periods, lags) | all reproduced (`results/simulations/regime_table.csv`) |
| Trace of J(E*) vanishes at | K = 90.0000000000 (closed form 90), \|Im λ\| = ω0 = 0.632 |
| Node → focus | K ≈ 42.6 (Joel: 42.5) |
| Inside and outside starts at K = 150 | same cycle, hare peak 134.277 |
| Bifurcation sweep, K < 89 | max − min of H ≤ 5e−5 (equilibrium) |
| Amplitude law, 0.5 ≤ K − K_H ≤ 8 | slope 0.507, A ≈ 7.81 √(K − K_H) (Joel: 0.507, 7.8) |
| Period at K − K_H = 0.5 | 9.97 yr → T0 = 9.93 yr |
| Paradox of enrichment, K = 200 | cycle minima H = 0.12, P = 0.45 thousand pelts |

## Figure captions

1. **rishi_solver_validation**. Lotka–Volterra orbit and drift of its conserved quantity: RK45 keeps V constant and
   closes the orbit; Euler drifts and spirals outward. Only an accurate solver can separate a real cycle from an artefact.
2. **rishi_regimes**. Time series and phase portraits from (20, 5) for K = 60, 85 (below K_H) and K = 95, 150 (above),
   with both nullclines, the hump peak and E* (filled stable, open unstable). Oscillations decay below K_H and persist above.
3. **rishi_limit_cycle**. At K = 150, starts inside and outside the cycle converge to the same orbit; successive hare
   maxima converge to one value. The cycle is orbitally stable, unlike Lotka–Volterra's neutral orbits.
4. **rishi_eigenvalues** (notebook and `results/simulations/figures/` only, not in the report, because Joel's
   trace–determinant figure already shows it). Real and imaginary parts of the eigenvalues of J(E*) against K.
5. **rishi_bifurcation**. Post-transient max and min of H and P against K. The cycle is born at K_H with zero amplitude
   and its minima approach zero as K grows (paradox of enrichment).
6. **rishi_amplitude_period**. Log–log half-amplitude against K − K_H (slope 0.507, supercritical prediction 1/2) and
   the period tending to T0 = 2π/ω0.

## To Arnav (reply to his handoff)

- The solver keeps the dimensional interface: states (H, P), parameters r, K, a, b, e, m, time in years, shared `model.rhs`.
  No dimensionless solver is used, so no mapping is needed.
- Initial state for the simulations is (20, 5) at t = 0, Joel's convention for the illustrative regimes. The fitting
  protocol's initial state and forecast origin stay with Advay and Yash (below).

## To Yash and Advay

- For forecasts use `lynx_hare.simulation.integrate(p, y0, (t0, t1), t_eval=...)`: shared `model.rhs`, RK45,
  rtol 1e-10, atol 1e-12. `model.solve` (rtol 1e-8, max_step 0.1) is what Yash's saved runs use; if the group
  standardises on one, change it in one place and regenerate results into a new directory.
- Once you have fitted parameters, send them to me: I will place the real system on the bifurcation diagram and report
  σ = K/K_H with its spread over seeds and multistarts (Joel's open question).

## Run

```text
python -m pytest -q tests/test_simulation.py tests/test_stability.py
python scripts/rishi_simulations.py          # figures, tables, summary.json
python scripts/build_rishi_notebook.py       # executed notebook
cd report && latexmk -pdf rishi_main.tex     # Joel + Rishi sections together
```

## 2-minute talk outline (Rishi: dynamics)

1. (15 s) Joel's analysis is local: one equilibrium, one parameter value. I test it numerically and measure what it can't give.
2. (20 s) Solver check: RK45 keeps the Lotka–Volterra invariant to 1e−10; Euler invents a spiral. (Fig 1)
3. (30 s) Below K_H = 90 oscillations die out; above, they persist. Nullcline picture matches. (Fig 2)
4. (20 s) Inside and outside starts reach the same loop: a stable limit cycle, unlike Lotka–Volterra. (Fig 3)
5. (25 s) Bifurcation diagram: cycle born at exactly 90 with zero size, amplitude ∝ √(K − K_H), slope 0.507, period → 9.94 yr:
   supercritical Hopf. (Figs 5–6)
6. (10 s) Minima sink toward zero: paradox of enrichment. Whether the real data cycle depends on fitted σ = K/K_H.

## AI-acknowledgement log entry (draft, edit to match the official format)

- Tool: Claude (Anthropic), Opus 5.5
- Task assisted: design and implementation of the simulation layer and figures; reproduction of Joel's validation
  targets; executed notebook; LaTeX section; explanations of RK45, Hopf bifurcation and figure interpretation.
- Generated material: src/lynx_hare/simulation.py, src/lynx_hare/simulation_plots.py, scripts/rishi_simulations.py,
  scripts/build_rishi_notebook.py, notebooks/rishi_simulations.ipynb, tests/test_simulation.py,
  report/rishi_simulation_section.tex, report/rishi_main.tex, configs/simulations.json, figures, results/simulations/, this note.
- Manually checked: (fill in, e.g. re-ran the script and tests, compared the regime table with Joel's Table 2 by hand,
  inspected every figure)
