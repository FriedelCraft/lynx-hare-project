"""Joel's analytic stability results for the shared Rosenzweig-MacArthur model.

H' = rH(1-H/K) - aHP/(b+H),  P' = eaHP/(b+H) - mP   (same as model.rhs)

Closed forms derived in report/joel_stability_section.tex and checked in
scripts/joel_symbolic_derivation.py and tests/test_stability.py.
"""
import numpy as np

from .model import Parameters


def coexistence_prey(p: Parameters) -> float:
    """H* = mb/(ea - m); only meaningful when ea > m."""
    return p.m * p.b / (p.e * p.a - p.m)


def coexistence_predator(p: Parameters) -> float:
    """P* = (r/a)(1 - H*/K)(b + H*)."""
    h = coexistence_prey(p)
    return p.r / p.a * (1 - h / p.K) * (p.b + h)


def coexistence_feasible(p: Parameters) -> bool:
    """E* lies in the open quadrant iff ea > m and H* < K (equivalently m < eaK/(b+K))."""
    return p.e * p.a > p.m and coexistence_prey(p) < p.K


def hopf_threshold(p: Parameters) -> float:
    """K_H = b + 2H* = b(ea + m)/(ea - m). Requires ea > m."""
    ea = p.e * p.a
    if ea <= p.m:
        raise ValueError("No coexistence equilibrium: e*a must exceed m")
    return p.b * (ea + p.m) / (ea - p.m)


def stability_margin(p: Parameters) -> float:
    """sigma = K/K_H: < 1 damped oscillations to E*, > 1 stable limit cycle."""
    return p.K / hopf_threshold(p)


def jacobian(H: float, P: float, p: Parameters) -> np.ndarray:
    r, K, a, b, e, m = p.r, p.K, p.a, p.b, p.e, p.m
    return np.array([[r * (1 - 2 * H / K) - a * b * P / (b + H) ** 2, -a * H / (b + H)],
                     [e * a * b * P / (b + H) ** 2, e * a * H / (b + H) - m]])


def coexistence_trace_det(p: Parameters) -> tuple[float, float]:
    """Closed forms: tr = rH*(K-K_H)/(K(b+H*)), det = rmb(K-H*)/(K(b+H*))."""
    h = coexistence_prey(p)
    tr = p.r * h * (p.K - hopf_threshold(p)) / (p.K * (p.b + h))
    det = p.r * p.m * p.b * (p.K - h) / (p.K * (p.b + h))
    return tr, det


def onset_period(p: Parameters) -> float:
    """Linear period at the Hopf point, 2*pi/sqrt(rmb/K_H) (uses K_H, not p.K)."""
    return 2 * np.pi / np.sqrt(p.r * p.m * p.b / hopf_threshold(p))


def regime(p: Parameters) -> str:
    """'predator_extinct', 'stable_coexistence', 'hopf_point' or 'limit_cycle'."""
    if not coexistence_feasible(p):
        return "predator_extinct"
    s = stability_margin(p)
    if np.isclose(s, 1.0, rtol=1e-12):
        return "hopf_point"
    return "stable_coexistence" if s < 1 else "limit_cycle"
