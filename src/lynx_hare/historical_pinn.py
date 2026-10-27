"""Historical fitting extensions; synthetic experiment sources remain frozen.

Only a TrainingData object enters optimization. Historical coefficients are effective
coefficients in the observation units, with bounds supplied by the common team config.
"""
import copy
import random
import time

import numpy as np
import torch
from torch import nn

from .model import NAMES
from .pinn import DTYPE, InversePINN


def validate_config(config):
    """Require explicit historical choices instead of borrowing synthetic constants."""
    if config.get("kind") != "historical" or "truth" in config:
        raise ValueError("Provide a historical config without generating truth")
    names = config.get("trainable", [])
    if not names or len(set(names)) != len(names) or not set(names) <= set(NAMES):
        raise ValueError("Declare distinct trainable model parameters")
    guesses, bounds = config.get("initial_guess"), config.get("bounds")
    if not isinstance(guesses, dict) or set(guesses) != set(NAMES):
        raise ValueError("Please supply initial_guess for all six parameters")
    if not isinstance(bounds, dict):
        raise ValueError("Please supply common positive parameter bounds")
    for name in NAMES:
        if not np.isfinite(guesses[name]) or guesses[name] <= 0:
            raise ValueError(f"Invalid initial/fixed value for {name}")
        if name in names:
            lo, hi = bounds[name]
            if not np.isfinite([lo, hi]).all() or not 0 < lo < guesses[name] < hi:
                raise ValueError(f"Require positive bounds containing the guess for {name}")
    if set(config.get("solver", {})) != {"rtol", "atol", "max_step"}:
        raise ValueError("Declare shared rtol, atol and max_step")
    if any(not np.isfinite(v) or v <= 0 for v in config["solver"].values()):
        raise ValueError("Solver settings must be finite and positive")
    for key in ("start_year", "train_end_year", "forecast_end_year", "training", "seeds"):
        if key not in config:
            raise ValueError(f"Missing {key}")
    if not config["start_year"] < config["train_end_year"] < config["forecast_end_year"]:
        raise ValueError("Require training years before forecast years")
    if not config["seeds"] or len(set(config["seeds"])) != len(config["seeds"]):
        raise ValueError("Declare distinct optimization seeds")
    if any(not isinstance(seed, int) or seed < 0 for seed in config["seeds"]):
        raise ValueError("Seeds must be nonnegative integers")
    settings = config["training"]
    for key in ("width", "depth", "collocation_points", "log_every", "patience", "threads"):
        if not isinstance(settings.get(key), int) or settings[key] < 1:
            raise ValueError(f"Require a positive integer {key}")
    if settings["collocation_points"] < 2:
        raise ValueError("Use at least two collocation points")
    for key in ("warmup_steps", "adam_steps", "lbfgs_steps"):
        if not isinstance(settings.get(key), int) or settings[key] < 0:
            raise ValueError(f"Require nonnegative integer {key}")
    for key in ("learning_rate", "data_weight", "physics_weight", "ic_weight", "gradient_clip", "min_delta"):
        value = settings.get(key)
        if value is None or not np.isfinite(value) or value < 0 or (key != "min_delta" and value == 0):
            raise ValueError(f"Invalid {key}")


class HistoricalPINN(InversePINN):
    def __init__(self, data, config, fit_initial=False):
        settings = config["training"]
        super().__init__(data.times[-1], data.scale, config["initial_guess"],
                         config["bounds"], config["trainable"],
                         settings["width"], settings["depth"])
        self.register_buffer("observed_initial", torch.as_tensor(data.initial_state, dtype=DTYPE))
        self.fit_initial = bool(fit_initial)
        if fit_initial:
            # Midpoint of [0.5*y0, 1.5*y0] is the observed initial state.
            self.raw_initial = nn.Parameter(torch.zeros(2, dtype=DTYPE))

    def initial_values(self):
        if self.fit_initial:
            return self.observed_initial * (0.5 + torch.sigmoid(self.raw_initial))
        return self.observed_initial


def observation_loss(predicted, observed, scale, error_model):
    if error_model == "additive":
        return ((predicted - observed) / scale).square().mean()
    if error_model == "log":
        return (torch.log(predicted) - torch.log(observed)).square().mean()
    raise ValueError("error_model must be additive or log")


def loss_parts(model, times, observed, collocation, error_model="additive"):
    data_loss = observation_loss(model(times) * model.scale, observed, model.scale, error_model)
    residual = model.residuals(collocation)
    initial = model.initial_values()
    ic = ((model(times[:1]) - initial / model.scale) ** 2).mean()
    return {"data": data_loss, "physics": residual.square().mean(), "ic": ic,
            "physics_hare": residual[:, 0].square().mean(),
            "physics_lynx": residual[:, 1].square().mean()}


