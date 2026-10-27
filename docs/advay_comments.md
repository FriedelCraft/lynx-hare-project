# Advay → team: comments and open decisions

Branch `advay/phase2-protocol`. Last updated 27 October 2026 (after the phase 3
held-out evaluation).

| Phase 1 step | Status |
|---|---|
| 1. Source, cite, tidy CSV | Done, merged in PR #3 (`data/historical/`) |
| 2. Plots and data checks | Done, merged (`results/historical/data_checks/`) |
| 3. Observation convention | **Agreed** by Arnav and Yash (`docs/advay_observation_convention.md`) |
| 4. Train/test split files | Done, merged (`train_1900_1915.csv`, `test_1916_1920.csv`, `split.json`) |

| Phase | Status |
|---|---|
| 2. Protocol decisions | Settled de facto by `configs/historical.json` (see §0) |
| 3. Least-squares baseline | **Done:** `results/historical/advay_baseline_v2` (forecasts frozen, unscored) |
| 4. Scoring and comparison | **Done:** `results/historical/advay_evaluation_v1` (plan in `docs/advay_scoring_plan.md`) |
| 5. Report section, notebook, slides | Next |

## 0b. Phase 4 held-out results (details in `results/historical/advay_evaluation_v1/README.md`)

- **Scoring followed a pre-declared plan** (`docs/advay_scoring_plan.md`, pushed before the
  test file was opened). All 19 frozen forecasts were hash-checked. Yash's numbers are
  reproduced exactly.
- **Headline (main variant), RMSE in thousands of pelts:**
  - least squares: hare 3.07, lynx 3.04;
  - PINN: hare 2.85, lynx 4.32.

  Verdict by the declared rule: hare similar; lynx least squares better (closer in all 5
  years).
- **Sensitivity variants:** least squares better or similar in both. Log-error PINN: hare
  RMSE 18.4, because its training fit misplaces the 1913 peaks.
- **Both methods beat the trivial forecasts by a wide margin** (holding the 1915 value:
  lynx RMSE 37; training mean: about 11). The fitted dynamics genuinely predict the crash
  and recovery.
- **Yash:** your selected PINN parameters fit the training years 1.9–3.4× worse than the
  least-squares optimum on the same objective (`pinn_training_fit.json`), with σ ≈ 1.35 in
  all variants. Worth a line in your section on why the PINN doesn't reach the LS optimum.
- **Joel and Rishi:** the held-out years don't settle the stability question either. Fits
  with σ ≈ 1.0 and σ ≈ 1.35 both forecast 1916–1920 reasonably.
- **Report table:** `report/tables/advay_heldout_metrics.tex`. Figures:
  `report/graphs/advay_heldout_{overlay,variants,metrics}.{eps,pdf}`.

## 0a. Phase 3 results for the team (details in `results/historical/advay_baseline_v2/README.md`)

- **Independent reproduction:** my least-squares code is separate from Yash's and uses a
  different start design, but reaches the same optimum in all three variants (training
  cost within 2e-7, forecasts within 0.002 thousand pelts). Forecasts frozen; not scored
  yet.
- **Protocol amendment, declared openly:** my first declared run (v1, kept) missed the
  best `fitted_initial` fit because its log-scale starts rarely landed near the upper
  bounds. v2 adds 40 starts spread evenly on the ordinary scale per variant. The decision
  used training cost only. See `docs/advay_baseline_protocol.md`.
- **Joel and Rishi, σ = K/K_H:** main 1.067 (just above Hopf), fitted 1900 state 0.993
  (just below), log errors 0.550 (damped). All three match the observed peak timing
  (period about 10 years, lynx lag about 1.6 years). **The data can't decide between a
  limit cycle and a damped oscillation.** Please don't describe the fitted system as
  showing a limit cycle. Parameters are in `parameters_for_team.json`; Rishi, these are
  for the bifurcation diagram.
- **Everyone, the saturation isn't identified:** b hits its upper bound (300) in every
  variant, and a does too in the main fit. With b about 4× the largest hare count,
  predation is almost linear in H over the data, and a, b, K are each uncertain by a
  factor of 3 or more (a–b correlation 0.998). Only the ratio a/b ≈ 0.024–0.033 is well
  determined. Joel: this probably belongs in the sensitivity discussion; the fitted point
  depends on the box.

## 0. Phase 2 decisions: where things stand

The historical protocol is now `configs/historical.json`. Yash chose it for his runs, and
his PINN and matched least-squares forecasts were **frozen and then scored** on
1916–1920 (`results/historical/yash_evaluation_v1/`). So changing any of these choices
now would be a revision made after scoring, and would have to be labelled that way.
**The baseline will use this config unchanged.**

