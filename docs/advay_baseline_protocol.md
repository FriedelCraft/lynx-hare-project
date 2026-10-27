# Advay's least-squares baseline: declared protocol

Declared 27 October 2026, **before the first run**, and committed on its own so the git
history shows that it came first. Yash's headline held-out scores were already public
(`docs/yash_historical_handoff.md`). None of the choices below depend on them, and none
will be changed after the baseline is scored.

## Fixed by the shared contract (not Advay's choice)

All of these come from `configs/historical.json`, used unchanged:
- **Fitted parameters:** all six (r, K, a, b, e, m), within the config's bounds.
- **Solver:** `model.solve`, RK45 with rtol 1e-8, atol 1e-10, max_step 0.1.
- **Data:** training file `data/historical/train_1900_1915.csv`, hash-checked against
  `split.json`.
- **Error models:**
  - additive, with residuals divided by the training maxima (77.4, 59.4);
  - log residuals for the `log_errors` variant.
- **Initial state:** the 1900 observation, except in `fitted_initial`, where H0 and P0 are
  fitted within [0.5, 1.5] × the observed values.
- **Forecasts:** frozen parameters integrated from 1900 to 1920; 1916–1920 exported as
  `Year,Hare,Lynx` in thousands of pelts. No restart from test values.

## Advay's own choices

| Choice | Value | Reason |
|---|---|---|
| Parameterisation | Optimise x = log θ with log bounds | Bounds span up to 600-fold (b: 0.5–300), so log steps treat small and large values evenly. The feasible set is unchanged |
| Starts per variant | 40 | 6–8 unknowns and a multimodal cost (one test start from the config guess ended at a poor optimum against four bounds). About 5 s per start |
| Start design | Start 0 = config initial guess; starts 1–39 = Latin hypercube in log space | Even coverage of the whole box. Different from Yash's uniform draws, which is useful for an independent check |
| Random seed | 20261027 (+0 / +1 / +2 for the three variants) | Reproducible |
| Optimiser | SciPy `least_squares`, trf, `x_scale="jac"`, `diff_step=1e-4`, `max_nfev=2000`, ftol = xtol = gtol = 1e-10 | `diff_step` well above the solver's 1e-8 tolerance, so finite-difference derivatives aren't dominated by solver noise |
| Failed solves | Residual set to 1000 (scaled); start excluded from selection | — |
| Selection | Lowest training cost per variant; `main` is the primary result | Training data only |
| Reported for every start | Cost, parameters, σ = K/K_H, regime, bound hits | Joel's and Rishi's request; shows how stable the optimum is |
| Reported at the selected fit | Starts within 1% of the best cost, their parameter and σ ranges, Jacobian singular values, approximate log-parameter standard errors and strongest correlations | Local identifiability diagnostics, not confidence intervals |

## What happens after the run

1. Forecasts are frozen (manifest status `forecasts_frozen_unscored`, with file hashes).
2. Compare against Yash's matched benchmark (`results/historical/yash_matching_baseline_v2`)
   on parameters, training cost and forecast values. This doesn't use test data.
3. Only then, in phase 4, open the test file and score every method in one script.

Run with:

```text
python scripts/advay_fit_baseline.py --output results/historical/advay_baseline_v1
```
