# Team integration handoff

This package completes Yash's PINN implementation and synthetic validation. The shared
model, solver and least-squares benchmark here are provisional scaffolding for this work.
They do not represent completed contributions or approval from the other members.

## Freeze these decisions together

| Interface | Current provisional choice | Confirm with |
|---|---|---|
| State order | H (hare), P (lynx) | Arnav and Rishi |
| Equations | rH(1−H/K)−aHP/(b+H), eaHP/(b+H)−mP | Arnav |
| Physical time | elapsed years from first training observation | Arnav and Advay |
| Measurement scale | synthetic abundance indices; later agree on pelt units/proxy | Advay |
| Numerical normalization | maxima of training H and P only | Advay |
| Primary unknowns | r, a, m; fixed K=60, b=20, e=0.6 for synthetic study | Joel and Advay |
| Bounds and feasibility | positive finite bounds in config, not ecological conclusions | Joel |
| ODE method | RK45; rtol 1e−8, atol 1e−10, max_step 0.1 years | Rishi |
| Initial condition | first training observation, fixed for both fitting methods | Rishi and Advay |
| Split | 1900–1915 training, 1916–1920 scoring only | Advay |
| Forecast | integrate from 1900; evaluate 1916–1920; no test-state restart | Rishi and Advay |

The synthetic observation convention assumes both species are observed in known index
units with no unknown observation multipliers. Adding multipliers changes parameter
identifiability and requires a revised contract for both methods.

## Files to pass to Advay

- `results/synthetic/predictions_for_advay.csv`: exactly Year, Hare, Lynx for five
  held-out years, in original **synthetic** index units.
- `results/synthetic/selected_run.json`: learned dimensional parameters and selection rule.
- `results/synthetic/heldout_metrics.csv`: each default seed plus least squares;
  noisy-observation scores and latent-truth scores are explicitly distinguished.
- `results/synthetic/runs/*/summary.json` and `training.csv`: settings, seeds, fixed
  values, initial guesses, losses, runtime and residual checks.

These files demonstrate the interface; they must not be merged into a historical-data
results table as if they were measured pelt-series forecasts.

## Replace dummy observations

1. Advay supplies a cited, versioned CSV with exactly `Year,Hare,Lynx`, positive finite
   values, increasing years, original units and a documented observation convention.
   Zeros need an agreed measurement model; do not silently shift or log-transform them.
2. Arnav confirms equations and scaling; Joel supplies feasible ranges; both fitting
   methods receive the same trainable names, bounds and fixed values. Correct synthetic
   fixed values are not estimates that should be carried over to real data.
3. Keep training and testing CSVs separate. No scaling, early stopping, model selection
   or loss-weight tuning may inspect 1916–1920. Use a training-only internal validation
   scheme if tuning is needed, and specify it before test evaluation.
4. Run `scripts/fit_csv.py` using the agreed configuration and `--kind historical` into
   a **new** output directory. This script loads only the training years and exports ODE
   forecasts without scoring against later observations.
5. Advay evaluates the frozen forecasts and baseline using separate hare/lynx RMSE and
   MAE, identical dates, units, initial-condition convention and tolerances.
6. Replace the synthetic report tables and figures, write the data provenance, and
   revise interpretation. Keep the synthetic recovery section as a validation experiment.

## Checkpoints and version control

Torch checkpoints are generated locally and ignored by Git. Source, configurations,
CSV outputs, logs, figures and the executed notebook are sufficient to reproduce them.
Do not load checkpoints supplied by an untrusted source. Review `git status` before
staging and uploading. The professor-format submission ZIP is kept outside the project
repository; collaborators should work from the project sources and notebook.

Each member should understand the shared equations and how parameter/observation
assumptions affect their own results. See `presentation/yash_pinn_notes.md` for Yash's
two-minute explanation and questions to rehearse.
