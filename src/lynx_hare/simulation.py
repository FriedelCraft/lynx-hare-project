"""Rishi's numerical simulations for the shared Rosenzweig-MacArthur model.

Every trajectory uses the team's single right-hand side, model.rhs, and every analytic
target comes from Joel's stability module, so this file adds numerics only:

* integrate          RK45 with the declared tolerances
* attractor_summary  post-transient min/max, period and predator lag
* bifurcation_sweep  numerical bifurcation diagram in K
* amplitude_law      cycle half-amplitude and period just above K_H
* Lotka-Volterra helpers for the solver-accuracy check (conserved quantity)

Illustrative parameters and validation targets: docs/joel_stability_handoff.md.
"""
from dataclasses import replace

import numpy as np
from scipy.integrate import solve_ivp

from .model import Parameters, rhs
from . import stability as st

RTOL, ATOL = 1e-10, 1e-12            # declared solver tolerances (Section 2, 1.8)
Y0 = (20.0, 5.0)                     # standard initial state, thousand pelts
T_BURN = 3000.0                      # default burn-in, years
T_BURN_NEAR_HOPF = 20000.0           # weak focus: |K - K_H| < 1 needs a much longer burn-in
ILLUSTRATIVE = dict(r=1.5, a=4.0, b=30.0, e=0.4, m=0.8)   # not fitted; H* = 30, K_H = 90
REGIMES = {"A": 25.0, "B": 60.0, "C": 85.0, "D": 90.0, "E": 95.0, "F": 150.0}


def with_K(p: Parameters, K: float) -> Parameters:
    return replace(p, K=float(K))


def integrate(p, y0, t_span, t_eval=None, rtol=RTOL, atol=ATOL, fun=rhs):
    """RK45 (Dormand-Prince) solution of fun(t, y, p); raises if the solver fails."""
    sol = solve_ivp(fun, t_span, np.asarray(y0, dtype=float), args=(p,), method="RK45",
                    rtol=rtol, atol=atol, t_eval=t_eval)
    if not sol.success:
        raise RuntimeError(f"RK45 failed: {sol.message}")
    return sol


def local_maxima(x):
    """Indices i with x[i-1] < x[i] > x[i+1]."""
    x = np.asarray(x)
    return np.where((x[1:-1] > x[:-2]) & (x[1:-1] > x[2:]))[0] + 1


def default_burn_in(p: Parameters) -> float:
    if st.coexistence_feasible(p) and abs(p.K - st.hopf_threshold(p)) < 1.0:
        return T_BURN_NEAR_HOPF
    return T_BURN


def attractor_summary(p, y0=Y0, t_burn=None, t_record=400.0, samples=40001, osc_tol=0.5):
    """Simulate past the transient and describe what the solution settles on.

    The first t_burn years are discarded. On the recorded window we report the range of
    H and P and, if H still oscillates by more than osc_tol, the mean period between hare
    peaks and the mean delay from each hare peak to the next lynx peak.
    """
    t_burn = default_burn_in(p) if t_burn is None else t_burn
    t = np.linspace(t_burn, t_burn + t_record, samples)
    H, P = integrate(p, y0, (0.0, t[-1]), t_eval=t).y
    out = dict(K=p.K, t_burn=t_burn, Hmin=H.min(), Hmax=H.max(), Pmin=P.min(), Pmax=P.max(),
               period=np.nan, lag=np.nan)
    hp, pp = local_maxima(H), local_maxima(P)
    if H.max() - H.min() > osc_tol and len(hp) > 2 and len(pp) > 2:
        out["period"] = float(np.mean(np.diff(t[hp])))
        lags = [t[pp][t[pp] > th][0] - th for th in t[hp] if np.any(t[pp] > th)]
        out["lag"] = float(np.mean(lags))
    return out


def regime_table(base=None, regimes=REGIMES, y0=Y0, t_burn=T_BURN):
    """Reproduce Joel's Table 2: eigenvalues plus simulated long-run behaviour.

    Uses the fixed 3000-year burn-in of Table 2 (so regime D keeps its expected
    slowly-decaying residual oscillation)."""
    base = base or Parameters(K=100.0, **ILLUSTRATIVE)
    rows = []
    for label, K in regimes.items():
        p = with_K(base, K)
        if st.coexistence_feasible(p):
            point = (st.coexistence_prey(p), st.coexistence_predator(p))
        else:
            point = (p.K, 0.0)                       # prey-only equilibrium E1
        eig = np.linalg.eigvals(st.jacobian(*point, p))
        rows.append(dict(label=label, regime=st.regime(p), eig=eig,
                         **attractor_summary(p, y0, t_burn=t_burn)))
    return rows


def bifurcation_sweep(base, K_values, y0=Y0, t_record=300.0, samples=15001):
    """Post-transient max/min of H and P for each K (numerical bifurcation diagram)."""
    rows = [attractor_summary(with_K(base, K), y0, t_record=t_record, samples=samples)
            for K in K_values]
    return {key: np.array([r[key] for r in rows]) for key in rows[0]}


def amplitude_law(base, dK, y0=Y0, t_record=400.0, samples=80001):
    """Half-amplitude of H and period at K = K_H + dK, plus the log-log fit A ~ c dK^s.

    A supercritical Hopf bifurcation predicts s = 1/2 and period -> 2 pi / omega_0."""
    KH = st.hopf_threshold(base)
    rows = [attractor_summary(with_K(base, KH + d), y0, t_record=t_record, samples=samples)
            for d in dK]
    amp = np.array([(r["Hmax"] - r["Hmin"]) / 2 for r in rows])
    period = np.array([r["period"] for r in rows])
    slope, log_c = np.polyfit(np.log(dK), np.log(amp), 1)
    return dict(dK=np.asarray(dK), amplitude=amp, period=period, slope=float(slope),
                coefficient=float(np.exp(log_c)),
                coefficient_sqrt=float(np.mean(amp / np.sqrt(dK))),
                onset_period=float(st.onset_period(base)))


def hopf_crossing(base, K_low, K_high):
    """K where the trace of J(E*) vanishes, found numerically (compare with K_H)."""
    from scipy.optimize import brentq
    trace = lambda K: np.trace(st.jacobian(st.coexistence_prey(with_K(base, K)),
                                           st.coexistence_predator(with_K(base, K)), with_K(base, K)))
    return brentq(trace, K_low, K_high, xtol=1e-13)


# ---------------------------------------------------------------- solver check
LV_DEFAULT = dict(alpha=1.0, beta=0.5, delta=0.25, gamma=0.5)


def lotka_volterra_rhs(t, y, q):
    H, P = y
    return [q["alpha"] * H - q["beta"] * H * P, q["delta"] * H * P - q["gamma"] * P]


def lotka_volterra_invariant(H, P, q):
    """V = delta H - gamma ln H + beta P - alpha ln P, constant on exact LV orbits."""
    return q["delta"] * H - q["gamma"] * np.log(H) + q["beta"] * P - q["alpha"] * np.log(P)


def euler(fun, y0, t_end, h, q):
    """Explicit Euler with fixed step h (used only to show its drift)."""
    n = int(round(t_end / h))
    y = np.empty((n + 1, 2))
    y[0] = y0
    for k in range(n):
        y[k + 1] = y[k] + h * np.asarray(fun(k * h, y[k], q))
    return np.linspace(0.0, n * h, n + 1), y
