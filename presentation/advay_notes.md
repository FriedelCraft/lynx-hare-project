# Advay: two-minute segment (data, comparison, limitations)

Last speaker, so this segment also closes the talk.

## Slide 1 – The data and the fit (about 50 seconds)

- Hudson's Bay Company pelt counts, 1900–1920, in thousands; Stan case-study series.
  **Trade counts, not censuses.** We model them as proportional to abundance (O1).
- Two cycles, hare peaks 1903 and 1913, lynx about 1–2 years behind.
  Train 1900–1915, test 1916–1920; the split was written down and checksummed first.
- Least squares: same model, bounds and solver as the PINN; 80 starts per variant
  because the fit has many local minima. Reproduces Yash's independent benchmark exactly.
- Two honest findings: the saturation constant b hits its bound (only a/b is pinned down),
  and σ = K/K_H lands at 1.07, 0.99 or 0.55 depending on assumptions, so **the data don't
  tell a limit cycle from a damped oscillation.**

Visual: `report/graphs/advay_baseline_fit.pdf` (or `advay_raw_series.pdf` for the data).

## Slide 2 – Held-out comparison and limitations (about 70 seconds)

| Main variant, RMSE | Hare | Lynx |
|---|---:|---:|
| Least squares | 3.07 | 3.04 |
| PINN-derived ODE | 2.85 | 4.32 |
| Hold the 1915 value | 7.38 | 37.16 |

- Scoring rules were committed and pushed before the test file was opened.
- Both methods predict the 1916–1920 crash and recovery, far better than trivial forecasts.
- Hare: similar. Lynx: least squares closer in all five years. Least squares also better
  or similar in both sensitivity checks.
- Limitations, one line each: five test points; trade counts with assumed constant
  catchability; two source compilations disagree; K, a, b not identifiable; results
  sensitive to the error model; closed two-species model.
- Closing line: the model captures the dominant short-term predator–prey feedback; five
  years of fur records can't tell us much more than that.

Visual: `report/graphs/advay_heldout_overlay.pdf`, plus the table above.

## Questions to rehearse

- Why least squares in log-parameter space, and why 80 starts? (Bounds span 600-fold;
  the first 40-start run missed a known lower minimum.)
- Isn't changing the starts after a run cheating? (Judged on training cost only, before
  any test score; both runs kept; documented in `docs/advay_baseline_protocol.md`.)
- Why is the PINN worse on lynx? (Its parameters fit training 1.9× worse than the LS
  optimum on the same objective; it cycles more strongly, σ ≈ 1.35.)
- What would make the forecast comparison meaningful? (Longer record, e.g. 1845–1935,
  with a new protected test period, declared in advance.)
