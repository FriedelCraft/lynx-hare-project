# Rishi → team handoffs (numerical simulations)

## What is in this branch

| Path | What |
|---|---|
| `configs/simulations.json` | Parameter configuration: illustrative parameters with units, regimes, solver tolerances, initial state, burn-ins, sweep grids |
| `src/lynx_hare/simulation.py` | RK45 wrapper with declared tolerances, attractor summary (range, period, lag), regime table, bifurcation sweep, amplitude law, Lotka–Volterra solver check |
| `src/lynx_hare/simulation_plots.py` | Publication figures (EPS-safe, no transparency) |
| `scripts/rishi_simulations.py` | Runs everything, checks Joel's targets, writes `results/simulations/` and `report/graphs/rishi_*` (about 9 min on one CPU) |
| `scripts/rishi_historical_placement.py` | Places every saved historical fit relative to the Hopf threshold; writes `results/simulations/historical/` and two report figures |
| `presentation/rishi_notes.md` | Three-slide, two-minute segment with likely questions |
| `scripts/build_rishi_notebook.py` | Builds and executes `notebooks/rishi_simulations.ipynb` from the two modules |
| `notebooks/rishi_simulations.ipynb` | Executed notebook: Markdown explanation, equations and algorithm before each code cell |
| `tests/test_simulation.py` | Solver accuracy, positivity, shared-RHS use, Joel's targets B/E/F, Hopf crossing, arrow directions, config, historical reconstruction |
| `report/rishi_simulation_section.tex` | Section for the report (`\input{rishi_simulation_section}` after Joel's section) |
| `report/rishi_main.tex`, `rishi_main.pdf` | Standalone build of Joel's and Rishi's sections together, so cross-references resolve |
| `report/graphs/rishi_*.{eps,pdf}` | Seven report figures, EPS plus PDF companion (same convention as Joel and Yash) |
| `report/references.bib` | One entry appended (`dormand1980`); nothing existing changed |

No existing model, PINN or baseline source or config was modified, so Yash's hash checks and Joel's tests are unaffected.
`requirements.txt` and `pyproject.toml` gained pandas (used by the notebook).
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
   with both nullclines, the hump peak, E* (filled stable, open unstable) and the direction field (arrows parallel to the
   flow, equal length). Oscillations decay below K_H and persist above.
3. **rishi_limit_cycle**. At K = 150, starts inside and outside the cycle converge to the same orbit; successive hare
   maxima converge to one value. The cycle is orbitally stable, unlike Lotka–Volterra's neutral orbits.
4. **rishi_eigenvalues** (notebook and `results/simulations/figures/` only, not in the report, because Joel's
   trace–determinant figure already shows it). Real and imaginary parts of the eigenvalues of J(E*) against K.
5. **rishi_bifurcation**. Post-transient max and min of H and P against K. The cycle is born at K_H with zero amplitude
   and its minima approach zero as K grows (paradox of enrichment).
6. **rishi_amplitude_period**. Log–log half-amplitude against K − K_H (slope 0.507, supercritical prediction 1/2) and
   the period tending to T0 = 2π/ω0.
7. **rishi_historical_sigma**. σ = K/K_H for every fitted parameter set (log scale). Filled: selected fit of each variant;
   open: other seeds/starts; crosses: least-squares local minima. PINN fits lie at σ ≈ 1.3–1.5, least-squares fits straddle 1.
8. **rishi_historical_bifurcation**. Bifurcation in K for the selected PINN and least-squares main fits, plotted against σ
   with the other fitted coefficients fixed; red line and bar: fitted σ and long-run hare range; grey band: 1900–1915 hare range.

## To Arnav (reply to his handoff)

- The solver keeps the dimensional interface: states (H, P), parameters r, K, a, b, e, m, time in years, shared `model.rhs`.
  No dimensionless solver is used, so no mapping is needed.
- Initial state for the simulations is (20, 5) at t = 0, Joel's convention for the illustrative regimes. The fitting
  protocol's initial state and forecast origin stay with Advay and Yash (below).

## Solver settings (corrected 27 October)

My first handoff recommended `simulation.integrate` for forecasts. That was wrong for the group protocol.

| Job | Function | Settings |
|---|---|---|
| Fitting (PINN and least squares) and 1900–1920 forecasts | `model.solve` | RK45, rtol 1e-8, atol 1e-10, max_step 0.1 yr (`configs/historical.json`) |
| Long-run simulations (thousands of years) in this section | `simulation.integrate` | RK45, rtol 1e-10, atol 1e-12, no step cap (`configs/simulations.json`) |

Both call the same `model.rhs`. Re-integrating Yash's selected PINN fit with `model.solve` reproduces his saved
1900–1920 path to 5e-12.

## Historical fits relative to the threshold (results/simulations/historical/)

All 13 PINN runs and 18 least-squares starts; the held-out test file is never opened.

| Selected fit | σ | Re λ (1/yr) | e-fold (yr) | First-century period, lag (yr) | On bounds |
|---|---|---|---|---|---|
| PINN main | 1.363 | +0.0079 | 127 | 10.7, 1.4 | K, b upper |
| PINN log errors | 1.343 | +0.0079 | 127 | 9.9, 1.3 | – |
| PINN fitted initial state | 1.347 | +0.0070 | 143 | 10.7, 1.4 | b upper |
| PINN wider bounds | 1.480 | +0.0049 | 204 | 10.5, 1.3 | b upper |
| PINN physics weight 100 | 1.364 | +0.0091 | 111 | 11.3, 1.4 | – |
| Least squares main | 1.067 | +0.0018 | 554 | 10.4, 1.6 | a, b upper |
| Least squares log errors | 0.550 | −0.0190 | 53 | 9.4, 2.0 | b upper |
| Least squares fitted initial state | 0.993 | −0.0002 | 5600 | 10.3, 1.7 | b upper |

For Joel's discussion: every good fit gives a ~10-year period and a 1.3–2-year lynx lag (Advay's plausibility check),
but σ ranges 0.55–1.48 across method, error model and bounds, b is on its upper bound in nearly every fit, and the
growth/decay rate is so small that 16 years cannot separate a damped oscillation from a limit cycle. Long-run cycle at
the selected fits: least squares H in [5.6, 85], period 10.8 yr; PINN H in [0.13, 247], period 18.5 yr.

## Run

```text
python -m pytest -q tests/test_simulation.py tests/test_stability.py
python scripts/rishi_simulations.py          # figures, tables, summary.json
python scripts/rishi_historical_placement.py # sigma for every saved fit, two figures
python scripts/build_rishi_notebook.py       # executed notebook
cd report && latexmk -pdf rishi_main.tex     # Joel + Rishi sections together
```

## Presentation and AI log

Talk material: `presentation/rishi_notes.md` (three slides, two minutes, likely questions).
AI-assistance entry: `docs/ai_acknowledgement.md`, section "Rishi". Rishi's own manual checks still need to be added there.
