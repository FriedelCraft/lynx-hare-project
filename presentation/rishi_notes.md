# Rishi: two-minute dynamics segment

Order in the group talk: after Joel (theory), before Yash (PINN). Three slides.
Figures are in `report/graphs/` (PDF/EPS) and `results/simulations/figures/` (PNG for slides).

## Slide 1 - Testing the theory numerically (about 45 seconds)

Visual: `rishi_regimes.png` (four phase portraits; show the bottom row).

- Joel's analysis is local: it tells us what happens near one equilibrium at one value of K.
  I simulate the full model to test it and to measure what linearisation cannot give.
- Solver: RK45 with declared tolerances. Check: on Lotka-Volterra it keeps the conserved
  quantity constant to 1e-10, while Euler drifts and invents a spiral.
- With Joel's illustrative parameters, K_H = 90. Below it (K = 60, 85) oscillations die out
  and the orbit spirals into E*. Above it (K = 95, 150) they settle onto a cycle.
- Arrows show the flow direction; it circulates counter-clockwise and lynx peaks lag hare peaks.

Say: "The switch happens exactly where the nullcline picture predicts: when the lynx line
crosses the hare hump to the left of its peak."

## Slide 2 - The Hopf bifurcation is supercritical (about 40 seconds)

Visual: `rishi_bifurcation.png` (left panel); backup `rishi_amplitude_period.png`, `rishi_limit_cycle.png`.

- Sweep K and record the long-run maximum and minimum of the hare population.
- Below 90 they coincide: an equilibrium. At 90 they separate continuously: a cycle born with zero size.
- Amplitude grows like the square root of (K - K_H): fitted slope 0.507, prediction 0.5.
  That is the signature of a supercritical Hopf bifurcation, so the cycle is stable.
- Starting inside or outside the cycle reaches the same loop: unlike Lotka-Volterra, the cycle attracts.
- Minima sink towards zero as K grows: the paradox of enrichment.

## Slide 3 - Where the real fits lie (about 35 seconds)

Visual: `rishi_historical_sigma.png`; backup `rishi_historical_bifurcation.png`.

- I evaluated sigma = K/K_H for all 31 fitted parameter sets (13 PINN, 18 least-squares starts).
- Every good fit reproduces a period of about 10 years and a lynx lag of 1.3-2 years.
- But PINN fits give sigma 1.32-1.48, least squares 0.55-1.07: the methods disagree about the side.
- Reason: the growth or decay rate is tiny, so the e-folding time is 50 to 5600 years.
  Over 16 years of data a slowly damped and a slowly growing oscillation look the same.
- And b sits on its upper bound in almost every fit; wider bounds move sigma from 1.36 to 1.48.

Say: "So the model sits close to the Hopf threshold, but these data cannot tell us whether the
real cycle is a stable limit cycle or a slowly damped oscillation."

## Likely questions

- *Why RK45 and not Euler?* Euler is first order and drifts; the Lotka-Volterra test shows it creating a spiral.
- *Why two solver settings?* Fitting and 1900-1920 forecasts use model.solve (rtol 1e-8, max_step 0.1),
  the same for both methods. Long-run runs over thousands of years use tighter tolerances (1e-10).
  Both use the same right-hand side; re-integrating the selected fit with model.solve matches Yash's
  saved path to 5e-12.
- *Why discard a burn-in?* The early part depends on the starting point; we want the long-term behaviour.
- *What is supercritical?* The cycle appears with zero amplitude and grows continuously, and it is stable.
  Subcritical: an unstable cycle, and the system jumps to a large oscillation at the threshold.
- *How do you know it is a limit cycle, not slow decay?* Long burn-in, constant peak heights, and
  convergence from inside and outside.
- *Does sigma > 1 mean the real ecosystem has a limit cycle?* No. It depends on the fitting method,
  error model and bounds, and the data cannot distinguish the two over 16 years.
- *Why is the PINN's long-run cycle so large (period 18.5 years)?* Its fitted trajectory over
  1900-1920 is an early part of a slowly growing spiral; the long-run cycle is reached only after centuries.
