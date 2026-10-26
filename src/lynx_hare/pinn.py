"""Inverse PINN trained only on a TrainingData object and fixed configuration."""
import copy
import random
import time
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from .model import NAMES, Parameters, rhs_torch

DTYPE = torch.float64


class InversePINN(nn.Module):
    def __init__(self, duration, scale, guess, bounds, trainable, width=48, depth=3):
        super().__init__()
        if duration <= 0 or not set(trainable).issubset(NAMES) or len(set(trainable)) != len(trainable):
            raise ValueError("Invalid duration or trainable parameter names")
        self.duration = float(duration)
        self.register_buffer("scale", torch.as_tensor(scale, dtype=DTYPE))
        self.fixed = {k: float(v) for k, v in guess.items() if k not in trainable}
        self.bounds = bounds
        self.raw = nn.ParameterDict()
        for k in trainable:
            lo, hi = bounds[k]
            if not 0 < lo < guess[k] < hi:
                raise ValueError(f"Initial guess for {k} must lie strictly within positive bounds")
            q = (guess[k] - lo) / (hi - lo)
            self.raw[k] = nn.Parameter(torch.tensor(np.log(q / (1 - q)), dtype=DTYPE))
        layers = [nn.Linear(1, width), nn.Tanh()]
        for _ in range(depth - 1):
            layers.extend((nn.Linear(width, width), nn.Tanh()))
        layers.append(nn.Linear(width, 2))
        self.network = nn.Sequential(*layers).to(dtype=DTYPE)
        for layer in self.network:
            if isinstance(layer, nn.Linear):
                nn.init.xavier_normal_(layer.weight)
                nn.init.zeros_(layer.bias)

    def parameter_values(self):
        values = dict(self.fixed)
        for k, raw in self.raw.items():
            lo, hi = self.bounds[k]
            values[k] = lo + (hi - lo) * torch.sigmoid(raw)
        return values

    def inferred(self):
        return Parameters(**{k: float(v.detach()) if isinstance(v, torch.Tensor) else float(v)
                             for k, v in self.parameter_values().items()})

    def forward(self, times):
        # The network is defined on scaled time [-1, 1]. Output positivity is strict.
        return F.softplus(self.network(2 * times / self.duration - 1)) + 1e-10

    def residuals(self, times):
        times = times.detach().clone().requires_grad_(True)
        normalized = self(times)
        derivatives = torch.cat([
            torch.autograd.grad(normalized[:, j:j+1], times,
                                torch.ones_like(normalized[:, j:j+1]), create_graph=True)[0]
            for j in range(2)], dim=1)
        return derivatives - rhs_torch(normalized * self.scale, self.parameter_values()) / self.scale


def loss_parts(model, times, observations, collocation, initial):
    data = ((model(times) - observations / model.scale) ** 2).mean()
    residual = model.residuals(collocation)
    physics_hare = residual[:, 0].square().mean()
    physics_lynx = residual[:, 1].square().mean()
    ic = ((model(torch.zeros((1, 1), dtype=DTYPE)) - initial / model.scale) ** 2).mean()
    return {"data": data, "physics": (physics_hare + physics_lynx) / 2,
            "physics_hare": physics_hare, "physics_lynx": physics_lynx, "ic": ic}


