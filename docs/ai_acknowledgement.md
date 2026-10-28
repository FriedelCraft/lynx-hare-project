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

## Advay work package, 27–28 October 2026

| Tool | Task assisted | Generated material | Checks actually performed |
|---|---|---|---|
| Claude Code (Anthropic, Claude Opus 5.5) | Read the work distribution; locate and document the historical data; implement the data checks, train/test split, least-squares baseline, scoring and comparison; write team notes, protocols, report section, notebook and talk notes | `data/historical/` (CSV, provenance, split), `scripts/advay_*.py`, `scripts/build_advay_notebook.py`, `src/lynx_hare/historical_ls.py`, `tests/test_historical_{data,ls}.py`, `results/historical/{data_checks,advay_baseline_v1,advay_baseline_v2,advay_evaluation_v1}/`, `report/advay_*.tex`, `report/tables/advay_heldout_metrics.tex`, `report/graphs/advay_*`, `notebooks/advay_data_validation.ipynb`, `docs/advay_*.md`, `presentation/advay_notes.md` | Data values compared against both downloaded sources; 9 automated tests (split integrity, checksums, residual scaling, bounds, recovery of known parameters from simulated data); least-squares optimum reproduced Yash's independent benchmark in all three variants; held-out scores reproduced Yash's evaluation exactly; notebook executed end to end; every figure inspected visually and re-drawn where labels covered data |
| SciPy `solve_ivp` and `least_squares` | ODE integration and bounded nonlinear least squares | Fitted parameters, forecasts, Jacobian diagnostics | Solver settings as in the shared config; known-parameter recovery test |

Protocol decisions (baseline starts, the v2 amendment and the scoring plan) were committed
before the runs and data they govern; the git history records the order. The LaTeX section
could not be compiled in the assistant's environment (no TeX installation); compilation and
a visual check of the PDF are still needed. The checks above were run by the assistant.
Advay should add his own manual checks after reading and rerunning the work, and confirm the
course's required acknowledgement wording before submission.

## Rishi: numerical simulations (26-27 October 2026)

| Tool | Task assisted | Generated material | Checks actually performed |
|---|---|---|---|
| Claude (Anthropic), Opus 5.5 | Simulation layer and figures; reproduction of Joel's validation targets; executed notebook; LaTeX section; historical sigma placement; presentation notes; explanations of RK45, Hopf bifurcation and the figures | `src/lynx_hare/simulation.py`, `simulation_plots.py`, `configs/simulations.json`, `scripts/rishi_simulations.py`, `scripts/rishi_historical_placement.py`, `scripts/build_rishi_notebook.py`, `notebooks/rishi_simulations.ipynb`, `tests/test_simulation.py`, `report/rishi_simulation_section.tex`, `report/rishi_main.tex`, `report/graphs/rishi_*`, `results/simulations/`, `presentation/rishi_notes.md`, `docs/rishi_simulation_handoff.md` | Automated tests (solver accuracy, positivity, shared RHS, Joel's targets, Hopf crossing, arrow directions, config consistency); all six of Joel's regimes reproduced; reconstruction of Yash's selected 1900-1920 path with model.solve (difference 5e-12); sigma recomputed for every saved fit and matched to Yash's reported values; notebook executed end to end; report compiled and figures inspected |
| SciPy solve_ivp | RK45 integration | All trajectories and long-run summaries | Lotka-Volterra invariant drift 4e-10; 100x tighter tolerances change results by 8e-10 |

The checks above were run by the assistant. A phase-portrait arrow error in the first version
(arrow directions skewed by unequal axis ranges) was found in group review and corrected on
27 October; a test now checks every arrow against the vector field.

**Rishi's own checks at submission (27 October):** Rishi worked through the model and theory
behind this section with the assistant's step-by-step explanations: the Lotka-Volterra model and its
conserved quantity, the Rosenzweig-MacArthur equilibria, Jacobian and trace-determinant stability,
the Hopf threshold K_H = b + 2H*, and the RK45 method. He reviewed the summary of results and the
group plan's checklist for his section.


## Yash: final integration, 28 October 2026

OpenAI Codex reviewed and integrated Arnav's final main-branch contribution, Advay's
PRs #4/#6, and Rishi's PR #5. It preserved both acknowledgement entries during the
merge; built a combined notebook with isolated author namespaces; compiled the
combined report and Advay's standalone report; repaired table/path layout; and
qualified the theory integration copy concerning equilibrium orbits and observation
scales. Original experimental fits, forecasts and selection rules were not changed.

Codex Artifact Tool generated Yash's two editable historical slides and the ten-slide
group deck with two slides per member and speaker notes. Both decks passed export,
layout, font, import and chart/workbook checks. Every final slide was rendered and
visually inspected by the assistant. All 37 combined-report pages, five updated Yash
pages and eight Advay pages were rendered and inspected. These checks do not claim
that Microsoft PowerPoint was opened or that a member personally reviewed the work.

The assistant ran 53 passing automated tests and executed all 39 code cells of the
combined notebook. Its default mode runs illustrative simulations and live
training-only least-squares demonstrations, reconstructs frozen PINN evidence and
recomputes historical sigma values. The full long-run historical simulation replay
is opt-in; PINN training and the 240-start baseline were not repeated during assembly.
The packaging audit now follows active TeX inputs and validates every referenced
EPS/vector-PDF pair, data provenance and notebook execution. Final archive validation
is recorded separately in results/integration/verification.json.

Yash and each teammate should record only manual checks actually performed. The ZIP
is prepared locally for the professor's required email submission; no email is sent
by this workflow.
