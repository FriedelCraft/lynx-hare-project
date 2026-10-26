"""Training-only diagnostic; does not inspect any held-out observations."""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
from lynx_hare.data import synthetic, TrainingData
from lynx_hare.pinn import fit_pinn

root = Path(__file__).resolve().parents[1]
config = json.loads((root / "configs/synthetic.json").read_text())
times = np.linspace(0, 15, 61)
truth, observations = synthetic(config, times, noise_fraction=0.0)
data = TrainingData(times + 1900, observations, 1900)
model, history, audit = fit_pinn(data, config, 17)
print(json.dumps({"inferred": model.inferred().to_dict(), "truth": config["truth"],
                  "audit": audit, "loss": history[-1]}, indent=2), flush=True)
