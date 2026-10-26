# Figure captions

All panels show synthetic experiments. PNG previews and EPS publication files contain
the same figure content and share the following base names in `results/synthetic/figures/`.

1. **forecast_comparison**. Synthetic annual hare and lynx observations, generating
   ODE trajectory, and frozen ODE forecasts from PINN-derived and least-squares parameters.
   The shaded interval covers held-out years after 1915. The PINN seed is chosen by its
   training objective only. Both forecast curves integrate from the first training row.
2. **training_losses**. Total weighted loss and unweighted data, physics and initial
   losses for the selected annual PINN. The horizontal coordinate combines joint Adam
   steps with subsequent L-BFGS closure evaluations; the 500-step warmup is omitted.
   Line-search trials may make the latter trace nonmonotonic.
3. **network_ode_consistency**. Neural state approximations and the ODE integrated with
   learned parameters on the training interval, with the observed training samples.
   This check distinguishes a good neural fit from an accurate mechanistic trajectory.
4. **parameter_recovery**. Absolute relative error of each unknown for 61 clean quarterly,
   61 noisy quarterly and 16 noisy annual training observations. Points are three
   optimizer seeds with one fixed noise realization; black marks are arithmetic means.
   These are optimization replicates, not confidence intervals.
5. **sensitivity**. Five-year ODE forecasts from the default annual seed-17 fit and
   prespecified changes to physics weight or initial guesses. The latent synthetic
   trajectory is a reference. These variants are diagnostic and do not select the
   reported configuration using test errors.
6. **identifiability**. Singular values of normalized trajectory sensitivities to log
   parameters, evaluated at the selected annual estimate. Compare varying r,a,m with
   varying all six rates/constants locally. Small singular values indicate weak local
   sensitivity; this is not an all-six PINN recovery experiment or a global proof.
7. **residual_check**. Scaled hare and lynx ODE residuals on an independent offset grid
   of 307 points within the training interval. Residuals have units of inverse years.
   These points diagnose finite-collocation error after fitting and do not tune the model.
