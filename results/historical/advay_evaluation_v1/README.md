# Phase 4: held-out evaluation, 1916–1920 (Advay)

Produced by `python scripts/advay_score_heldout.py`, following the plan in
`docs/advay_scoring_plan.md`. The plan was committed and pushed (`308ff48`) before the test
file was opened, and the script was committed before it ran.

**One rerun:** the script was run twice. The second run only moved two figure legends that
covered data. `metrics.csv` was byte-identical across the two runs.

All 19 frozen forecasts were hash-checked before scoring.

**Cross-check:** every forecast that Yash also scored reproduces his
`yash_evaluation_v1/heldout_metrics.csv` exactly (max difference 0.0). My least-squares
forecasts score the same as his matched benchmark to the 2 decimals reported.

## Headline and sensitivity results (thousands of pelts)

| Variant | Method | Hare RMSE | Hare MAE | Lynx RMSE | Lynx MAE | Verdict (declared rule) |
|---|---|---|---|---|---|---|
| **Main (headline)** | Least squares | 3.07 | 2.59 | **3.04** | **2.56** | Hare: similar. Lynx: LS better (closer in 5/5 years) |
| | PINN-derived ODE (seed 17) | **2.85** | 2.59 | 4.32 | 4.05 | |
| Log errors | Least squares | **6.87** | **6.63** | **1.60** | **1.38** | Hare: LS better. Lynx: LS better (5/5) |
| | PINN-derived ODE (seed 29) | 18.35 | 14.29 | 10.03 | 8.97 | |
| Fitted 1900 state | Least squares | **2.25** | **2.08** | **3.24** | **2.71** | Hare: similar (LS closer in only 2/5 years). Lynx: LS better (5/5) |
| | PINN-derived ODE (seed 17) | 3.69 | 3.06 | 4.70 | 4.53 | |
| Reference | Persistence (1915 value) | 7.38 | 6.72 | 37.16 | 36.32 | |
| Reference | Training mean | 25.87 | 25.23 | 10.58 | 10.21 | |

The declared rule calls a method "better" only if it has both a smaller RMSE and a smaller
MAE, and is closer in at least 3 of the 5 years. Otherwise the result is "similar".
`metrics.csv` has all 19 forecasts plus the two references.
`yearly_errors.csv` has the signed error for each year.

## What the results show

1. **Both methods forecast the crash and recovery well.** In the main variant both predict
   the 1916–1920 lynx collapse and the hare recovery within about 3–4 thousand pelts.
   That's far better than the trivial forecasts: holding the 1915 lynx value gives
   RMSE 37, and the training mean gives about 11. So the fitted model's dynamics carry
   real information about the next half-cycle.
2. **The headline comparison is mixed and close.**
   - Hare: similar. PINN RMSE 2.85 vs 3.07, with identical MAE.
   - Lynx: least squares is better (3.04 vs 4.32) and closer in all 5 years.
   - The PINN's lynx curve falls too low after 1918 (observed 9.7–10.1, PINN about 3–5).
3. **The least-squares advantage holds in both sensitivity variants** and is large with
   log errors. There the PINN's training fit is poor: the 1913 hare and lynx peaks are
   misplaced (see `advay_heldout_variants`).
4. **Why the methods differ (training-only diagnostic, `pinn_training_fit.json`).** The
   selected PINN parameters, scored on the least-squares training objective, fit
   1900–1915 worse than the least-squares optimum:

   | Variant | PINN training cost ÷ LS optimum |
   |---|---|
   | main | 1.9× |
   | log errors | 3.4× |
   | fitted 1900 state | 1.9× |

   This is expected, since the PINN minimises a combined data, physics and initial-state
   loss. Its fitted dynamics are more strongly cycling (σ ≈ 1.34–1.36 in all three
   variants, against 0.55–1.07 for least squares). A better training fit didn't guarantee
   a better hare forecast in the main variant. With 5 test points, neither result is
   strong evidence.
5. **Stability is still undecided.** The PINN forecasts (σ ≈ 1.35) and the LS forecasts
   (σ ≈ 1) both match 1916–1920 reasonably, so the held-out years don't settle whether
   the system has a limit cycle either.
6. **The other PINN runs agree with the selected seeds:**
   - the three seeds per variant are within about 0.2 (main) and 0.8 (fitted state) of
     each other;
   - wider bounds: lynx RMSE about 4.1;
   - physics weight 100: hare 4.52, lynx 3.98.

   None of them changes the picture.

## Caveats

- 5 test points, roughly half a cycle, starting at the 1915 lynx peak.
- All errors are conditional on the Stan compilation. The tsibbledata series differs by
  more than these forecast errors in some years.
- Both methods share the same model, bounds and observation assumptions. The comparison is
  between fitting procedures, not between models.

## Figure captions

1. **advay_heldout_overlay**. Hare (top) and lynx (bottom) pelt counts with the
   least-squares (solid) and PINN-derived (dashed) Rosenzweig–MacArthur fits, main
   variant. Open circles are training data (1900–1915) and filled circles are held-out data
   (1916–1920, shaded). Both models were fitted to the training years only and integrated
   forward from 1900.
2. **advay_heldout_variants**. The same comparison for the main and the two sensitivity
   variants, 1910–1920. The log-error PINN fit misplaces the 1913 peaks, which explains its
   large held-out errors.
3. **advay_heldout_metrics**. Held-out RMSE and MAE for hare and lynx in the main variant,
   with persistence and training-mean reference forecasts. Both fitted models beat both
   references by a wide margin.
