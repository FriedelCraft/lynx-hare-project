# AI assistance log

## Yash work package prepared on 26 October 2026

| Tool | Task assisted | Generated material | Checks actually performed |
|---|---|---|---|
| OpenAI Codex | Implement and document the inverse PINN using the supplied work distribution | Python source, tests, synthetic generator, configuration, experiment pipeline, executed notebook, figures, tables, LaTeX section and presentation notes | Automated model/gradient/solver/leakage/reproducibility tests; actual CPU training; CSV and figure inspection; successful report compilation |
| Codex Artifact Tool | Prepare Yash's presentation segment | Two editable slides with speaker notes and a native comparison chart | Slide preview inspection, package/layout checks and chart/workbook consistency validation |
| PyTorch autograd and optimizers | Compute derivatives and fit network/parameters | Numerical gradients, training logs and learned parameters | NumPy/Torch RHS agreement, finite-difference chain-rule check, unknown-parameter gradients and deterministic repeated small fit |
| SciPy solve_ivp and least_squares | Generate synthetic trajectories, forecast and build a provisional comparison | Synthetic CSVs, ODE predictions and matching baseline estimates | Tighter-tolerance solver comparison, positivity, known-equilibrium check and noiseless recovery |

The checks above were run by the coding assistant. They do not assert that Yash has
personally reviewed or independently reproduced the derivations and code. Before
submission, Yash should run the notebook, explain each loss term and chain rule, inspect
the outputs, and record his own manual checks here. Any additional AI tools used by
teammates belong in their own logs. Confirm the course's required acknowledgement wording
and grading rules before submitting this log.

All included data are synthetic. No historical measurements, teammate contributions,
manual checks by teammates or successful real-data forecasts have been invented.
