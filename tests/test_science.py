"""Scientific contract tests: gradients, units, solver, leakage and reproducibility."""
import copy
import json
from pathlib import Path
import numpy as np
import pytest
import torch
from lynx_hare.model import Parameters, NAMES, rhs, rhs_torch, solve
from lynx_hare.data import TrainingData, synthetic, read_training, write_csv
from lynx_hare.pinn import InversePINN, fit_pinn, DTYPE
from lynx_hare.baseline import fit_least_squares

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "configs/synthetic.json").read_text())


def test_numpy_and_autograd_model_agree():
    states = np.array([[3.0, 7.0], [40, 10], [14, 13]])
    expected = np.array([rhs(0, y, Parameters(**CONFIG["truth"])) for y in states])
    actual = rhs_torch(torch.tensor(states, dtype=DTYPE), CONFIG["truth"]).numpy()
    np.testing.assert_allclose(expected, actual, rtol=1e-14)


def test_equilibrium_and_boundary_invariance():
    p = Parameters(**CONFIG["truth"])
    H = p.m * p.b / (p.e * p.a - p.m)
    P = p.r * (1-H/p.K) * (p.b+H) / p.a
    np.testing.assert_allclose(rhs(0, [H, P], p), [0, 0], atol=1e-13)
    assert rhs(0, [0, 4], p)[0] == 0
    assert rhs(0, [4, 0], p)[1] == 0


def test_solver_tolerance_and_nonnegativity():
    t = np.linspace(0, 20, 101)
    p = Parameters(**CONFIG["truth"])
    default = solve(t, CONFIG["initial_state"], p, **CONFIG["solver"])
    tight = solve(t, CONFIG["initial_state"], p, rtol=1e-10, atol=1e-12, max_step=0.05)
    assert np.min(default) > 0
    np.testing.assert_allclose(default, tight, rtol=2e-6, atol=1e-7)


@pytest.mark.parametrize("times,y0", [([0, 0], [1, 1]), ([0, 1], [-1, 1]), ([0, np.nan], [1, 1])])
def test_solver_rejects_invalid_inputs(times, y0):
    with pytest.raises(ValueError):
        solve(times, y0, Parameters(**CONFIG["truth"]))


def test_autodiff_includes_time_and_state_chain_rules():
    torch.manual_seed(5)
    model = InversePINN(15, [40, 25], CONFIG["initial_guess"], CONFIG["bounds"], CONFIG["trainable"], width=8, depth=2)
    t = torch.tensor([[1.1], [4.2]], dtype=DTYPE)
    residual = model.residuals(t).detach().numpy()
    eps = 1e-5
    with torch.no_grad():
        finite_diff = (model(t + eps) - model(t - eps)).numpy() / (2*eps)
        states = model(t).numpy() * model.scale.numpy()
    expected = finite_diff - np.array([rhs(0, y, model.inferred()) for y in states]) / model.scale.numpy()
    np.testing.assert_allclose(residual, expected, rtol=1e-7, atol=1e-9)


def test_physics_residual_backpropagates_to_every_unknown():
    model = InversePINN(15, [40, 25], CONFIG["initial_guess"], CONFIG["bounds"], CONFIG["trainable"], width=8, depth=2)
    model.residuals(torch.linspace(0, 15, 11, dtype=DTYPE)[:, None]).square().mean().backward()
    for raw in model.raw.values():
        assert raw.grad is not None and torch.isfinite(raw.grad) and abs(raw.grad) > 1e-12


def test_positivity_bounds_and_fixed_parameters():
    model = InversePINN(15, [40, 25], CONFIG["initial_guess"], CONFIG["bounds"], CONFIG["trainable"], width=8, depth=2)
    assert torch.all(model(torch.linspace(0, 15, 20, dtype=DTYPE)[:, None]) > 0)
    for name, raw in model.raw.items():
        with torch.no_grad():
            raw.fill_(-40)
        assert model.parameter_values()[name] >= CONFIG["bounds"][name][0]
    assert model.inferred().e == CONFIG["initial_guess"]["e"]


def test_scaling_and_loader_cannot_read_heldout(tmp_path):
    path = tmp_path / "combined.csv"
    rows = [[1900, 4, 2], [1915, 5, 3], [1916, 1e9, 1e9]]
    write_csv(path, ["Year", "Hare", "Lynx"], rows)
    training = read_training(path)
    np.testing.assert_array_equal(training.scale, [5, 3])
    np.testing.assert_array_equal(training.years, [1900, 1915])


def test_reproducible_training_without_truth_access():
    t = np.arange(4, dtype=float)
    _, observations = synthetic(CONFIG, t, noise_fraction=0)
    data = TrainingData(t + 1900, observations, 1900)
    settings = {"width": 8, "depth": 2, "collocation_points": 11,
                "warmup_steps": 5, "adam_steps": 10, "lbfgs_steps": 3, "log_every": 5}
    config = copy.deepcopy(CONFIG)
    config.pop("truth")
    first, _, audit = fit_pinn(data, config, 7, settings)
    second, _, _ = fit_pinn(data, config, 7, settings)
    assert first.inferred().to_dict() == second.inferred().to_dict()
    assert audit["train_years"][-1] == 1903


def test_noiseless_least_squares_recovers_known_parameters():
    t = np.arange(16, dtype=float)
    _, observations = synthetic(CONFIG, t, noise_fraction=0)
    data = TrainingData(t + 1900, observations, 1900)
    learned, _ = fit_least_squares(data, CONFIG, multistart=1)
    for name in CONFIG["trainable"]:
        assert abs(learned.to_dict()[name]/CONFIG["truth"][name] - 1) < 1e-4