def fit_historical(data, config, seed, error_model="additive", fit_initial=False):
    """Fit a frozen training split; no test path or test observations are accepted."""
    validate_config(config)
    if data.years.tolist() != list(range(config["start_year"], config["train_end_year"] + 1)):
        raise ValueError("TrainingData must contain the complete declared annual training split")
    if error_model not in ("additive", "log"):
        raise ValueError("error_model must be additive or log")
    s = config["training"]
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(s["threads"])
    torch.use_deterministic_algorithms(True)
    model = HistoricalPINN(data, config, fit_initial)
    times = torch.tensor(data.times[:, None], dtype=DTYPE)
    observed = torch.tensor(data.observations, dtype=DTYPE)
    collocation = torch.linspace(0, data.times[-1], s["collocation_points"], dtype=DTYPE)[:, None]
    start = time.perf_counter()
    history, best_state = [], None
    best_loss, stale, best_iteration = float("inf"), 0, -1

    def total(parts):
        return sum(s[f"{key}_weight"] * parts[key] for key in ("data", "physics", "ic"))

    def record(stage, step):
        nonlocal best_loss, best_state, stale, best_iteration
        parts = loss_parts(model, times, observed, collocation, error_model)
        score = float(total(parts).detach())
        if not np.isfinite(score):
            raise RuntimeError("Nonfinite historical training loss")
        history.append({"stage": stage, "step": step, "total": score,
                        **{k: float(v.detach()) for k, v in parts.items()}})
        stale = 0 if score < best_loss - s["min_delta"] else stale + 1
        if score < best_loss:
            best_loss, best_state, best_iteration = score, copy.deepcopy(model.state_dict()), step
        return score

    optimizer = torch.optim.Adam(model.parameters(), lr=s["learning_rate"])
    for _ in range(s["warmup_steps"]):
        optimizer.zero_grad()
        data_loss = observation_loss(model(times) * model.scale, observed, model.scale, error_model)
        ic = ((model(times[:1]) - model.initial_values() / model.scale) ** 2).mean()
        warmup = s["data_weight"] * data_loss + s["ic_weight"] * ic
        warmup.backward()
        optimizer.step()
    record("joint_adam", 0)
    adam_stop = "maximum_steps"
    for step in range(1, s["adam_steps"] + 1):
        optimizer.zero_grad()
        objective = total(loss_parts(model, times, observed, collocation, error_model))
        if not torch.isfinite(objective):
            raise RuntimeError("Nonfinite historical Adam loss")
        objective.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), s["gradient_clip"])
        optimizer.step()
        if step % s["log_every"] == 0 or step == s["adam_steps"]:
            record("joint_adam", step)
            if stale >= s["patience"]:
                adam_stop = "training_plateau"
                break
    model.load_state_dict(best_state)
    closure_evaluations = 0
    lbfgs = torch.optim.LBFGS(model.parameters(), max_iter=s["lbfgs_steps"],
                             line_search_fn="strong_wolfe", tolerance_grad=1e-10,
                             tolerance_change=1e-12, history_size=50)

    def closure():
        nonlocal closure_evaluations
        lbfgs.zero_grad()
        objective = total(loss_parts(model, times, observed, collocation, error_model))
        if not torch.isfinite(objective):
            raise RuntimeError("Nonfinite historical L-BFGS loss")
        objective.backward()
        closure_evaluations += 1
        if closure_evaluations % 25 == 0:
            record("lbfgs", s["adam_steps"] + closure_evaluations)
        return objective

    if s["lbfgs_steps"]:
        lbfgs.step(closure)
        record("lbfgs_final", s["adam_steps"] + closure_evaluations)
    model.load_state_dict(best_state)
    with torch.no_grad():
        network_initial = (model(times[:1]) * model.scale).numpy()[0]
        ode_initial = model.initial_values().numpy()
    audit = {"seed": int(seed), "settings": dict(s), "trainable": config["trainable"],
             "fixed": model.fixed, "initial_guess": config["initial_guess"],
             "scale": data.scale.tolist(), "train_years": data.years.tolist(),
             "error_model": error_model, "fit_initial": fit_initial,
             "initial_bounds_factors": [0.5, 1.5] if fit_initial else None,
             "observed_initial": data.initial_state.tolist(), "ode_initial": ode_initial.tolist(),
             "network_initial": network_initial.tolist(),
             "network_minus_ode_initial": (network_initial - ode_initial).tolist(),
             "network_minus_observed_initial": (network_initial - data.initial_state).tolist(),
             "training_objective": best_loss, "best_iteration": best_iteration,
             "adam_stop": adam_stop, "lbfgs_closure_evaluations": closure_evaluations,
             "elapsed_seconds": time.perf_counter() - start,
             "selection_rule": "minimum weighted training loss within each variant; no held-out scores"}
    return model, history, audit