| Decision | Outcome | Who agreed |
|---|---|---|
| Data source | Stan compilation, frozen split v1; tsibbledata disagreement reported as a limitation | Arnav, Yash |
| Observation convention (O1) | H, P directly in thousands of pelts; no fitted scale factor; observed = state + error; annual totals as point samples | Arnav (units sheet updated), Yash |
| Error model and scaling | Additive; residuals divided by training maxima (77.4, 59.4) | Yash (already in code) |
| Fitted parameters | **All six** (r, K, a, b, e, m) fitted; e not fixed; no e ≤ 1 limit; no coexistence constraint | Yash's choice; **Joel to acknowledge** |
| Bounds | r, m ∈ [0.05, 3]; K ∈ [20, 500]; a ∈ [0.05, 10]; b ∈ [0.5, 300]; e ∈ [0.02, 5]; start r=0.8, K=150, a=2, b=30, e=0.6, m=0.6. Exploratory numerical limits, not ecological ranges | Yash's choice; **Joel to acknowledge** |
| Solver | `model.solve`: RK45, rtol 1e-8, atol 1e-10, max_step 0.1, for fitting **and** forecasting | Yash; **Rishi to acknowledge** (his tighter `simulation.integrate` stays for long-run simulations) |
| Initial state | Main: 1900 observation (30.0, 4.0). PINN uses a soft penalty; its main ODE forecasts still start at the observed state | Yash |
| Sensitivity runs | Log residuals; fitted H0, P0 within ±50%. Run as separate variants | Arnav, Yash (both implemented) |
| Evaluation | Train-only fitting; integrate from 1900; separate hare/lynx RMSE and MAE in thousands of pelts | Arnav, Yash |

**Still needed:** a short acknowledgement from Joel (all six fitted, bounds) and Rishi
(solver for fitting/forecasting). Neither blocks the baseline, since the config is fixed.

**What this changes for Advay's work:**
- Yash's `results/historical/yash_matching_baseline_v2` is an independent benchmark, not
  Advay's baseline (as Yash's manifest states). Advay's baseline will be a separate
  implementation on the same config, with its own multistart settings declared before it
  runs. It will be checked against Yash's benchmark, and must not be adjusted using the
  1916–1920 scores.
- Yash has already scored the forecasts. Advay will independently recompute all RMSE/MAE
  from the frozen forecast files and the test CSV, and build the final comparison
  figures and tables.

## 1. Historical dataset is in the repo

- File: `data/historical/pelts_1900_1920.csv`, columns exactly `Year,Hare,Lynx`, 21 rows
  (1900–1920), no missing values, no zeros.
- Units: **thousands of pelts traded by the Hudson's Bay Company per year**, copied
  unchanged from the source.
- Source: the CSV that comes with the Stan case study named in our work-distribution
  document (Carpenter, 2018). Chain of sources: HBC records → *Life: The Science of
  Biology* (Purves et al.) → Mahaffy (2010) lecture notes → Howard (2009) lecture notes
  → Stan. This is a secondary compilation; we have no original archival table.
- Provenance, file checksums and the full change log are in
  `data/historical/provenance.json`. The raw downloads are kept unmodified in
  `data/historical/raw/`.
- New citation keys in `report/references.bib`: `carpenter2018`, `howard2009`,
  `hewitt1921`, `tsibbledata_pelt`.

## 2. The two suggested sources disagree — please decide

Our document lists both the Stan series and tsibbledata `pelt`. Over 1900–1920 they are
different compilations:

| | Correlation with Stan series | Hare peaks | Lynx peaks |
|---|---|---|---|
| Stan (currently used) | — | 1903, 1913 | 1904, 1915 |
| tsibbledata | Hare 0.32, Lynx 0.81 | 1904, 1912 | 1905, 1914 |

Both show two cycles with lynx peaking about a year after hare, but the yearly values
differ a lot, especially for hare. I've used the Stan series because our protocol names
it, and I'll report the disagreement as a data limitation. **If anyone prefers
tsibbledata, say so before any fitting starts.** Switching later means redoing every
fit and forecast.

## 2b. Data check results (full details in `results/historical/data_checks/README.md`)

- Clean file: no missing values, no zeros, no outliers (robust check on year-to-year log
  growth, using training years only).
- Hare peaks in 1903 and 1913 (about a 10-year cycle). Lynx lags hare by 1–2 years; the
  cross-correlation peaks at a 2-year lag (r = 0.94).
- **Heads-up for everyone forecasting:** training ends exactly at the 1915 lynx peak, so
  the test years are the following crash. Both methods have to predict an unseen turning
  point. Expect large errors and don't over-read small differences between methods.
