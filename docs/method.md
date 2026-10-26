# Inverse PINN method

## Question and scope

Can a neural approximation constrained by the Rosenzweig–MacArthur differential
equations recover known rates from sparse noisy observations, and do those rates give
useful ODE forecasts? The present answer concerns a controlled synthetic system.
It does not establish predictive performance on Hudson's Bay Company pelt counts.

## Equations and units

With synthetic abundance indices H and P and time t in years,

\[
f_H=rH(1-H/K)-aHP/(b+H),\quad f_P=eaHP/(b+H)-mP.
\]

| Parameter | Meaning | Units in this convention | Primary inverse task |
|---|---|---|---|
| r | Intrinsic hare growth rate | year⁻¹ | Estimated |
| K | Hare carrying capacity | hare index | Fixed at 60 |
| a | Saturated consumption per predator | hare index / lynx index / year | Estimated |
| b | Half-saturation abundance | hare index | Fixed at 20 |
| e | Conversion factor | lynx index / hare index | Fixed at 0.6 |
| m | Predator mortality rate | year⁻¹ | Estimated |

These values and bounds are designed for a numerical demonstration. They are not
biological estimates or constraints supplied by Joel. Constants in the model contract
must be agreed with the team before the historical application.

## Normalization and chain rule

Let s_H and s_P be the species-wise maxima of the training observations, T=15 years,
u=H/s_H, v=P/s_P and τ=t/T. The network takes x=2τ−1 and returns
(u,v)=softplus(Nθ(x))+10⁻¹⁰. Its three hidden layers have 48 tanh units each;
weights use Xavier normal initialization and biases start at zero.

The equations in τ coordinates would be

\[
u_\tau=Tru(1-s_Hu/K)-Ta s_Puv/(b+s_Hu),
\quad v_\tau=Tea s_Huv/(b+s_Hu)-Tmv.
\]

The implementation differentiates with respect to the original elapsed t, while the
network performs time normalization internally. Autograd therefore supplies the factor
2/T automatically. Residuals are R_H=du/dt−f_H(s_Hu,s_Pv)/s_H and
R_P=dv/dt−f_P(s_Hu,s_Pv)/s_P. Each residual is in normalized index per year.
This choice must be preserved when loss weights are transferred to another time unit.

## Unknown parameters and loss

Each unknown q is represented by q=lower+(upper−lower)sigmoid(η), so all learned
rates remain within strictly positive configured bounds. Fixed K, b and e are not
optimizer variables. Both fitting methods use this same parameter space; least squares
enforces bounds directly. r, a, m start at 0.7, 1.4, 0.35 before sensitivity changes.

\[
L=L_{data}+10L_{physics}+10L_{IC},\quad
L_{physics}=\frac{1}{2N_c}\sum_j(R_H(t_j)^2+R_P(t_j)^2).
\]

Data loss averages squared normalized errors across both species and all training
rows. Initial-condition loss averages the two squared errors at t=0, using the first
observed row. The first row also appears in data loss: it is deliberately given extra
weight through the IC term. Collocation consists of 161 evenly spaced points on [0,15],
including both endpoints. None is placed in the forecast interval. A separate 307-point
offset grid diagnoses between-collocation residuals after fitting, without retuning.

## Training and stopping

Training uses float64 and one CPU thread, with Python, NumPy and PyTorch seeds fixed
and deterministic PyTorch operations requested. A 500-step data/IC warmup precedes joint
Adam optimization (learning rate 0.002, maximum 5000 steps, gradient norm clipped at 10).
Every 100 joint steps, the complete training objective and its components are recorded.
Adam stops after 15 logged checks without improvement exceeding 10⁻⁸ or at its cap.
The best training checkpoint is then refined with L-BFGS and strong-Wolfe line search,
at most 600 iterations and the optimizer's default evaluation cap (750 evaluations).
Gradient and objective tolerances are 10⁻¹⁰ and 10⁻¹². L-BFGS closure losses are logged
every 25 evaluations and at exit. These evaluations include line-search trials and need
not be monotonic. The saved state minimizes the recorded weighted training objective.
The logs report the actual stop and iteration/evaluation counts; reaching a cap is not
presented as a proof of convergence to a global minimum.

## Synthetic experiments

The generator uses r=1, K=60, a=2, b=20, e=0.6, m=0.5, H(0)=35 and P(0)=9.
RK45 uses rtol=10⁻⁸, atol=10⁻¹⁰ and maximum internal step 0.1 years.
Observations are y_obs=y_true(1+0.03ε), ε~N(0,1), independently per time and species,
clipped below at 10⁻⁸. The synthetic initial condition is known exactly and its noise is
set to zero. This favorable condition is explicit and shared by both methods.

| Experiment | Observations through year label 1915 | Repeated training seeds |
|---|---|---|
| Dense clean | 61 quarterly samples, no noise | 17, 29, 43 |
| Dense noisy | 61 quarterly samples, 3% noise | 17, 29, 43 |
| Annual noisy | 16 annual samples, 3% noise | 17, 29, 43 |

All fits within a case share one noise realization (data seed 314). Variation across
training seeds measures optimization variability conditional on that realization, not
sampling uncertainty or confidence intervals. Additional annual runs fix seed 17 and
change physics weight to 1 or 100, or multiply unknown initial guesses by 0.6 or 1.4.
Configurations are declared in advance; none is selected on held-out performance.

## Comparison and forecasting

Least squares minimizes the same species-normalized training observation errors by
integrating the ODE. It uses six starts (seed 91), identical fixed parameters, bounds,
initial condition and RK45 settings. It does not include an ODE-residual penalty because
its predicted trajectory already solves the ODE to numerical accuracy. Nonconverged
starts are recorded and excluded from baseline selection.

For the main display, the default annual PINN seed with the smallest training objective
is selected. All three default seeds' scores remain in the tables. Every forecast is
integrated from 1900 with the fixed first training observation through 1920. Its values
for 1916–1920 are scored only after training and selection are frozen. We do not restart
from a held-out observation or extrapolate the network. The handoff uses original
synthetic evaluation units. RMSE=√mean(error²) and MAE=mean(|error|) are reported
separately for hare and lynx, against both noisy test observations and latent truth.

## Identifiability and limits

Absolute relative parameter recovery is 100|q_hat/q_true−1|. A finite-difference Jacobian
of normalized training trajectories with respect to log parameters gives singular values
for the three-unknown and six-variable settings. The latter diagnostic varies fixed
parameters locally; it does not train an all-six PINN. Small singular values indicate
weak local sensitivity. This diagnostic cannot prove structural or global identifiability.
The primary recovery result is conditional on correct fixed parameters, known initial
state and a correctly specified observation model.

Sparse observations, finite collocation, nonconvex optimization and interacting rates
can produce similar fitted curves with different forecasts. Loss components are on
different scales; low total loss alone does not guarantee an accurate integrated
trajectory. We therefore compare the network with the ODE during training, inspect
residuals on new training-domain points and report sensitivity and seed variability.
The test horizon has five points per species and the system has no seasonality,
spatial effects or measurement mechanism for traded pelts. Synthetic evidence cannot
resolve these real-world limitations.

## Sources

The PINN construction follows the general data-plus-physics approach described by
[Raissi and colleagues](https://maziarraissi.github.io/PINNs/). Time derivatives use
[PyTorch autograd](https://docs.pytorch.org/docs/stable/generated/torch.autograd.grad.html);
ODE trajectories use [SciPy solve_ivp](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html).
Model attribution: [Rosenzweig and MacArthur (1963)](https://doi.org/10.1086/282272).
