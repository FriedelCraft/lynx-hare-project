"""Historical extension checks use synthetic fixtures, never held-out observations."""
import copy
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from lynx_hare.data import TrainingData, synthetic, write_csv
from lynx_hare.historical_pinn import (HistoricalPINN, fit_historical, loss_parts,
                                       observation_loss, validate_config)
from lynx_hare.model import NAMES, Parameters, solve
from lynx_hare.pinn import DTYPE

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def fixture_protocol():
    generating = json.loads((ROOT / "configs/synthetic.json").read_text())
    _, observed = synthetic(generating, np.arange(16), noise_fraction=0)
    data = TrainingData(np.arange(1900, 1916), observed, 1900)
    config = copy.deepcopy(generating)
    config.pop("truth")
    config.update(kind="historical", trainable=list(NAMES), forecast_end_year=1920, seeds=[17])
    config["training"].update(width=8, depth=2, collocation_points=11,
                              warmup_steps=2, adam_steps=4, lbfgs_steps=2, log_every=2)
    return data, config


def test_pending_protocol_does_not_borrow_synthetic_constants():
    config = json.loads((ROOT / "configs/historical.pending.json").read_text())
    with pytest.raises(ValueError, match="supply initial_guess"):
        validate_config(config)


def test_log_loss_is_scale_invariant_and_additive_loss_matches_contract():
    obs = torch.tensor([[30.0, 4.0], [45.0, 20.0]], dtype=DTYPE)
    pred = 1.1 * obs
    scale = obs.max(dim=0).values
    assert observation_loss(pred, obs, scale, "additive") == pytest.approx(float(((pred-obs)/scale).square().mean()))
    assert observation_loss(pred, obs, scale, "log") == pytest.approx(np.log(1.1)**2)
    torch.testing.assert_close(observation_loss(pred*7, obs*7, scale*7, "log"),
                               observation_loss(pred, obs, scale, "log"))


def test_all_six_rates_and_initial_state_receive_gradients(fixture_protocol):
    data, config = fixture_protocol
    model = HistoricalPINN(data, config, fit_initial=True)
    with torch.no_grad():
        np.testing.assert_allclose(model.initial_values().numpy(), data.initial_state)
    t = torch.tensor(data.times[:, None], dtype=DTYPE)
    parts = loss_parts(model, t, torch.tensor(data.observations, dtype=DTYPE), t, "log")
    (parts["physics"] + parts["ic"] + parts["data"]).backward()
    for name in NAMES:
        assert model.raw[name].grad is not None
        assert torch.isfinite(model.raw[name].grad) and abs(model.raw[name].grad) > 1e-12
    assert model.raw_initial.grad is not None and torch.isfinite(model.raw_initial.grad).all()
    for value, factor in ((-100.0, 0.5), (100.0, 1.5)):
        with torch.no_grad():
            model.raw_initial.fill_(value)
            np.testing.assert_allclose(model.initial_values().numpy(), data.initial_state*factor)


@pytest.mark.parametrize("error_model,fit_initial", [("additive", False), ("log", False), ("additive", True)])
def test_training_is_repeatable_and_reports_initial_mismatch(fixture_protocol, error_model, fit_initial):
    data, config = fixture_protocol
    model, history, audit = fit_historical(data, config, 17, error_model, fit_initial)
    repeat, _, repeat_audit = fit_historical(data, config, 17, error_model, fit_initial)
    assert model.inferred() == repeat.inferred()
    assert audit["ode_initial"] == repeat_audit["ode_initial"]
    assert history and audit["train_years"] == list(range(1900, 1916))
    assert audit["scale"] == data.scale.tolist()
    np.testing.assert_allclose(np.array(audit["network_initial"])-audit["ode_initial"], audit["network_minus_ode_initial"])
    if not fit_initial:
        assert audit["ode_initial"] == data.initial_state.tolist()


def runner_module():
    spec = importlib.util.spec_from_file_location("historical_runner", ROOT / "scripts/run_historical_pinn.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_split_loader_never_opens_test_or_master(monkeypatch):
    runner = runner_module()
    original = Path.open
    def guarded(path, *args, **kwargs):
        if path.name in ("test_1916_1920.csv", "pelts_1900_1920.csv"):
            raise AssertionError("Held-out/master table was accessed")
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded)
    data, _ = runner.training_split()
    assert data.years.tolist() == list(range(1900, 1916))


def test_complete_export_freezes_every_variant_without_heldout_access(fixture_protocol, monkeypatch, tmp_path):
    data, config = fixture_protocol
    runner = runner_module()
    train = tmp_path / "synthetic_fixture.csv"
    write_csv(train, ["Year", "Hare", "Lynx"], np.column_stack((data.years, data.observations)))
    monkeypatch.setattr(runner, "training_split", lambda root: (data, train))
    config_path = tmp_path / "fixture.json"
    config_path.write_text(json.dumps(config))
    original = Path.open
    def guarded(path, *args, **kwargs):
        if path.name in ("test_1916_1920.csv", "pelts_1900_1920.csv"):
            raise AssertionError("Held-out/master table was accessed")
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded)
    output = runner.run(config_path, tmp_path / "synthetic_outputs")
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["status"] == "forecasts_frozen_unscored"
    assert manifest["run_count"] == 3 and manifest["heldout_observations_read"] is False
    for variant in runner.VARIANTS:
        folder = output / "runs" / f"{variant}_seed17"
        summary = json.loads((folder / "summary.json").read_text())
        exported = np.loadtxt(folder / "forecast.csv", delimiter=",", skiprows=1)
        reconstructed = solve(np.arange(21), summary["audit"]["ode_initial"],
                              Parameters(**summary["parameters"]), **config["solver"])
        np.testing.assert_array_equal(exported[:, 0], np.arange(1916, 1921))
        np.testing.assert_allclose(exported[:, 1:], reconstructed[16:], rtol=1e-12)
    with pytest.raises(ValueError, match="new output directory"):
        runner.run(config_path, output)


def test_matching_baseline_exports_serializable_synthetic_results(fixture_protocol, monkeypatch, tmp_path):
    data, config = fixture_protocol
    # Start at the generating values for a fast, meaningful zero-residual check.
    generating = json.loads((ROOT / "configs/synthetic.json").read_text())
    config["initial_guess"] = generating["truth"]
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    import fit_historical_baseline as baseline
    train = tmp_path / "synthetic_fixture.csv"
    write_csv(train, ["Year", "Hare", "Lynx"], np.column_stack((data.years, data.observations)))
    monkeypatch.setattr(baseline, "training_split", lambda: (data, train))
    path = tmp_path / "fixture.json"
    path.write_text(json.dumps(config))
    output = baseline.run(path, tmp_path / "baseline", multistart=1)
    chosen = json.loads((output / "selected.json").read_text())
    assert set(chosen) == {"main", "log_errors", "fitted_initial"}
    assert all(r["training_mse"] < 1e-15 for r in chosen.values())
    assert json.loads((output / "manifest.json").read_text())["status"] == "forecasts_frozen_unscored"