- Rishi and Joel: a fitted parameter set should reproduce roughly a 10-year period and a
  1–2 year lynx lag. That's a quick plausibility check before looking at σ.

## 3. Observation convention (Arnav, Yash)

Full proposal: **`docs/advay_observation_convention.md`** (status: proposed, awaiting
sign-off). Summary:

- H and P are defined directly in **thousands of pelts**. Pelts are assumed proportional
  to abundance with unknown constant factors (assumption O1). No observation scale factor
  is fitted in either method.
- Only r, m and the dimensionless groups (β, α, δ, σ) have a biological reading. K, b, a
  and e are effective coefficients in pelt units. No absolute population sizes are claimed.
- Error model: additive, residuals divided by the 1900–1915 maxima (77.4, 59.4), equal
  weight per species. **The code already does this in both `baseline.py` and `pinn.py`**,
  and I checked that the shared loader reads the historical CSV correctly.
- Initial state: 1900 observation (30.0, 4.0), as in the current code. Least squares fixes
  it exactly; the PINN uses a soft penalty. Yash: please report how far the PINN's t = 0
  state ends up from (30.0, 4.0).
- **Two sensitivity runs declared now, before any test scoring:** (1) log residuals,
  (2) H0 and P0 fitted as extra parameters (±50% bounds). Both will be reported whatever
  they show.
- Arnav, Yash, Joel: the specific questions are in §6 of that file.

## 4. Fixed vs. fitted parameters (Joel, Yash)

- a and e: Joel's (P, a, e) → (cP, a/c, ec) symmetry only bites if a lynx scale factor is
  fitted. Under the proposed convention (§3) there isn't one, so a and e are separable in
  principle, though perhaps poorly determined from 16 points. Proposal: try fitting both;
  fix e if the sensitivity analysis or Yash's seeds show they trade off. Whatever is
  chosen applies to **both** methods.
- The synthetic values K = 60, b = 20, e = 0.6 do **not** apply to real data. I need
  values or bounds for K and b on the pelt scale. Joel, can you suggest feasible ranges?
- Proposed bounds and starting guesses will go in a new `configs/historical.json`. I
  won't edit `configs/synthetic.json`.

## 5. Solver tolerances differ (Rishi, Yash)

- `model.solve` (used by Yash's saved runs): RK45, rtol 1e-8, atol 1e-10, max_step 0.1.
- `simulation.integrate` (Rishi's): RK45, rtol 1e-10, atol 1e-12.

The comparison is only fair if both fitting methods and the forecast use the same
settings. I suggest `model.solve` for fitting and forecasting, because the existing PINN
pipeline already uses it. Please agree on one before historical runs.

## 6. Evaluation protocol (everyone)

- Train on 1900–1915 (16 rows) and test on 1916–1920 (5 rows). **Split files are ready:**
  use `data/historical/train_1900_1915.csv` for all fitting (e.g.
  `scripts/fit_csv.py --csv data/historical/train_1900_1915.csv --kind historical ...`).
  `data/historical/test_1916_1920.csv` is for my final scoring only; please don't open it.
  Hashes are in `data/historical/split.json`, and `tests/test_historical_data.py` checks
  them. Nothing may use the test file except the final scoring script: no
  scaling, early stopping, choosing seeds or tuning loss weights on it.
- Forecasts integrate from the 1900 observation through 1920, with no restart from a
  held-out state.
- Metrics: RMSE and MAE, **separately for hare and lynx**, in thousands of pelts on the
  same years.
- Yash: please send forecasts as `Year,Hare,Lynx` for 1916–1920 from
  `scripts/fit_csv.py --kind historical`, written to a new output directory, plus the
  learned parameters and a log of every seed.

## 7. For Rishi and Joel: σ = K/K_H

I'll report σ = K/K_H for every least-squares start (and ask Yash for every PINN seed),
then send you the fitted parameters for the bifurcation diagram. With only about two
cycles in the training years, a damped oscillation may fit nearly as well as a limit
cycle. So "the data show a limit cycle" needs σ > 1 consistently across fits.

## 8. Limitations I'll cover in the report

Short test window (5 points, about half a cycle); trade counts rather than censuses
(trapping effort, prices, lynx easier to trap when hungry); disagreement between source
compilations; missing ecology (vegetation, other predators, spatial effects); parameters
that cannot be uniquely identified; sensitivity to the observation model; the
proportional-index assumption O1 (catchability probably not constant); annual season
totals treated as point-in-time samples; a noisy 1900 observation used as the exact
initial state; the test window starting right after the 1915 lynx peak.
