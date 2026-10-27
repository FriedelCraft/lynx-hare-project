# Historical data checks (Advay, phase 1 step 2)

Produced by `python scripts/advay_data_checks.py`. Numbers are in `summary.json`. Figures
are in `figures/` (PNG, EPS, PDF), and EPS/PDF copies are in `report/graphs/advay_*`.

Any statistic that could inform a modelling choice is computed from the **1900–1915
training rows only**. The 1916–1920 rows are plotted, shaded and labelled as held out, but
they are not used in any calculation.

## Findings

| Check | Result |
|---|---|
| Format | 21 consecutive years, no duplicates, no missing values, no zeros or negatives |
| Training ranges (thousands of pelts) | Hare 18.1–77.4 (mean 40.1); Lynx 4.0–59.4 (mean 21.9) |
| Dynamic range (max/min) | Hare 4.3×, Lynx 14.9× |
| Outliers | None. Robust z of year-to-year log growth: max 2.94 for hare (the 1903→1904 crash) and 2.17 for lynx, against a threshold of 3.5 |
| Hare peaks | 1903 and 1913: a 10-year spacing, so roughly one cycle per decade |
| Lynx peaks | 1904 and 1915 (1915 is the last training year, so the true peak may be later) |
| Lag | Peak-to-peak 1 year (1903→1904) and 2 years (1913→1915). The cross-correlation of Hare(t) with Lynx(t+k) peaks at k = 2 (r = 0.94), with r = 0.76 at k = 1 |
| Phase plane | Counter-clockwise loops (hare rises, then lynx rises, then hare falls, then lynx falls), as predator–prey models predict |

## What this implies for fitting

- **No cleaning needed.** No values are missing, imputed or removed.
- **Normalise each species by its training maximum** (Hare 77.4, Lynx 59.4), as the current
  model contract already says. Hare counts are about twice lynx counts on average, so an
  unscaled least-squares fit would mostly fit hare.
- **No log transform for the main fit.** All values are positive, and the protocol's
  RMSE/MAE are in original units. Lynx varies about 15-fold, so errors at low counts are
  small in absolute terms. A log-residual fit is worth running as a sensitivity check.
- **The split falls at an awkward point.** Training ends at the 1915 lynx peak, and the
  test years are the next crash and the start of recovery. The model must predict a
  turning point it has never seen in that cycle, from about two cycles of training data.
- The 1–2 year lag and 10-year period give a qualitative check for any fitted parameter
  set: the fitted model should reproduce both.

## Figure captions

1. **advay_raw_series**. Left: annual Hudson's Bay Company hare and lynx pelt counts,
   1900–1920 (thousands); the shaded band marks the held-out years. Right: the same data
   in the hare–lynx plane, with the training years as a solid line and the held-out years
   dashed. The counter-clockwise loops show lynx counts rising after hare counts.
2. **advay_lag**. Correlation between hare counts in year t and lynx counts in year t+k over
   the training years. The peak at k = 2 (r = 0.94) shows lynx trailing hare by one to two
   years.
3. **advay_source_comparison**. The Stan case-study series used here (solid) against the
   tsibbledata `pelt` compilation (dashed) for the same years. Both show two cycles, but
   yearly values differ, especially for hare (r = 0.32). The choice of source is itself a
   source of uncertainty.
