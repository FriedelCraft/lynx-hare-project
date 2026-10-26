"""Provisional least-squares benchmark, shared solver, bounds, fixed values and IC."""
import numpy as np
from scipy.optimize import least_squares
from .model import Parameters, solve


def fit_least_squares(data, config, multistart=6, seed=91):
    names = config["trainable"]
    lower = np.array([config["bounds"][k][0] for k in names])
    upper = np.array([config["bounds"][k][1] for k in names])
    base = np.array([config["initial_guess"][k] for k in names])
    rng = np.random.default_rng(seed)

    def parameters(x):
        return Parameters(**{**config["initial_guess"], **dict(zip(names, x))})

    def residual(x):
        try:
            predicted = solve(data.times, data.initial_state, parameters(x), **config["solver"])
            return ((predicted - data.observations) / data.scale).ravel()
        except RuntimeError:
            return np.full(data.observations.size, 1e6)

    candidates, logs = [], []
    for i in range(multistart):
        guess = base if i == 0 else rng.uniform(lower + 1e-5, upper - 1e-5)
        fit = least_squares(residual, guess, bounds=(lower, upper), max_nfev=500,
                             ftol=1e-10, xtol=1e-10, gtol=1e-10)
        candidates.append(fit)
        logs.append({"start": i, "initial_guess": guess.tolist(), "cost": float(fit.cost),
                     "success": bool(fit.success), "status": int(fit.status), "nfev": int(fit.nfev),
                     "message": fit.message})
    eligible = [f for f in candidates if f.success and np.isfinite(f.cost)]
    if not eligible:
        raise RuntimeError("No least-squares start converged")
    best = min(eligible, key=lambda f: f.cost)
    return parameters(best.x), logs


def sensitivity_spectrum(data, p, config, names):
    """Local scaled trajectory sensitivity w.r.t. log parameters, not a proof of identifiability."""
    columns = []
    eps = 1e-4
    for k in names:
        plus, minus = p.to_dict(), p.to_dict()
        plus[k] *= np.exp(eps)
        minus[k] *= np.exp(-eps)
        delta = (solve(data.times, data.initial_state, Parameters(**plus), **config["solver"])
                 - solve(data.times, data.initial_state, Parameters(**minus), **config["solver"]))
        columns.append((delta / (2 * eps) / data.scale).ravel())
    singular = np.linalg.svd(np.column_stack(columns), compute_uv=False)
    return {"names": list(names), "singular_values": singular.tolist(),
            "condition_number": float(singular[0] / singular[-1])}
