# Lynx Hare Project

MAC F314 Mathematical Modelling: Canadian lynx and snowshoe hare dynamics.
This repository contains **Yash's inverse physics-informed neural network (PINN) work package**,
**Joel's stability analysis**, **Arnav's model formulation**, **Rishi's simulations**,
and **Advay's independent historical baseline and evaluation**.
Synthetic controlled recovery experiments and historical pelt-index experiments are
kept separately. Historical counts are abundance indices, not animal censuses.

## Combined deliverables (28 October 2026)

- [Executed group notebook](notebooks/group_project.ipynb): all five credited contributions,
  with isolated namespaces and 39 executable cells.
- [Combined report PDF](report/group_main.pdf) and [main LaTeX source](report/group_main.tex).
- [Ten-slide group presentation](presentation/group_presentation.pptx), two slides per member,
  and [Yash's historical segment](presentation/yash_historical_slides.pptx).
- [Current completion record](docs/completion_status_2026-10-28.md), including reproduction modes.

Install `requirements.txt`, then `pip install -e . --no-deps`. Run
`python scripts/execute_notebook.py --notebook notebooks/group_project.ipynb`.
The default notebook replays illustrative simulations and training-only LS demos,
audits frozen PINN outputs, and checks historical sigma. Set `FULL_LONG_RUN_REPLAY=True`
only to repeat the expensive historical simulations over thousands of years.
Build the professor-format ZIP with `python scripts/build_submission.py --extract-check`.
It is written outside Git; no email is sent. Use `--scope synthetic` for the older
controlled component, or `--scope historical` for Yash's standalone historical component.

## Historical results (27 October 2026)

Start with [Yash's executed historical notebook](notebooks/yash_historical_pinn.ipynb),
[historical report PDF](report/yash_historical_main.pdf),
[LaTeX source](report/yash_historical_main.tex), or
[handoff and protocol](docs/yash_historical_handoff.md).
There are 13 PINN runs and an independent matching benchmark with 18 least-squares starts.
The primary PINN's held-out hare/lynx RMSE is 2.847/4.317 thousand pelts; matching
least squares gives 3.072/3.043. The comparison is mixed, and several parameters depend
strongly on numerical bounds. These choices were made by Yash with assistance;
approval or completion of other members' fitting work is not implied.
Training uses only 1900-1915; forecast choices were frozen before scoring 1916-1920.
The common comparison config is [historical.json](configs/historical.json).
Advay has independently reproduced the matching baseline and completed evaluation;
the combined deliverables above incorporate that contribution.

## What is included

- A PyTorch inverse PINN with positive states, bounded positive unknown parameters,
  automatic ODE residuals, reproducible Adam and L-BFGS training, logging and checkpoints.
- Synthetic clean and noisy recovery experiments over three training seeds.
- A matching RK45 least-squares benchmark, five-year ODE forecasts, separate hare/lynx
  RMSE and MAE, loss-weight and initial-guess sensitivity, and a local identifiability diagnostic.
- An executed explanatory notebook, PNG/EPS figures, a LaTeX report section, two-minute
  presentation deck with speaker notes, handoff CSVs, tests and an AI assistance log.

For the separate synthetic experiment, start with [the notebook](notebooks/yash_pinn.ipynb), [measured results](docs/results_summary.md),
or [the mathematical method](docs/method.md).

## Teammate quick start

Arnav's contribution is in [`contributions/arnav/`](contributions/arnav/README.md):
the phase-by-phase explanation, [compiled report](contributions/arnav/main.pdf),
LaTeX sources and bibliography, [executed notebook](contributions/arnav/arnav_model_explained.ipynb),
equation/units sheet, presentation notes, and team handoff. Its dimensionless notation
matches Joel's current analysis. The notebook verifies coordinate transformations;
it does not fit historical data or replace the shared solver or PINN.

Clone the project and create a branch for your work:

```text
git clone https://github.com/FriedelCraft/lynx-hare-project.git
cd lynx-hare-project
git switch -c your-name/work
```

Follow the environment setup below, then open `notebooks/group_project.ipynb`.
The historical datasets, shared protocol and all five contributions are integrated.
The original synthetic notebook remains a separate controlled recovery experiment.
Existing frozen results can be inspected without retraining.

| Member | Current contribution and review entry point |
|---|---|
| Arnav | Final model, observation units and scaling in `contributions/arnav/` |
| Joel | Stability derivation, symbolic checks and `report/joel_group_section.tex` |
| Rishi | Numerical simulations and historical stability placement in `notebooks/rishi_simulations.ipynb` |
| Advay | Historical data, independent baseline and evaluation in `notebooks/advay_data_validation.ipynb` |
| Yash | Historical PINN in `notebooks/yash_historical_pinn.ipynb`, slides and group integration |

After accepting the collaborator invitation, push your branch and open a pull request:

```text
git add <files-you-changed>
git commit -m "Describe your change"
git push -u origin HEAD
```

Use a new results directory when changing scientific sources or configuration. Existing
reference results carry source/configuration hashes, so they must not be mixed with a
different model. The `.gitattributes` file preserves evidence-file bytes across clones.

## Run from a clean environment

Use Python 3.12 (tested on 3.12.14). A CPU is sufficient; the reference run uses one CPU
thread and float64. These commands work in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m pip install --no-deps -e .
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python scripts/run_experiments.py
```

On macOS/Linux, replace `.\.venv\Scripts\python` with `.venv/bin/python`.
The main runner also adds `src` to its import path, so an editable install is optional for it.
For a quick API check, use `scripts/run_experiments.py --quick`; its results go to
`results/smoke/` and are not scientific evidence.

The full runner resumes existing run summaries if their configuration hash matches.
To repeat training independently, move `results/synthetic/` to a separate location first.
Do not compare a mixture of results from different source revisions. The manifest records
source and configuration hashes and runtime versions. Numerical results can vary slightly
across library versions and hardware despite deterministic seeds.

Open the notebook using VS Code's Jupyter extension or install JupyterLab separately:

```powershell
.\.venv\Scripts\python -m pip install jupyterlab
.\.venv\Scripts\python -m jupyterlab notebooks/yash_pinn.ipynb
```

The notebook contains the complete model, data, PINN, training, baseline, figure and
evaluation code in executable cells, generated from the canonical modules in `src/`.
It reuses completed reference runs by default. `scripts/build_deliverables.py` records
the embedded modules' hashes so the notebook and modular implementation can be checked
together, rather than maintaining separate versions manually.

## Model and experimental choices

\[
\dot H=rH(1-H/K)-\frac{aHP}{b+H},\qquad
\dot P=\frac{eaHP}{b+H}-mP.
\]

The primary inverse task estimates **r, a and m** while fixing **K, b and e**.
Both PINN and least squares use the same fixed values, bounds, initial state, training
normalization and RK45 tolerances. Fixed values equal generating values only in this
controlled synthetic study. This favorable assumption must be reconsidered for real data.
See [the model contract](docs/team_handoff.md) before replacing any shared interface.

Forecasts come from **integrating the ODE with learned parameters from the first training
year**, using the common initial state. Neural network extrapolation is not used.
The selected annual seed minimizes the training loss; held-out observations never choose
parameters, configurations or seeds. All default seed results are retained.

## Repository guide

| Location | Purpose |
|---|---|
| `src/lynx_hare/` | Shared model, data contract, PINN, baseline, experiments and plots |
| `configs/synthetic.json` | Generating parameters, bounds, seeds and optimizer settings |
| `data/synthetic/` | CSV observations, truth and provenance |
| `notebooks/yash_pinn.ipynb` | Executed analysis with equations and explanations |
| `results/synthetic/` | Recovery tables, metrics, forecasts, logs and manifest |
| `results/synthetic/figures/` | Publication figures in EPS and PNG |
| `report/` | Integrable LaTeX section, tables and bibliography |
| `presentation/` | Two-minute speaking notes and suggested slide content |
| `docs/` | Method, measured findings, handoffs and acknowledgements |
| `tests/` | Model, solver, gradients, leakage and reproducibility checks |

The solver and least-squares code are provisional integration aids for Yash's experiments;
Rishi and Advay retain ownership of their final group implementations. This is not the
completed five-person report or an empirical validation of the historical lynx–hare series.

## Replace synthetic data later

Follow [the handoff checklist](docs/team_handoff.md). Agree on units, notation, fixed
parameters and observation assumptions before fitting. Historical pelts are trade counts,
not direct population censuses. Keep the test years sealed during model development and
use a new result directory so synthetic evidence cannot be confused with historical results.

No collaborators are contacted by this code. There are no automatic Git pushes, credentials,
cloud calls or external experiment trackers.

Open `presentation/yash_pinn_slides.pptx` for the two-slide segment. Its text, notes and
comparison chart remain editable. The chart stores scores rounded to six decimals and
shows three decimals; full precision remains in the CSV. `presentation/slides.mjs` is
the source for the Codex Artifact Tool authoring environment. The Python environment
reproduces the scientific results independently of that slide-authoring tool.

## References

- Rosenzweig and MacArthur (1963), [Graphical Representation and Stability Conditions of Predator–Prey Interactions](https://doi.org/10.1086/282272).
- Raissi, Perdikaris and Karniadakis (2019), [Physics-informed neural networks](https://doi.org/10.1016/j.jcp.2018.10.045); [authors' project](https://maziarraissi.github.io/PINNs/).
- [PyTorch automatic differentiation](https://docs.pytorch.org/docs/stable/generated/torch.autograd.grad.html).
- [SciPy RK45 and solve_ivp](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html).

See [the AI assistance log](docs/ai_acknowledgement.md) for generated material and checks.

## Professor-format submission ZIP

The package layout and report compilation instructions are in
[SUBMISSION_README.md](SUBMISSION_README.md). The report PDF is `report/main.pdf`.
All seven report graphs have EPS sources in `report/graphs/`; vector PDF companions
support PDF-engine compilation. The report uses no separate diagrams.

After the notebook and report are finalized, build and audit the archive:

```powershell
.\.venv\Scripts\python scripts/verify_outputs.py
.\.venv\Scripts\python scripts/build_submission.py --extract-check
```

By default this writes `../submission/Lynx_Hare_Yash_PINN_Synthetic.zip`, outside the
repository. It includes the complete program, all datasets and supporting report files,
and excludes environments, Git metadata, caches and model checkpoints. The professor
requires email submission at least one week before the presentation. The current ZIP
is Yash's synthetic component for group integration and has not been emailed.
