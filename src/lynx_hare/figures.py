"""EPS and PNG figures; captions are in docs/figure_captions.md."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, FormatStrFormatter
from .model import Parameters, solve


def make_figures(root, output, truth, observations, summaries, scores):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "savefig.dpi": 180, "ps.fonttype": 42, "pdf.fonttype": 42})
    figdir = output / "figures"
    figdir.mkdir(exist_ok=True)
    colors = ["#197278", "#C4532E", "#4E3F82"]

    def save(fig, name):
        fig.savefig(figdir / f"{name}.png", bbox_inches="tight", facecolor="white")
        fig.savefig(figdir / f"{name}.eps", bbox_inches="tight", facecolor="white")
        fig.savefig(figdir / f"{name}.pdf", bbox_inches="tight", facecolor="white")
        plt.close(fig)

    selected_id = json.loads((output / "selected_run.json").read_text())["run_id"]
    folder = output / "runs" / selected_id
    pinn = np.loadtxt(folder / "ode_dense.csv", delimiter=",", skiprows=1)
    network = np.loadtxt(folder / "network_train.csv", delimiter=",", skiprows=1)
    baseline = json.loads((output / "least_squares.json").read_text())["parameters"]
    config = json.loads((root / "configs/synthetic.json").read_text())
    grid = pinn[:, 0] - 1900
    base = solve(grid, observations[0], Parameters(**baseline), **config["solver"])
    exact = solve(grid, config["initial_state"], Parameters(**config["truth"]), **config["solver"])
    fig, axes = plt.subplots(2, 1, figsize=(9, 6.5), sharex=True, layout="constrained")
    for j, ax in enumerate(axes):
        ax.axvspan(1915, 1920, color="#EEEEEE", label="Held-out period")
        ax.plot(grid + 1900, exact[:, j], color="black", lw=1.4, label="Synthetic latent truth")
        ax.scatter(np.arange(1900, 1916), observations[:16, j], s=21, color=colors[0], label="Training observations", zorder=4)
        ax.scatter(np.arange(1916, 1921), observations[16:, j], s=30, marker="x", color="black", label="Held-out observations", zorder=4)
        ax.plot(pinn[:, 0], pinn[:, j+1], color=colors[1], lw=1.6, label="PINN-derived ODE")
        ax.plot(grid + 1900, base[:, j], color=colors[2], ls="--", lw=1.5, label="Least-squares ODE")
        ax.set_ylabel(["Hare index", "Lynx index"][j])
        ax.grid(color="#E5E5E5", linewidth=0.6)
    axes[0].legend(ncol=3, fontsize=8, frameon=False)
    axes[0].set_title("Synthetic annual observations and frozen ODE forecasts")
    axes[-1].set_xlabel("Year label (synthetic data)")
    save(fig, "forecast_comparison")

    history = np.genfromtxt(folder / "training.csv", delimiter=",", names=True, dtype=None, encoding="utf-8")
    fig, ax = plt.subplots(figsize=(8, 4), layout="constrained")
    for name, color in zip(("total", "data", "physics", "ic"), ("black", *colors)):
        ax.semilogy(history["step"], np.maximum(history[name], 1e-14), label=name, color=color)
    ax.set(xlabel="Joint Adam steps + L-BFGS closure evaluations", ylabel="Loss", title=f"Synthetic training losses ({selected_id})")
    ax.legend(frameon=False, ncol=4)
    ax.grid(color="#E5E5E5")
    save(fig, "training_losses")

    fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
    for j, ax in enumerate(axes):
        ax.plot(network[:, 0], network[:, j+1], color=colors[0], label="PINN state approximation")
        train_grid = pinn[pinn[:, 0] <= 1915]
        ax.plot(train_grid[:, 0], train_grid[:, j+1], color=colors[1], ls="--", label="ODE with inferred parameters")
        ax.scatter(np.arange(1900, 1916), observations[:16, j], color="black", s=15, label="Training observations")
        ax.set(xlabel="Synthetic year label", ylabel=["Hare index", "Lynx index"][j])
    axes[0].legend(frameon=False, fontsize=8)
    fig.suptitle("Training consistency between network and ODE")
    save(fig, "network_ode_consistency")

    fig, axes = plt.subplots(1, 3, figsize=(10, 3.8), layout="constrained")
    for j, name in enumerate(config["trainable"]):
        ax = axes[j]
        for x, case in enumerate(("dense_clean", "dense_noisy", "annual_noisy")):
            values = [100 * abs(s["parameters"][name] / config["truth"][name] - 1)
                      for s in summaries if s["case"] == case and s["variant"] == "default"]
            ax.scatter(np.full(len(values), x) + np.linspace(-0.08, 0.08, len(values)), values, color=colors[x], s=35)
            ax.plot([x-0.16, x+0.16], [np.mean(values)]*2, color="black", lw=2)
        ax.set_xticks(range(3), ["Dense\nclean", "Dense\n3% noise", "Annual\n3% noise"])
        ax.set(title=name, ylabel="Absolute relative error (%)")
    fig.suptitle("Synthetic parameter recovery across training seeds")
    save(fig, "parameter_recovery")

    fig, axes = plt.subplots(1, 2, figsize=(9, 3.8), layout="constrained")
    variants = [s for s in summaries if s["case"] == "annual_noisy" and (s["variant"] != "default" or s["seed"] == 17)]
    labels = ["default" if s["variant"] == "default" else s["variant"].replace("_", " ") for s in variants]
    for j, ax in enumerate(axes):
        for i, s in enumerate(variants):
            forecast = np.loadtxt(output / "runs" / s["run_id"] / "forecast.csv", delimiter=",", skiprows=1)
            ax.plot(forecast[16:, 0], forecast[16:, j+1], marker="o", ms=3, label=labels[i])
        ax.plot(np.arange(1916, 1921), truth[16:, j], color="black", ls="--", label="Synthetic truth")
        ax.set(xlabel="Synthetic held-out year", ylabel=["Hare index", "Lynx index"][j])
        ax.xaxis.set_major_locator(MaxNLocator(nbins=4, integer=True))
        ax.xaxis.set_major_formatter(FormatStrFormatter("%.0f"))
    axes[0].legend(frameon=False, fontsize=7)
    fig.suptitle("Forecast sensitivity (training configurations fixed before scoring)")
    save(fig, "sensitivity")

    spectrum = json.loads((output / "identifiability.json").read_text())
    fig, ax = plt.subplots(figsize=(6.8, 3.8), layout="constrained")
    for key, label, color in (("three_parameters", "Estimate r, a, m", colors[0]), ("six_parameters", "Vary all six parameters", colors[1])):
        singular = spectrum[key]["singular_values"]
        ax.semilogy(np.arange(1, len(singular)+1), singular, "o-", color=color, label=label)
    ax.set(xlabel="Singular value index", ylabel="Scaled trajectory sensitivity", title="Local identifiability diagnostic (synthetic training data)")
    ax.legend(frameon=False)
    save(fig, "identifiability")

    check = np.loadtxt(folder / "residual_check.csv", delimiter=",", skiprows=1)
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6), layout="constrained")
    for j, ax in enumerate(axes):
        ax.plot(check[:, 0], check[:, j+1], color=colors[j])
        ax.axhline(0, color="black", lw=0.7)
        ax.set(xlabel="Synthetic training year", ylabel="Scaled residual (1/year)", title=["Hare ODE residual", "Lynx ODE residual"][j])
        ax.xaxis.set_major_locator(MaxNLocator(nbins=5, integer=True))
        ax.xaxis.set_major_formatter(FormatStrFormatter("%.0f"))
    save(fig, "residual_check")
