"""Checks on Advay's least-squares baseline module (no held-out data involved)."""
import json
from pathlib import Path

import numpy as np

from lynx_hare.data import TrainingData, read_training
from lynx_hare.model import Parameters, solve
from lynx_hare import historical_ls as hls

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "configs" / "historical.json").read_text())


def historical():
    return read_training(ROOT / "data" / "historical" / "train_1900_1915.csv", 1900, 1915)


def test_log_bounds_match_config_box():
    for variant in hls.VARIANTS:
        problem = hls.Problem(historical(), CONFIG, variant)
        lo, hi = np.exp(problem.lower), np.exp(problem.upper)
        for i, name in enumerate(CONFIG["trainable"]):
            assert np.isclose(lo[i], CONFIG["bounds"][name][0])
            assert np.isclose(hi[i], CONFIG["bounds"][name][1])
        if problem.fit_initial:
            np.testing.assert_allclose(lo[-2:], [15.0, 2.0])
            np.testing.assert_allclose(hi[-2:], [45.0, 6.0])


def test_starts_lie_inside_bounds_and_are_reproducible():
    problem = hls.Problem(historical(), CONFIG, "fitted_initial")
    a = hls.starting_points(problem, 40, 7)
    b = hls.starting_points(problem, 40, 7)
    np.testing.assert_array_equal(a, b)
    np.testing.assert_array_equal(a[0], problem.x_guess)
    assert np.all(a > problem.lower) and np.all(a < problem.upper)


def test_residuals_match_contract_scaling():
    data = historical()
    problem = hls.Problem(data, CONFIG, "main")
    p, y0 = problem.unpack(problem.x_guess)
    pred = solve(data.times, y0, p, **CONFIG["solver"])
    np.testing.assert_allclose(problem.residual(problem.x_guess),
                               ((pred - data.observations) / [77.4, 59.4]).ravel())
    log_problem = hls.Problem(data, CONFIG, "log_errors")
    np.testing.assert_allclose(log_problem.residual(problem.x_guess),
                               (np.log(pred) - np.log(data.observations)).ravel())


def test_recovers_known_parameters_from_exact_synthetic_trajectory():
    truth = Parameters(r=1.2, K=90.0, a=1.5, b=25.0, e=0.5, m=0.6)
    years = np.arange(1900, 1916)
    obs = solve(years - 1900.0, [30.0, 4.0], truth, **CONFIG["solver"])
    data = TrainingData(years, obs, 1900)
    config = {**CONFIG, "trainable": ["r", "a", "m"],
              "initial_guess": {**truth.to_dict(), "r": 0.8, "a": 1.0, "m": 0.4}}
    problem = hls.Problem(data, config, "main")
    settings = {"diff_step": 1e-4, "max_nfev": 500, "ftol": 1e-12, "xtol": 1e-12, "gtol": 1e-12}
    fit = hls.fit_start(problem, problem.x_guess, settings)
    p, _ = problem.unpack(fit.x)
    for k in ("r", "a", "m"):
        assert abs(getattr(p, k) / getattr(truth, k) - 1) < 1e-4, k


def test_forecast_covers_only_heldout_years():
    p = Parameters(**CONFIG["initial_guess"])
    years, states = hls.forecast(p, [30.0, 4.0], CONFIG, 1900, 1920, 1915)
    assert years.tolist() == [1916, 1917, 1918, 1919, 1920]
    assert states.shape == (5, 2) and np.all(states > 0)
