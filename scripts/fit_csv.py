"""Fit only training CSV rows, freeze parameters, then export ODE forecasts."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
from lynx_hare.data import read_training, write_csv
from lynx_hare.pinn import fit_pinn
from lynx_hare.model import solve
from lynx_hare.experiments import save_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--kind", choices=["synthetic", "historical"], required=True)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--start-year", type=int, default=1900)
    parser.add_argument("--train-end", type=int, default=1915)
    parser.add_argument("--forecast-end", type=int, default=1920)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new output directory to preserve existing experiment evidence")
    if not args.start_year < args.train_end < args.forecast_end:
        parser.error("Require start-year < train-end < forecast-end")
    config = json.loads(args.config.read_text())
    config.pop("truth", None)  # Generating parameters have no role in inference.
    data = read_training(args.csv, args.start_year, args.train_end)
    if data.years[-1] != args.train_end:
        parser.error("Training data must end at the declared train-end year")
    model, history, audit = fit_pinn(data, config, args.seed)
    args.output.mkdir(parents=True)
    save_json(args.output / "parameters.json", {"kind": args.kind,
              "parameters": model.inferred().to_dict(), "audit": audit})
    write_csv(args.output / "training.csv", list(history[0]), [list(r.values()) for r in history])
    years = np.arange(args.start_year, args.forecast_end + 1)
    states = solve(years - args.start_year, data.initial_state, model.inferred(), **config["solver"])
    heldout = years > args.train_end
    write_csv(args.output / "forecast.csv", ["Year", "Hare", "Lynx"],
              np.column_stack((years[heldout], states[heldout])))
    print(f"Frozen parameters and ODE forecasts saved to {args.output}")


if __name__ == "__main__":
    main()
