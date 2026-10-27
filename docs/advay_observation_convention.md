# Observation convention for the historical pelt data (proposal)

Owner: Advay. Needs sign-off from **Arnav** (model and units) and **Yash** (PINN).
Status: **proposed, not yet agreed**. Last updated 27 October 2026.

This note states exactly how the numbers in `data/historical/pelts_1900_1920.csv` connect
to the model states H and P. Both fitting methods must use these rules unchanged. Any
change after fitting starts means rerunning both methods into a new results directory.

## 1. What a data point is

| Item | Convention |
|---|---|
| Hare_obs(Year), Lynx_obs(Year) | Thousands of pelts traded by the Hudson's Bay Company in that year, unchanged from the source |
| Model time | t = Year − 1900, in years (same as Arnav's units sheet and the existing code) |
| Timing | Each annual count is treated as a sample of the state at t = Year − 1900. In reality it is a total over a trapping season; that mismatch of up to a year is a stated limitation, not modelled |
| State order | H (hare), P (lynx) |

## 2. Pelts as abundance indices

**Assumption O1 (proportional index).** Pelts traded are proportional to abundance with
constant, unknown factors: Hare_obs ≈ c_H · N_hare and Lynx_obs ≈ c_P · N_lynx. We do not
estimate c_H or c_P. **The model states H and P are defined directly in pelt units**, so
H ≈ Hare_obs and P ≈ Lynx_obs, with no extra scale factor in either fitting method.

What follows from Arnav's unit-change result (`contributions/arnav/equations_and_units.md`):

- **r and m** (1/year) do not depend on c_H or c_P. They are the only fitted rates with a
  direct biological reading, and only if O1 holds.
- **K and b** are in thousands of hare pelts. **a** and **e** depend on c_H/c_P. These are
  effective coefficients in pelt units. We will **not** describe them as absolute carrying
  capacities, feeding rates or conversion efficiencies.
- **Dimensionless groups** (β = b/K, α = ea/r, δ = m/r, and σ = K/K_H) do not depend on
  c_H or c_P. Stability claims should be stated in terms of these.
- No absolute population sizes are claimed anywhere in the report.

**Consequence for a and e (Joel's note).** Joel's (P, a, e) → (cP, a/c, ec) symmetry makes
a and e impossible to separate only if a free lynx scale factor is fitted. Under O1 there is
no such factor, so a and e are separable in principle as effective coefficients. They may
still be **poorly determined in practice** from 16 points. The least-squares sensitivity
analysis and Yash's seeds will test this, and e may still need to be fixed for that reason.

**Why O1 is only an approximation.** Trapping effort, fur prices and the number of
reporting posts change over time. Lynx are easier to trap when hungry, which happens when
hares are scarce (Hewitt 1921). So c_H and c_P are probably not constant. This goes in
the limitations section.

## 3. Error model and scaling (must be identical in both methods)

- **Additive errors, constant spread within each species**, after dividing each species by
  its training maximum. Least-squares residual:
  `(model − obs) / scale`, with `scale = (77.4, 59.4)` = max of Hare and Lynx over
  1900–1915.
- This is **already the case in the code**: `baseline.py` divides residuals by `data.scale`,
  and `pinn.py` (`loss_parts`, data term) compares `model(t)` with `obs / scale`. Both use
  `TrainingData.scale`, which only sees training rows. I checked that `read_training` on
  the historical CSV returns 16 rows, scale (77.4, 59.4) and initial state (30.0, 4.0).
- Hare and lynx get equal weight after scaling. No log transform in the main fit.
- **Declared now, before any test-year scoring:** one sensitivity fit with log residuals
  `log(model) − log(obs)`, to check results don't hinge on the error model. Its outcome
  will be reported whichever way it goes.
- Scaling is numerical only. Fitted parameters and forecasts are converted back and
  reported in thousands of pelts.

## 4. Initial condition

**Current code:** the 1900 observation (30.0, 4.0) is the exact state at t = 0. Least
squares fixes it exactly; the PINN enforces it through a penalty with `ic_weight = 10`.

**Issue:** the 1900 counts are as noisy as any other year, and lynx at 4.0 is near a cycle
minimum, where small absolute errors are large relative errors. Every forecast starts from
this point, so treating it as exact matters.

**Proposal:**
- Main analysis: keep the current convention (initial state = 1900 observation) for both
  methods. This matches the existing contract and Yash's pipeline.
- Sensitivity, declared now: least squares with H0 and P0 fitted as two extra parameters,
  bounded to ±50% of the 1900 values. If Yash can add the same option to the PINN, both
  methods are compared on it as well. Otherwise it's reported as a baseline-only check.
- Yash: the PINN's soft IC penalty versus least squares' exact IC is a small mismatch.
  Please report how far the PINN's t = 0 state ends up from (30.0, 4.0).

## 5. Forecasts and evaluation

- Both methods integrate the frozen fitted model from t = 0 (1900) through t = 20 (1920),
  using the shared solver. There is no restart from any 1916–1920 value.
- Forecasts are delivered as `Year,Hare,Lynx` in thousands of pelts.
- Scoring: RMSE and MAE for hare and lynx separately, in thousands of pelts, on
  1916–1920 only.

## 6. Questions to confirm

| To | Question |
|---|---|
| Arnav | OK to define H and P directly in thousands of pelts (O1), with the interpretation limits in §2? Does the units sheet need an "observation model" line? |
| Yash | OK with the error model and scaling in §3 (unchanged from your code)? Can the PINN support fitting H0, P0 for the §4 sensitivity run? |
| Joel | With no lynx scale factor, do you agree a and e are separable in principle (§2)? Fix e anyway, or decide after the sensitivity results? |
| All | Any objection to the two declared sensitivity runs (log residuals; fitted initial state)? |
