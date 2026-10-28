# Phase 4 scoring plan (Advay)

Declared 28 October 2026, **before `data/historical/test_1916_1920.csv` is opened by any of
Advay's code**, and committed and pushed on its own. Yash's evaluation
(`results/historical/yash_evaluation_v1`) already exists and his headline numbers are
public. This plan fixes what is compared and how it is described, so that the choice of
comparison can't depend on the scores.

## 1. Forecasts scored

Every file is checked against its recorded SHA-256 before scoring. Any mismatch stops the
script.

| Label | Method | File | Recorded in |
|---|---|---|---|
| LS-Advay / main, log_errors, fitted_initial | Advay's least squares (v2) | `advay_baseline_v2/forecast_{variant}.csv` | that folder's `manifest.json` |
| LS-Yash / main, log_errors, fitted_initial | Yash's matched least-squares benchmark | `yash_matching_baseline_v2/forecast_{variant}.csv` | that folder's `manifest.json` |
| PINN / {variant} seed {17, 29, 43} | Yash's PINN-derived ODE forecasts, 9 runs | `yash_pinn_v1/runs/{variant}_seed{s}/forecast.csv` | `yash_evaluation_v1/forecast_freeze.json` |
| PINN-wider / main seed {17, 29, 43} | PINN, wider bounds | `yash_pinn_wider_v1/runs/main_seed{s}/forecast.csv` | same |
| PINN-physics100 / main seed 17 | PINN, physics weight 100 | `yash_pinn_physics100_v1/runs/main_seed17/forecast.csv` | same |

Not scored: `advay_baseline_v1`. It's superseded by v2 under the declared amendment; its
`main` and `log_errors` forecasts equal v2's to within 0.003.

**Reference forecasts**, built from training data only, to show whether either model beats
a trivial forecast:
- **Persistence:** the 1915 value held constant (Hare 19.5, Lynx 51.1).
- **Training mean:** the 1900–1915 mean held constant (Hare 40.09, Lynx 21.85).

## 2. Comparisons and their status

- **Headline comparison (declared now):** LS-Advay main vs PINN main seed 17. Seed 17 is
  the seed Yash selected by training loss before scoring.
- **Sensitivity comparisons:** the same pairing for `log_errors` (PINN seed 29) and
  `fitted_initial` (PINN seed 17), again using Yash's pre-scoring seed selection.
- **Reported in full, not headline:** all other PINN seeds, wider bounds, physics100,
  LS-Yash, and the two reference forecasts.
- No method, seed or variant is chosen or re-ranked using test errors.

## 3. Metrics

- **Years:** 1916–1920 only, all five, equally weighted. Units: thousands of pelts.
- **Per species, never combined:** RMSE and MAE for hare and for lynx.
- **Also reported:** the signed error per year (forecast − observed) for the headline and
  sensitivity forecasts.
- **Interpretation rule (declared now):** with 5 test points, about half a cycle starting at
  the 1915 lynx peak, a difference between methods is described as "similar" unless one
  method's error is smaller for **both** RMSE and MAE **and** for most of the five years.
  No significance test is claimed.
- **Cross-check:** every forecast that Yash also scored must reproduce his
  `heldout_metrics.csv` to within 1e-9. Any difference is reported, not hidden.

## 4. Outputs

All written to a new folder, `results/historical/advay_evaluation_v1/`, which the script
refuses to overwrite:
- `metrics.csv` (every scored forecast), `yearly_errors.csv`, `crosscheck_yash.json`,
  and `manifest.json` with input hashes;
- figures, also copied as EPS/PDF to `report/graphs/`:
  - `advay_heldout_overlay`: training data, test data and both methods' fitted
    trajectories 1900–1920, one panel per species, main variant;
  - `advay_heldout_variants`: the same for the three variants;
  - `advay_heldout_metrics`: grouped bars of RMSE and MAE per species, including the
    reference forecasts;
- `report/tables/advay_heldout_metrics.tex`: the headline and sensitivity table.
