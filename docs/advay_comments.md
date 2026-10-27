# Advay → team: comments and open decisions

Branch `advay/data-validation`. Last updated 27 October 2026.

| Phase 1 step | Status |
|---|---|
| 1. Source, cite, tidy CSV | Done (`data/historical/`) |
| 2. Plots and data checks | Done (`results/historical/data_checks/`) |
| 3. Observation convention | Proposed (`docs/advay_observation_convention.md`), **awaiting Arnav/Yash/Joel** |
| 4. Train/test split files | Done (`data/historical/train_1900_1915.csv`, `test_1916_1920.csv`, `split.json`) |

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
