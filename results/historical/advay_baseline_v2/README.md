# Advay's least-squares baseline, v2 (reported version)

Produced by:

```text
python scripts/advay_fit_baseline.py --protocol v2 --output results/historical/advay_baseline_v2
python scripts/advay_compare_benchmark.py
```

- **Protocol** (declared before running): `docs/advay_baseline_protocol.md`.
- **Config:** `configs/historical.json`, used unchanged.
- **Data:** training file only. The test file has not been opened.
- **Manifest status:** `forecasts_frozen_unscored`, with hashes of every output.

## Files

| File | Contents |
|---|---|
| `forecast_{main,log_errors,fitted_initial}.csv` | Frozen 1916–1920 forecasts, `Year,Hare,Lynx`, thousands of pelts |
| `ode_*.csv` | Fitted trajectories 1900–1920 every 0.05 years (for plots) |
| `selected.json` | Selected fit per variant: parameters, σ, regime, bound hits, near-best spread, identifiability diagnostics |
| `starts.json` | Every start (240): starting point, final cost, parameters, σ, status |
| `parameters_for_team.json` | For Joel and Rishi: parameters, σ and regime per variant |
| `benchmark_comparison.json` | Comparison with Yash's matched benchmark (training cost, parameters, forecasts) |
| `figures/advay_baseline_fit.*`, `figures/advay_baseline_sigma.*` | Figures; EPS/PDF copies also in `report/graphs/` |

## Results (training data only)

| Variant | Training cost | r | K | a | b | e | m | σ = K/K_H | Regime |
|---|---|---|---|---|---|---|---|---|---|
| main | 0.0845 | 0.647 | 382 | 10.0* | 300* | 0.967 | 0.857 | **1.067** | limit cycle |
| log_errors | 0.903 | 0.520 | 197 | 7.17 | 300* | 1.80 | 1.15 | **0.550** | damped (stable coexistence) |
| fitted_initial | 0.0634 | 0.520 | 362 | 8.15 | 300* | 1.32 | 1.05 | **0.993** | damped (stable coexistence) |

\* = at the upper bound of the config box. Units: r and m per year; K and b in thousands of
hare pelts; a and e are effective coefficients in pelt units (O1). Fitted 1900 state in
`fitted_initial`: (37.1, 3.64), compared with the observed (30.0, 4.0).

### 1. Independent reproduction of Yash's benchmark

All three variants match `yash_matching_baseline_v2`:
- training costs agree to within 2 × 10⁻⁷ relative;
- parameters agree to about 10⁻⁴;
- forecasts differ by at most 0.002 thousand pelts.

The code and start design are different (log-scale optimisation, Latin hypercube starts),
so the least-squares optimum on this config is a well-defined computational result. It
doesn't depend on one implementation.

Within each variant, every start that came within 1% of the best cost found the **same**
parameters to 4 significant figures:
- `main`: 18 of 80 starts;
- `log_errors`: 42 of 78 (2 starts failed);
- `fitted_initial`: 16 of 80.

The other starts stopped in clearly worse local minima, 5–50 times the best cost (see the
σ figure). v1 used only log-scale starts and missed the `fitted_initial` optimum. That's
why v2 exists (protocol, amendment section).

### 2. The data can't pin down the saturating functional response

- b sits on its upper bound (300) in every variant, and a does too in `main`.
- The fitted b is about 4 times the largest hare count (77.4). So over the observed range
  aH/(b+H) ≈ (a/b)·H: predation is almost linear in hare numbers, and the Holling type II
  saturation is barely used.
- The scaled Jacobian shows a–b correlations of 0.996–0.998 and K–a and K–b correlations
  of 0.96–0.98. Approximate standard errors in log-parameters are about 1.1–2.3 for K, a
  and b, meaning these are uncertain by a factor of 3 or more.
- r, e and m are better determined (log-SE 0.1–0.4).
- What the data do pin down is roughly the low-density attack rate a/b ≈ 0.024–0.033 per
  year per (thousand lynx pelts).
- Because the optimum is on the box boundary, its location depends on the bounds. Yash
  saw this too when he widened the box.

### 3. Limit cycle or damped oscillation? The data don't decide

σ crosses 1 depending on the observation assumptions:
- 1.07 for `main`: just past Joel's Hopf threshold, so a stable limit cycle;
- 0.99 for a fitted 1900 state: just below, so a slowly damped oscillation;
- 0.55 for log errors: clearly damped.

All three reproduce the observed timing equally well:
- hare peaks fitted at 1902.5–1902.8 and 1912.6–1913.0 (observed 1903 and 1913);
- lynx peaks at about 1904.2–1904.5 and 1914.4–1914.6 (observed 1904 and 1915);
- a period of about 10 years and a lynx lag of about 1.6 years.

So, as Joel warned, two cycles of data can't tell a limit cycle from a slowly damped
oscillation. The report should not claim the data show a limit cycle.

### 4. Forecasts

Forecasts are frozen and **not yet scored**. Scoring happens in phase 4, in one script for
all methods.

## Figure captions

1. **advay_baseline_fit**. Least-squares fits of the Rosenzweig–MacArthur model to the
   1900–1915 pelt counts (markers), with the fitted model continued through 1920 (shaded,
   held out). Panels: main analysis (additive errors, observed 1900 state); log-error
   sensitivity; fitted-1900-state sensitivity. All three reproduce the timing of both
   cycles. They differ mainly in peak heights and in the 1916–1920 projection.
2. **advay_baseline_sigma**. Training cost (relative to the best) against σ = K/K_H for
   every converged start, one panel per variant. The dashed line is Joel's Hopf threshold
   σ = 1. The best fits sit close to σ = 1, on different sides depending on the variant.
   Starts with σ ≫ 1 converge to fits 5–50 times worse.
