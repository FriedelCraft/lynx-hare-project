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

The 26 October experiment above uses synthetic data. Historical work added on
27 October is recorded separately below. Manual checks by Yash or teammates are not claimed.

## Historical extension prepared on 27 October 2026

OpenAI Codex helped choose and document an explicit historical protocol after Yash
asked to make the choices locally. It implemented historical PINN sensitivities,
an independent matched least-squares benchmark, freezing/scoring and verification
scripts, the executed historical notebook, EPS/PDF/PNG figures and LaTeX/PDF report.
The dataset and provenance were supplied by Advay in PR #3; the assistant did not
collect new historical records or obtain approval from other members.

Checks actually performed by the assistant: 42 automated tests; 13 historical PINN
runs; 18 least-squares starts; source/data/configuration and frozen-output hash checks;
independent reconstruction of all exported forecasts and recomputation of held-out
metrics; successful execution of all eight historical notebook code cells; report
compilation and visual inspection of every final page. A first baseline export failed
because a NumPy boolean was not JSON-serializable; that partial v1 folder is retained,
and the corrected complete run is v2. No post-scoring retuning was performed.

Historical bounds and initial guesses are modelling choices in pelt units, not
measured biological values. Boundary sensitivity and worse outcomes were retained.
Yash should add his own manual checks after reading and reproducing the work.
