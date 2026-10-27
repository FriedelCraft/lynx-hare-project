"""Advay's nonlinear least-squares baseline for the historical pelt data.

Written independently of Yash's matched benchmark, on the same shared contract:
model.rhs / model.solve, configs/historical.json (trainable names, bounds, solver),
training rows only, residuals scaled by training maxima (or log residuals).

Optimisation runs in log-parameter space, x = log(theta), because the bounds span
several orders of magnitude. Box bounds become log-bounds, so the feasible set is
identical to the config's.
"""
from dataclasses import dataclass

import numpy as np
from scipy.optimize import least_squares

from .model import NAMES, Parameters, solve
from . import stability as st

VARIANTS = {"main": ("additive", False), "log_errors": ("log", False),
            "fitted_initial": ("additive", True)}
FAILED_RESIDUAL = 1e3
INITIAL_FACTOR = (0.5, 1.5)


@dataclass
class Problem:
    data: object
    config: dict
    variant: str

    def __post_init__(self):
        if self.variant not in VARIANTS:
            raise ValueError(f"Unknown variant {self.variant}")
        self.error_model, self.fit_initial = VARIANTS[self.variant]
        self.names = list(self.config["trainable"])
        lo = [self.config["bounds"][n][0] for n in self.names]
        hi = [self.config["bounds"][n][1] for n in self.names]
        if self.fit_initial:
            y0 = self.data.initial_state
            lo += list(y0 * INITIAL_FACTOR[0])
            hi += list(y0 * INITIAL_FACTOR[1])
        self.lower, self.upper = np.log(lo), np.log(hi)
        guess = [self.config["initial_guess"][n] for n in self.names]
        if self.fit_initial:
            guess += list(self.data.initial_state)
        self.x_guess = np.log(guess)

    def unpack(self, x):
        theta = np.exp(x)
        values = dict(self.config["initial_guess"])
        values.update(zip(self.names, theta[:len(self.names)]))
        p = Parameters(**{k: float(values[k]) for k in NAMES})
        y0 = theta[len(self.names):] if self.fit_initial else self.data.initial_state
        return p, np.asarray(y0, dtype=float)

    def residual(self, x):
        try:
            p, y0 = self.unpack(x)
            pred = solve(self.data.times, y0, p, **self.config["solver"])
            if self.error_model == "log":
                if np.any(pred <= 0):
                    raise RuntimeError("nonpositive prediction")
                r = np.log(pred) - np.log(self.data.observations)
            else:
                r = (pred - self.data.observations) / self.data.scale
            if not np.all(np.isfinite(r)):
                raise RuntimeError("nonfinite residual")
            return r.ravel()
        except (RuntimeError, ValueError):
            return np.full(self.data.observations.size, FAILED_RESIDUAL)


def starting_points(problem, n_starts, seed):
    """Start 0 is the config's initial guess; the rest are a Latin hypercube in log space."""
    rng = np.random.default_rng(seed)
    d = len(problem.lower)
    m = n_starts - 1
    cells = (np.argsort(rng.random((m, d)), axis=0) + rng.random((m, d))) / m
    span = problem.upper - problem.lower
    inner = problem.lower + 1e-6 * span + cells * span * (1 - 2e-6)
    return np.vstack([problem.x_guess, inner])


def fit_start(problem, x0, settings):
    return least_squares(problem.residual, x0, bounds=(problem.lower, problem.upper),
                         method="trf", x_scale="jac", diff_step=settings["diff_step"],
                         max_nfev=settings["max_nfev"], ftol=settings["ftol"],
                         xtol=settings["xtol"], gtol=settings["gtol"])


def describe(problem, fit):
    """Everything worth knowing about one finished start, in original units."""
    p, y0 = problem.unpack(fit.x)
    span = problem.upper - problem.lower
    near = {n: ("lower" if (fit.x[i] - problem.lower[i]) < 0.01 * span[i] else
                "upper" if (problem.upper[i] - fit.x[i]) < 0.01 * span[i] else None)
            for i, n in enumerate(problem.names + (["H0", "P0"] if problem.fit_initial else []))}
    feasible = st.coexistence_feasible(p)
    out = {"cost": float(fit.cost), "success": bool(fit.success), "status": int(fit.status),
           "nfev": int(fit.nfev), "message": fit.message,
           "failed_solve": bool(np.all(fit.fun == FAILED_RESIDUAL)),
           "parameters": p.to_dict(), "initial_state": y0.tolist(),
           "at_bound": {k: v for k, v in near.items() if v},
           "coexistence_feasible": bool(feasible),
           "regime": st.regime(p),
           "sigma": float(st.stability_margin(p)) if feasible else None,
           "hopf_threshold_K_H": float(st.hopf_threshold(p)) if p.e * p.a > p.m else None}
    return out


def local_identifiability(problem, fit):
    """Singular values of the scaled Jacobian in log-parameter space and approximate
    relative standard errors from (J^T J)^-1 s^2. Local and linearised: a diagnostic,
    not a confidence interval."""
    J = fit.jac
    names = problem.names + (["H0", "P0"] if problem.fit_initial else [])
    sv = np.linalg.svd(J, compute_uv=False)
    dof = max(J.shape[0] - J.shape[1], 1)
    s2 = 2 * fit.cost / dof
    try:
        cov = np.linalg.pinv(J.T @ J) * s2
        rel_se = dict(zip(names, np.sqrt(np.clip(np.diag(cov), 0, None)).tolist()))
        corr = cov / np.sqrt(np.outer(np.diag(cov), np.diag(cov)))
        strongest = sorted(((abs(corr[i, j]), names[i], names[j]) for i in range(len(names))
                            for j in range(i + 1, len(names))), reverse=True)[:5]
    except np.linalg.LinAlgError:
        rel_se, strongest = None, []
    return {"names": names, "singular_values": sv.tolist(),
            "condition_number": float(sv[0] / sv[-1]) if sv[-1] > 0 else None,
            "residual_variance": float(s2), "degrees_of_freedom": int(dof),
            "approx_log_parameter_se": rel_se,
            "strongest_correlations": [{"pair": [a, b], "abs_corr": float(c)} for c, a, b in strongest]}


def forecast(p, y0, config, start_year, end_year, train_end):
    years = np.arange(start_year, end_year + 1)
    states = solve(years - start_year, y0, p, **config["solver"])
    keep = years > train_end
    return years[keep], states[keep]


def dense(p, y0, config, duration, step=0.05):
    t = np.arange(0, duration + step / 2, step)
    return t, solve(t, y0, p, **config["solver"])
