"""Validated training contract and independently generated synthetic observations."""
from dataclasses import dataclass
from pathlib import Path
import csv
import numpy as np
from .model import Parameters, solve


@dataclass
class TrainingData:
    years: np.ndarray
    observations: np.ndarray
    time_origin: float

    def __post_init__(self):
        self.years = np.asarray(self.years, dtype=float)
        self.observations = np.asarray(self.observations, dtype=float)
        if (self.years.ndim != 1 or len(self.years) < 2
                or self.observations.shape != (len(self.years), 2)
                or not np.isfinite(self.years).all()
                or not np.isfinite(self.observations).all()
                or np.any(np.diff(self.years) <= 0)
                or np.any(self.observations <= 0)
                or not np.isfinite(self.time_origin)
                or self.years[0] != self.time_origin):
            raise ValueError("Training data require increasing years and positive finite Hare/Lynx observations, starting at time_origin")

    @property
    def times(self):
        return self.years - self.time_origin

    @property
    def scale(self):
        # This method has no access to test observations or generating parameters.
        return self.observations.max(axis=0)

    @property
    def initial_state(self):
        return self.observations[0].copy()


def write_csv(path, columns, values):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(values)


def read_training(path, time_origin=1900, train_end=1915):
    with Path(path).open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    values = np.array([[float(r[k]) for k in ("Year", "Hare", "Lynx")] for r in rows])
    values = values[values[:, 0] <= train_end]
    return TrainingData(values[:, 0], values[:, 1:], time_origin)


def synthetic(config, times, noise_fraction=None, seed=None):
    """Noise is multiplicative Gaussian with exact controlled initial condition.

    In this synthetic experiment the initial state is treated as measured exactly.
    This is an explicit experimental assumption, not a claim about pelt data.
    """
    noise = config["noise_fraction"] if noise_fraction is None else noise_fraction
    if noise < 0:
        raise ValueError("noise_fraction cannot be negative")
    states = solve(times, config["initial_state"], Parameters(**config["truth"]), **config["solver"])
    rng = np.random.default_rng(config["data_seed"] if seed is None else seed)
    observed = states * (1 + noise * rng.normal(size=states.shape))
    observed = np.maximum(observed, 1e-8)
    observed[0] = states[0]
    return states, observed
