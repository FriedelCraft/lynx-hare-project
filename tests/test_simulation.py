"""Checks Rishi's simulation layer against the shared model and Joel's validation targets."""
import json
from pathlib import Path

import numpy as np
import pytest

from lynx_hare.model import Parameters, rhs
from lynx_hare import simulation as sim, stability as st

ROOT = Path(__file__).resolve().parents[1]
BASE = Parameters(K=150.0, **sim.ILLUSTRATIVE)
TARGETS = {r["label"]: r for r in json.loads(
    (ROOT / "results" / "stability" / "validation_targets.json").read_text())["regimes"]}


def test_rk45_preserves_lotka_volterra_invariant_and_euler_does_not():
    q, y0 = sim.LV_DEFAULT, (3.0, 1.0)
    t = np.linspace(0, 100, 2001)
    y = sim.integrate(q, y0, (0, 100), t_eval=t, fun=sim.lotka_volterra_rhs).y
    V0 = sim.lotka_volterra_invariant(*y0, q)
    assert np.abs(sim.lotka_volterra_invariant(*y, q) - V0).max() < 1e-7
    _, ye = sim.euler(sim.lotka_volterra_rhs, y0, 100, 0.01, q)
    assert np.abs(sim.lotka_volterra_invariant(ye[:, 0], ye[:, 1], q) - V0).max() > 1e-2


def test_simulation_uses_shared_rhs_and_stays_positive():
    t = np.linspace(0, 200, 4001)
    y = sim.integrate(BASE, sim.Y0, (0, 200), t_eval=t).y
    assert y.min() > 0
    np.testing.assert_allclose(rhs(0, y[:, -1], BASE),
                               np.gradient(y, t, axis=1)[:, -1], rtol=0.05, atol=0.5)


def test_local_maxima():
    x = np.sin(np.linspace(0, 6 * np.pi, 3001))
    assert len(sim.local_maxima(x)) == 3


@pytest.mark.parametrize("label", ["B", "E", "F"])
def test_attractor_matches_joel_targets(label):
    p = sim.with_K(BASE, sim.REGIMES[label])
    got = sim.attractor_summary(p, t_burn=sim.T_BURN)
    tg = TARGETS[label]
    for key in ("Hmin", "Hmax", "Pmin", "Pmax"):
        assert got[key] == pytest.approx(tg[key], rel=5e-3, abs=5e-2)
    if label != "B":
        assert got["period"] == pytest.approx(tg["period"], rel=5e-3)
    else:
        assert np.isnan(got["period"])


def test_numerical_hopf_crossing_matches_closed_form():
    assert sim.hopf_crossing(BASE, 60.0, 120.0) == pytest.approx(st.hopf_threshold(BASE), abs=1e-9)


def test_near_hopf_points_get_long_burn_in():
    assert sim.default_burn_in(sim.with_K(BASE, 90.5)) == sim.T_BURN_NEAR_HOPF
    assert sim.default_burn_in(sim.with_K(BASE, 150.0)) == sim.T_BURN
