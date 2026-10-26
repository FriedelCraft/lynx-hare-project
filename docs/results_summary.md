# Measured synthetic results

The complete reference run contains **13 PINN fits** on one CPU thread.
Training took 213.7 seconds in total, excluding imports, baseline fitting,
plotting and notebook execution. The exact runtime versions and source hashes are in
`results/synthetic/manifest.json`. These are synthetic index trajectories, not historical data.

## Parameter recovery

All primary fits estimate r, a and m; K=60, b=20 and e=0.6 are fixed correctly for this
controlled experiment. Maximum absolute relative errors across the three default seeds
and the three estimated parameters were:

| Training observations | Maximum error |
|---|---:|
| 61 clean quarterly observations | 0.0057% |
| 61 quarterly observations with 3% noise | 0.796% |
| 16 annual observations with 3% noise | 0.358% |

This comparison holds the noise seed fixed within each case. It does not show that
annual observations are generally more informative than quarterly observations; the
finite noise realizations differ and the three rates are conditionally identifiable.

The selected default annual run is **annual_noisy_seed17**, chosen using the smallest
weighted training objective. Its estimates are r=1.00353118, a=1.99769981 and
m=0.49866347. All seeds and sensitivity variants are retained in `parameter_recovery.csv`.

## Held-out ODE forecasts

These scores use five years labelled 1916–1920. Parameters and the seed choice were
frozen before scoring. The ODE is integrated from 1900 using the same initial state and
RK45 settings for both methods. Values are in arbitrary synthetic abundance-index units.

| Method | Evaluation target | Hare RMSE | Lynx RMSE | Hare MAE | Lynx MAE |
|---|---|---:|---:|---:|---:|
| PINN-derived ODE | noisy observations | 0.33189 | 0.38624 | 0.27799 | 0.24630 |
| PINN-derived ODE | latent truth | 0.05237 | 0.08202 | 0.04745 | 0.07126 |
| least_squares | noisy observations | 0.29617 | 0.44120 | 0.25099 | 0.30352 |
| least_squares | latent truth | 0.22365 | 0.15703 | 0.19099 | 0.14861 |

Against noisy observations, least squares has the lower hare error and the selected
PINN-derived ODE has the lower lynx error. Against latent truth the selected PINN-derived
ODE is closer for both species in this realization. This mixed result is not evidence
of general superiority. The experiment favors the mechanistic model because the same
equations generated the observations, three constants are known, and the initial state
is exact. No claim about historical predictive accuracy follows.

## Sensitivity and identifiability

The prespecified physics weights 1 and 100 and initial-guess factors 0.6 and 1.4 produce
the trajectories in `figures/sensitivity.png`. This is a diagnostic sweep, not a test-based
search for the best configuration. The local sensitivity condition number rises from
3.74 when varying r,a,m to
60.24 when all six parameters are varied
locally. That indicates more weakly constrained directions in the larger local problem;
it does not prove structural non-identifiability or establish six-parameter recovery.

The independent residual grid and network/ODE consistency figures check two failure
modes: satisfying physics only at the training grid and fitting observations with a
network whose inferred ODE follows a different trajectory. Neither diagnostic is a
formal error bound or a substitute for held-out validation.

## Practical limits

Three optimizer seeds on one noise draw do not quantify observation uncertainty. Bounds,
loss weights and fixed constants are provisional. The forecast contains only five test
points per species. The synthetic system omits ecology and the pelt-trading observation
mechanism. Real fitting requires the team's frozen equations, units, feasibility ranges,
data provenance and evaluation protocol. See `docs/team_handoff.md`.
