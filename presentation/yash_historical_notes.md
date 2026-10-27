# Yash: two-minute historical results segment

Use the historical graphs below, replacing the synthetic numerical examples in the
older slide deck when the group assembles its final presentation.

## Slide 1 - Inverse PINN and real-data protocol (about 55 seconds)

- Fit all six positive effective coefficients in the shared Rosenzweig-MacArthur model.
- Stan pelt indices, thousands of pelts: train 1900-1915, freeze forecasts, score 1916-1920.
- Three-layer, 48-unit tanh network; positive outputs; automatic differentiation for the ODE residual.
- Loss = training-max-scaled data error + 10 x physics error + 10 x initial-state error.
- Three seeds, Adam then L-BFGS; select by training objective. Forecast by ODE integration from 1900.

Visual: `report/graphs/yash_historical_fit.pdf`.
Explain that the network and integrated ODE can differ because physics is a soft penalty.
The main network initial-state error is approximately (+0.101,-0.007) thousand pelts;
the ODE still starts at the observed (30,4).

## Slide 2 - Mixed forecast result and sensitivity (about 65 seconds)

| Primary model | Hare RMSE | Lynx RMSE |
|---|---:|---:|
| PINN-derived ODE | 2.847 | 4.317 |
| Matched least squares | 3.072 | 3.043 |

Units: thousands of pelts; five held-out years. Slightly better hare RMSE, worse lynx
RMSE: no overall PINN superiority claim. The benchmark is an independent matched
calculation for Yash's contribution, not a claim that Advay completed his own baseline.

Visual: `report/graphs/yash_historical_forecast.pdf`; optionally show
`report/graphs/yash_historical_bounds.pdf` as backup.
Say: "Changing the bounds moves K and b towards the new limits. Similar seeds do not
mean precise biological estimates. We kept the log-error, fitted-initial-state,
wider-bound and physics-weight sensitivities, including worse outcomes."

The selected fitted ODE has sigma about 1.36, but this is conditional on the model,
data convention and bounds. It does not prove an ecological limit cycle from two
cycles of pelt returns. Main limitations: abundance indices, source disagreement,
short test window, soft-physics discrepancy and parameter sensitivity.