def fit_pinn(data, config, seed, training_overrides=None, initial_factor=1.0, trainable=None):
    """No truth, held-out observations, or held-out metrics enter optimization."""
    settings = {**config["training"], **(training_overrides or {})}
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(settings["threads"])
    torch.use_deterministic_algorithms(True)
    names = config["trainable"] if trainable is None else trainable
    guess = dict(config["initial_guess"])
    for k in names:
        lo, hi = config["bounds"][k]
        guess[k] = float(np.clip(guess[k] * initial_factor, lo + 1e-4, hi - 1e-4))
    model = InversePINN(data.times[-1], data.scale, guess, config["bounds"], names,
                        settings["width"], settings["depth"])
    times = torch.as_tensor(data.times[:, None], dtype=DTYPE)
    observed = torch.as_tensor(data.observations, dtype=DTYPE)
    initial = torch.as_tensor(data.initial_state, dtype=DTYPE)
    collocation = torch.linspace(0, data.times[-1], settings["collocation_points"], dtype=DTYPE)[:, None]
    history, best_state = [], None
    best_loss, stale, best_iteration = float("inf"), 0, -1
    start = time.perf_counter()

    def total(parts):
        return (settings["data_weight"] * parts["data"] + settings["physics_weight"] * parts["physics"]
                + settings["ic_weight"] * parts["ic"])

    def record(stage, step):
        nonlocal best_state, best_loss, stale, best_iteration
        parts = loss_parts(model, times, observed, collocation, initial)
        score = float(total(parts).detach())
        if not np.isfinite(score):
            raise RuntimeError("Nonfinite PINN training objective")
        history.append({"stage": stage, "step": step, "total": score,
                        **{k: float(v.detach()) for k, v in parts.items()}})
        improved_materially = score < best_loss - settings["min_delta"]
        stale = 0 if improved_materially else stale + 1
        if score < best_loss:
            best_loss, best_state, best_iteration = score, copy.deepcopy(model.state_dict()), step
        return score

    optimizer = torch.optim.Adam(model.parameters(), lr=settings["learning_rate"])
    # Warmup fits states before physics is introduced. No parameters are inferred in warmup.
    for _ in range(settings["warmup_steps"]):
        optimizer.zero_grad()
        warm = ((model(times) - observed / model.scale) ** 2).mean()
        warm = warm + settings["ic_weight"] * ((model(times[:1]) - initial / model.scale) ** 2).mean()
        warm.backward()
        optimizer.step()
    record("joint_adam", 0)
    adam_stop = "maximum_steps"
    for step in range(1, settings["adam_steps"] + 1):
        optimizer.zero_grad()
        objective = total(loss_parts(model, times, observed, collocation, initial))
        if not torch.isfinite(objective):
            raise RuntimeError("Nonfinite PINN loss")
        objective.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), settings["gradient_clip"])
        optimizer.step()
        if step % settings["log_every"] == 0 or step == settings["adam_steps"]:
            record("joint_adam", step)
            if stale >= settings["patience"]:
                adam_stop = "training_plateau"
                break
    model.load_state_dict(best_state)
    closure_evaluations = 0
    optimizer2 = torch.optim.LBFGS(model.parameters(), max_iter=settings["lbfgs_steps"],
                                  line_search_fn="strong_wolfe", tolerance_grad=1e-10,
                                  tolerance_change=1e-12, history_size=50)

    def closure():
        nonlocal closure_evaluations
        optimizer2.zero_grad()
        objective = total(loss_parts(model, times, observed, collocation, initial))
        if not torch.isfinite(objective):
            raise RuntimeError("Nonfinite L-BFGS loss")
        objective.backward()
        closure_evaluations += 1
        if closure_evaluations % 25 == 0:
            record("lbfgs", settings["adam_steps"] + closure_evaluations)
        return objective

    if settings["lbfgs_steps"]:
        optimizer2.step(closure)
        record("lbfgs_final", settings["adam_steps"] + closure_evaluations)
    model.load_state_dict(best_state)
    audit = {"seed": seed, "settings": settings, "trainable": names, "initial_guess": guess,
             "fixed": model.fixed, "scale": data.scale.tolist(), "train_years": data.years.tolist(),
             "training_objective": best_loss, "best_iteration": best_iteration,
             "adam_stop": adam_stop, "lbfgs_iterations": optimizer2.state.get(next(iter(model.parameters())), {}).get("n_iter", 0),
             "lbfgs_closure_evaluations": closure_evaluations,
             "elapsed_seconds": time.perf_counter() - start,
             "selection_rule": "minimum weighted training loss; held-out data never used"}
    return model, history, audit
