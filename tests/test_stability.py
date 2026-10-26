"""Checks Joel's closed-form stability results against the shared model.rhs."""
import json
from pathlib import Path

import numpy as np
import pytest
from scipy.integrate import solve_ivp

from lynx_hare.model import Parameters, rhs
from lynx_hare import stability as st

ROOT = Path(__file__).resolve().parents[1]
ILLUSTRATIVE = dict(r=1.5, K=90.0, a=4.0, b=30.0, e=0.4, m=0.8)


def numerical_jacobian(H, P, p, h=1e-6):
    cols = [(rhs(0, [H + dh, P + dp], p) - rhs(0, [H - dh, P - dp], p)) / (2 * h)
            for dh, dp in ((h, 0), (0, h))]
    return np.column_stack(cols)


@pytest.mark.parametrize("K", [40.0, 60.0, 90.0, 95.0, 150.0])
def test_equilibrium_and_jacobian_match_shared_model(K):
    p = Parameters(**dict(ILLUSTRATIVE, K=K))
    H, P = st.coexistence_prey(p), st.coexistence_predator(p)
    np.testing.assert_allclose(rhs(0, [H, P], p), [0, 0], atol=1e-12)
    J = st.jacobian(H, P, p)
    np.testing.assert_allclose(J, numerical_jacobian(H, P, p), rtol=1e-6, atol=1e-8)
    tr, det = st.coexistence_trace_det(p)
    np.testing.assert_allclose([np.trace(J), np.linalg.det(J)], [tr, det], atol=1e-12)
    assert det > 0


def test_hopf_threshold_trace_crosses_zero():
    p = Parameters(**ILLUSTRATIVE)
    assert st.hopf_threshold(p) == pytest.approx(30 + 2 * 30)
    trace = lambda K: st.coexistence_trace_det(Parameters(**dict(ILLUSTRATIVE, K=K)))[0]
    assert trace(89.0) < 0 < trace(91.0)
    assert trace(90.0) == pytest.approx(0, abs=1e-14)
    assert st.onset_period(p) == pytest.approx(2 * np.pi / np.sqrt(0.4))


def test_regimes_and_simulated_behaviour():
    below = Parameters(**dict(ILLUSTRATIVE, K=60.0))
    above = Parameters(**dict(ILLUSTRATIVE, K=150.0))
    extinct = Parameters(**dict(ILLUSTRATIVE, K=25.0))
    assert st.regime(below) == "stable_coexistence"
    assert st.regime(above) == "limit_cycle"
    assert st.regime(extinct) == "predator_extinct"

    def tail_range(p):
        s = solve_ivp(rhs, (0, 600), [20.0, 5.0], args=(p,), rtol=1e-9, atol=1e-11, dense_output=True)
        H = s.sol(np.linspace(500, 600, 2001))[0]
        return H.max() - H.min()

    assert tail_range(below) < 1e-3          # converges to E*
    assert tail_range(above) > 100           # sustained large cycle


def test_coexistence_conditions_match_persistence_boundary():
    p = Parameters(**ILLUSTRATIVE)
    m_edge = p.e * p.a * p.K / (p.b + p.K)
    assert st.coexistence_feasible(Parameters(**dict(ILLUSTRATIVE, m=0.99 * m_edge)))
    assert not st.coexistence_feasible(Parameters(**dict(ILLUSTRATIVE, m=1.01 * m_edge)))


def test_synthetic_truth_regime_is_documented():
    truth = Parameters(**json.loads((ROOT / "configs/synthetic.json").read_text())["truth"])
    assert st.regime(truth) == "limit_cycle"
    assert st.stability_margin(truth) == pytest.approx(60 / (20 * 1.7 / 0.7))
