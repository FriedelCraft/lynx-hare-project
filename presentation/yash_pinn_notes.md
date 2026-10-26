# Yash presentation notes

Target: about two minutes. Use two slides and point to figures rather than reading formulas.

## Slide 1 How the inverse PINN works

Show the two model equations, a time → network → hare/lynx sketch, and
L = data error + 10 × physics error + 10 × initial-condition error.

**Speaking notes, about 60 seconds**

“My part tests whether a physics-informed neural network can recover model parameters
while fitting observations. I used synthetic data because our final historical data
and shared interfaces are not ready yet. The network takes scaled time and predicts
positive hare and lynx indices. Automatic differentiation computes their time derivatives.
The loss penalizes observation errors, violations of both differential equations, and
initial-condition errors. I estimate r, a and m within positive bounds, while fixing K,
b and e for this controlled test. I train with Adam and then L-BFGS, and repeat the fit
with three random seeds. The exact initial state and correct fixed constants are favorable
assumptions that we will need to revisit for the real data.”

## Slide 2 What the synthetic tests show

Show `parameter_recovery.png` beside `forecast_comparison.png`, with the words
**Synthetic data**, **ODE forecast**, and **Mixed comparison** clearly visible.

**Speaking notes, about 60 seconds**

“Across three seeds, the maximum parameter error was 0.0057 percent for clean
quarterly data and 0.358 percent for the noisy annual case. These are optimizer
replicates on one noise realization, not confidence intervals. For forecasting, I freeze
the learned parameters and integrate the ODE through the five held-out years. I do not
extrapolate the neural network. Against noisy test observations, least squares has lower
hare error and the selected PINN has lower lynx error, so there is no overall win to
claim. I also vary loss weights and initial guesses and check local parameter sensitivity.
The current conclusion is that the implementation works on this controlled example.
The next empirical step is to use the team's agreed data and assumptions without
changing the method using the test period.”

## Questions to rehearse

- Why fix three parameters? To define a tractable controlled inverse test; correctness
  of those fixed values is a strong assumption, not something recovered by the PINN.
- Why scale both species? To avoid one index dominating the data loss through its units.
- Why use autograd? To differentiate the network through its internal time transformation.
- Why compare with least squares? It tests whether the neural approximation adds value
  beyond directly fitting this small ODE model; better performance is not assumed.
- Why use an ODE forecast? It tests the learned mechanistic parameters and avoids
  treating unconstrained neural extrapolation as a dynamical forecast.
- What is still provisional? Real measurements, observation conventions, parameter ranges
  and the final shared model and solver. Historical predictive performance is untested.
