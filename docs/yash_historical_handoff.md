# Yash: historical PINN results and handoff

Prepared 27 October 2026 using Advay's data PR #3, revision
`da99cea212198c6e995324e3cb8158c170891fa3`. Advay's data contribution is retained
separately in the project history from Yash's historical fitting work.

## Current status

Yash asked to make the modelling choices locally rather than wait for group approval.
The historical protocol is now explicit in `configs/historical.json`; it does not
claim other members' agreement. Thirteen PINN runs and 18 matched least-squares starts
have completed. Forecast and seed choices were frozen before final scoring.
The independent benchmark is not represented as Advay's completed baseline.
The source and results are project deliverables; the submission ZIP and local training
checkpoints are excluded from Git. Previous synthetic evidence is preserved.

Primary held-out RMSE (thousands of pelts): PINN hare 2.847, lynx 4.317;
least squares hare 3.072, lynx 3.043. This is a mixed comparison. Both methods must
use the same shared config for any future official comparison.
Several coefficients approach box limits and shift when the box expands; narrow
seed spread is not evidence of precise biological recovery.

## Answers to Advay's questions for Yash

- The proposed additive error measure is supported: each species' residual is divided
  by its maximum in the training file. For the proposed Stan split those maxima are
  77.4 and 59.4. No test-year scale is used.
- The new PINN supports fitting H0 and P0 within [0.5, 1.5] times the 1900 observations.
  The first observation remains in the data loss. The IC penalty ties the network's
  starting state to the fitted starting state; it does not constrain that state to be
  exactly the observed value in this sensitivity run.
- Every seed records the observed, fitted ODE and network initial states; network minus
  observed and network minus ODE differences are saved in original pelt units. For the
  main analysis, ODE forecasts still start at the observed initial state, even when the
  network's soft IC penalty leaves a small discrepancy.
- Both declared sensitivity variants are implemented: log observation residuals with
  observed initial state, and additive residuals with fitted initial state. They are
  separate changes, not a combined sensitivity. The physics loss stays on the existing
  training-scaled state derivatives in all variants.
- Each variant runs the declared seeds independently and selects the lowest weighted
  training objective within that variant. Objectives from different error models are
  not compared to select the primary method. All seeds and both sensitivities are kept.
- Export format is `Year,Hare,Lynx` for 1916-1920 in thousands of pelts. Forecasts integrate
  the frozen parameters from 1900 through 1920 using `model.solve`; neural-network
  extrapolation and restarts from test observations are not used.
- Per-seed parameter JSON includes all six values, fitted/fixed labels in the audit,
  initial states, bounds proximity, local sensitivity spectrum, and sigma when positive
  coexistence is feasible. Sigma is null otherwise, with a feasibility flag.

## Choices made for this iteration

The source is Advay's frozen Stan split. H and P are defined directly in thousands of
pelts without additional observation scales. All six coefficients, including e, are
fitted with positive independent box bounds and no coexistence constraint. The starting
vector is r=0.8, K=150, a=2, b=30, e=0.6, m=0.6. Primary bounds are r,m in [0.05,3],
K in [20,500], a in [0.05,10], b in [0.5,300], e in [0.02,5]. These are exploratory
numerical limits, not measured ecological ranges; no e<=1 restriction is imposed.

The solver is RK45, rtol=1e-8, atol=1e-10, max_step=0.1 for both methods and forecasts.
These settings are separate from Rishi's
tighter tolerances for long-run illustrative simulations.

`configs/historical.pending.json` preserves the earlier incomplete template for context;
it is superseded by `historical.json`. No synthetic K, b or e is fixed in the historical
fit. All six are fitted, without claiming identifiability from 16 pairs.
Before scoring, each box lower limit was halved and upper limit doubled for a
three-seed sensitivity (`historical_wider_bounds.json`); physics weight 100 was also
checked at seed 17 (`historical_physics100.json`). No variant replaced the primary
after test scores were available.

## Reproduce into a new output directory

```text
python scripts/run_historical_pinn.py --config configs/historical.json --output results/historical/reproduction_primary
```

The output directory must be new. The runner validates the training-file hash against
Advay's split record, and its only data-table input is `train_1900_1915.csv`.
It does not open the master or test table. The predeclared three variants and three
default seeds produce nine runs. Each run saves training loss, inferred parameters,
training-grid network states, ODE trajectories, separate-grid physics residuals,
initial-state differences and five-year forecasts. Checkpoints are local and ignored
by Git. Failed runs stop with an error; a partial output manifest remains `running`.

The runner verifies that its sources, config and training file did not change before
marking forecasts frozen. The final manifest records source, data, configuration and
output hashes and package versions. Completed outputs are marked
`forecasts_frozen_unscored`.

The completed primary output is `results/historical/yash_pinn_v1`.
Give Advay `predictions_for_advay.csv`, `predictions_log_errors.csv`,
`predictions_fitted_initial.csv`, `selected_runs.json`, the manifest and all run summaries.
Give Joel and Rishi `parameters_for_team.json`. An independent matching baseline is in
`results/historical/yash_matching_baseline_v2`, with six starts per variant. Its partial
v1 predecessor failed during JSON export and is retained as a failed run, not scored.
Advay's own baseline has not arrived in PR #3. He can independently reproduce this
benchmark or compare using the identical config rather than adopting different bounds.

## Validation and deliverables

The extension tests cover all-six-parameter physics gradients, log-error scaling,
bounded fitted ICs, deterministic fitting, IC discrepancy reporting, forbidden access
to master/test tables, source/config provenance, and independent ODE reconstruction
of exported forecasts. The end-to-end training smoke test uses a synthetic fixture;
it is not evidence of historical convergence or parameter accuracy.

All 42 tests passed. The historical notebook executed eight code cells and independently
reconstructed all 13 PINN forecasts. The verifier also checks the three selected baseline
forecasts, training-only seed selection, source/config/output hashes and all 16 scored
forecast files. Results are in `results/historical/yash_evaluation_v1`; no post-scoring
parameter or protocol tuning was performed. The report records the network/ODE gap,
IC differences, boundary hits, local sensitivity and all sensitivity scores.

Notebook: `notebooks/yash_historical_pinn.ipynb`. Report: `report/yash_historical_main.tex`
and `.pdf`, with `yash_historical_section.tex` for group integration. Five EPS graphs
and matching vector PDF companions are in `report/graphs/yash_historical_*`.
Historical presentation notes are in `presentation/yash_historical_notes.md`.
The older synthetic slide deck and submission ZIP remain separate. This work does not
claim to be the combined group notebook/report or the final group submission.
