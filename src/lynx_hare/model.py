"""Shared dimensional model and RK45 solver, provisional until team agreement."""
from dataclasses import dataclass, asdict
import numpy as np
from scipy.integrate import solve_ivp

NAMES = ("r", "K", "a", "b", "e", "m")


@dataclass(frozen=True)
class Parameters:
    r: float
    K: float
    a: float
    b: float
    e: float
    m: float

    def __post_init__(self):
        if not all(np.isfinite(v) and v > 0 for v in asdict(self).values()):
            raise ValueError("Every model parameter must be finite and positive")

    def to_dict(self):
        return asdict(self)


def rhs(t, state, p):
    """H' = rH(1-H/K)-aHP/(b+H); P' = eaHP/(b+H)-mP."""
    H, P = state
    consumption = p.a * H * P / (p.b + H)
    return np.array([p.r * H * (1 - H / p.K) - consumption,
                     p.e * consumption - p.m * P])


def rhs_torch(state, p):
    """Same equations, batch shape (N, 2), preserving the autograd graph."""
    import torch
    H, P = state[:, :1], state[:, 1:]
    consumption = p["a"] * H * P / (p["b"] + H)
    return torch.cat((p["r"] * H * (1 - H / p["K"]) - consumption,
                      p["e"] * consumption - p["m"] * P), dim=1)


def solve(times, initial_state, p, rtol=1e-8, atol=1e-10, max_step=0.1):
    """State at strictly increasing times; initial_state belongs to times[0]."""
    times = np.asarray(times, dtype=float)
    y0 = np.asarray(initial_state, dtype=float)
    if times.ndim != 1 or times.size == 0 or not np.isfinite(times).all():
        raise ValueError("times must be a nonempty finite 1D array")
    if np.any(np.diff(times) <= 0) or y0.shape != (2,) or not np.isfinite(y0).all() or np.any(y0 < 0):
        raise ValueError("times must increase; initial_state must contain two nonnegative values")
    if times.size == 1:
        return y0[None, :].copy()
    result = solve_ivp(lambda t, y: rhs(t, y, p), (times[0], times[-1]), y0,
                       t_eval=times, method="RK45", rtol=rtol, atol=atol, max_step=max_step)
    if not result.success or result.y.shape[1] != len(times):
        raise RuntimeError(f"ODE integration failed: {result.message}")
    states = result.y.T
    if not np.isfinite(states).all() or np.min(states) < -100 * atol:
        raise RuntimeError("ODE returned invalid or negative states")
    return states
