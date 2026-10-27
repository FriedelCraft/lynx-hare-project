"""Publication figures for Rishi's simulation section (EPS-safe: no transparency)."""
import numpy as np
import matplotlib.pyplot as plt

from . import simulation as sim
from . import stability as st
from .model import rhs

HARE, LYNX, EQ = "#1f5fa8", "#c0392b", "#111111"
NULL_H, NULL_P, GREY = "#2e8b57", "#8e44ad", "#999999"

STYLE = {"font.size": 11, "axes.grid": True, "grid.color": "#dddddd",
         "legend.framealpha": 1.0, "savefig.bbox": "tight"}


def save(fig, stem, figures_dir, graphs_dir=None):
    """PNG/EPS/PDF into figures_dir; EPS/PDF only into graphs_dir (report convention)."""
    for folder, exts in ((figures_dir, ("png", "eps", "pdf")), (graphs_dir, ("eps", "pdf"))):
        if folder is None:
            continue
        folder.mkdir(parents=True, exist_ok=True)
        for ext in exts:
            fig.savefig(folder / f"{stem}.{ext}", dpi=200 if ext == "png" else None)


def solver_validation(q=sim.LV_DEFAULT, y0=(3.0, 1.0), t_end=100.0, h=0.01):
    """Fig 1: RK45 keeps the Lotka-Volterra invariant constant; Euler drifts outward."""
    t = np.linspace(0, t_end, 4001)
    rk = sim.integrate(q, y0, (0, t_end), t_eval=t, fun=sim.lotka_volterra_rhs).y
    te, ye = sim.euler(sim.lotka_volterra_rhs, y0, t_end, h, q)
    V0 = sim.lotka_volterra_invariant(*y0, q)
    drift_rk = sim.lotka_volterra_invariant(*rk, q) - V0
    drift_eu = sim.lotka_volterra_invariant(ye[:, 0], ye[:, 1], q) - V0

    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].plot(ye[:, 0], ye[:, 1], color=GREY, lw=1, label=f"Euler, h = {h}")
    ax[0].plot(*rk, color=HARE, lw=2, label="RK45")
    ax[0].set(xlabel="prey H", ylabel="predator P", title="Lotka-Volterra orbit")
    ax[0].legend()
    ax[1].plot(t, drift_rk, color=HARE, lw=2, label="RK45")
    ax[1].plot(te, drift_eu, color=GREY, lw=1, label=f"Euler, h = {h}")
    ax[1].set(xlabel="time t", ylabel="V(t) - V(0)", title="Drift of the conserved quantity")
    ax[1].legend()
    fig.tight_layout()
    return fig, dict(max_drift_rk45=float(np.abs(drift_rk).max()),
                     max_drift_euler=float(np.abs(drift_eu).max()))


def _phase_portrait(ax, p, y, title):
    Hs, Ps = st.coexistence_prey(p), st.coexistence_predator(p)
    Hmax = max(p.K, y[0].max()) * 1.05
    Pmax = max(y[1].max(), Ps) * 1.25
    Hg, Pg = np.meshgrid(np.linspace(0.5, Hmax, 18), np.linspace(0.3, Pmax, 14))
    dH, dP = rhs(0, [Hg, Pg], p)
    norm = np.hypot(dH / Hmax, dP / Pmax) + 1e-12
    ax.quiver(Hg, Pg, dH / norm / Hmax, dP / norm / Pmax, color="#b5b5b5",
              angles="xy", scale=30, width=0.003)
    Hn = np.linspace(0, p.K, 400)
    ax.plot(Hn, p.r / p.a * (1 - Hn / p.K) * (p.b + Hn), color=NULL_H, lw=2, label="prey nullcline")
    ax.axvline(Hs, color=NULL_P, lw=2, ls="--", label="predator nullcline H = H*")
    ax.axvline((p.K - p.b) / 2, color=NULL_H, lw=1, ls=":", label="hump peak (K - b)/2")
    ax.plot(y[0], y[1], color=HARE, lw=1.1, label="trajectory from (20, 5)")
    stable = p.K < st.hopf_threshold(p)
    ax.plot(Hs, Ps, "o", ms=8, mec=EQ, mfc=EQ if stable else "white", mew=1.5, label="E*")
    ax.set(xlim=(0, Hmax), ylim=(0, Pmax), xlabel="hare H (thousand pelts)",
           ylabel="lynx P (thousand pelts)", title=title)


def regimes(base, shown=(("B", 60, 120), ("C", 85, 600), ("E", 95, 600), ("F", 150, 200)), y0=sim.Y0):
    """Fig 2: time series (top) and phase portraits (bottom) on both sides of K_H."""
    KH = st.hopf_threshold(base)
    fig, axes = plt.subplots(2, len(shown), figsize=(5 * len(shown), 8.5))
    for j, (label, K, T) in enumerate(shown):
        p = sim.with_K(base, K)
        t = np.linspace(0, T, 30001)
        y = sim.integrate(p, y0, (0, T), t_eval=t).y
        title = f"{label}: K = {K:g} ({'below' if K < KH else 'above'} K_H = {KH:g})"
        axes[0, j].plot(t, y[0], color=HARE, lw=1.1, label="hare H")
        axes[0, j].plot(t, y[1], color=LYNX, lw=1.1, label="lynx P")
        axes[0, j].set(xlabel="time t (years)", ylabel="thousand pelts", title=title)
        axes[0, j].legend(loc="upper right")
        _phase_portrait(axes[1, j], p, y, title)
    axes[1, 0].legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    return fig


def limit_cycle_attracts(base, K=150.0, outside=(145.0, 45.0), T=300.0):
    """Fig 3: starts inside and outside the cycle converge to the same loop."""
    p = sim.with_K(base, K)
    Hs, Ps = st.coexistence_prey(p), st.coexistence_predator(p)
    t = np.linspace(0, T, 60001)
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.6))
    last_peaks = {}
    for name, y0, c in (("start inside (next to E*)", (1.02 * Hs, Ps), HARE),
                        ("start outside", outside, LYNX)):
        y = sim.integrate(p, y0, (0, T), t_eval=t).y
        ax[0].plot(y[0], y[1], color=c, lw=1, label=name)
        ax[0].plot(*y0, "s", color=c, ms=7)
        peaks = y[0][sim.local_maxima(y[0])]
        ax[1].plot(np.arange(1, len(peaks) + 1), peaks, "o-", color=c, ms=4, label=name)
        last_peaks[name] = peaks[-3:].tolist()
    ax[0].plot(Hs, Ps, "o", ms=8, mec=EQ, mfc="white", mew=1.5, label="E* (unstable)")
    ax[0].set(xlabel="hare H (thousand pelts)", ylabel="lynx P (thousand pelts)",
              title=f"K = {K:g}: both trajectories reach the same loop")
    ax[0].legend(fontsize=9)
    ax[1].set(xlabel="peak number", ylabel="hare peak value", title="Successive hare peaks converge")
    ax[1].legend(fontsize=9)
    fig.tight_layout()
    return fig, last_peaks


def eigenvalues_vs_K(base, K_values):
    """Fig 4: real and imaginary parts of the eigenvalues of J(E*) against K."""
    KH = st.hopf_threshold(base)
    omega0 = 2 * np.pi / st.onset_period(base)
    re, im = [], []
    for K in K_values:
        p = sim.with_K(base, K)
        lam = np.linalg.eigvals(st.jacobian(st.coexistence_prey(p), st.coexistence_predator(p), p))
        re.append(lam.real.max())
        im.append(np.abs(lam.imag).max())
    re, im = np.array(re), np.array(im)
    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
    ax[0].plot(K_values, re, color=HARE, lw=2)
    ax[0].axhline(0, color="black", lw=1)
    ax[0].axvline(KH, color=LYNX, ls="--", label=f"K_H = {KH:g}")
    ax[0].set(xlabel="carrying capacity K", ylabel="max Re(lambda)", title="Real part of the eigenvalues at E*")
    ax[0].legend()
    ax[1].plot(K_values, im, color=NULL_P, lw=2)
    ax[1].axvline(KH, color=LYNX, ls="--", label=f"K_H = {KH:g}")
    ax[1].axhline(omega0, color="#777777", ls=":", label=f"omega_0 = {omega0:.3f}")
    ax[1].set(xlabel="carrying capacity K", ylabel="|Im(lambda)|", title="Imaginary part of the eigenvalues at E*")
    ax[1].legend()
    fig.tight_layout()
    focus_K = float(np.asarray(K_values)[np.argmax(im > 0)])
    return fig, dict(node_to_focus_K=focus_K)


def bifurcation(base, sweep):
    """Fig 5: post-transient max/min of H and P against K."""
    K = sweep["K"]
    KH = st.hopf_threshold(base)
    Hs = st.coexistence_prey(base)
    P_eq = np.array([st.coexistence_predator(sim.with_K(base, k)) for k in K])
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    for a, mx, mn, eq, name, c in ((ax[0], sweep["Hmax"], sweep["Hmin"], np.full_like(K, Hs), "hare H", HARE),
                                   (ax[1], sweep["Pmax"], sweep["Pmin"], P_eq, "lynx P", LYNX)):
        stable = K <= KH
        a.plot(K[stable], eq[stable], color="black", lw=2, label="stable E*")
        a.plot(K[~stable], eq[~stable], color="black", lw=1.5, ls="--", label="unstable E*")
        a.plot(K, mx, "o", color=c, ms=3, label="max on attractor")
        a.plot(K, mn, "^", color=c, ms=3, label="min on attractor")
        a.axvline(KH, color="#777777", ls=":", label=f"K_H = {KH:g}")
        a.set(xlabel="carrying capacity K", ylabel=f"{name} (thousand pelts)",
              title=f"Bifurcation diagram: {name.split()[0]}")
        a.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    return fig


def amplitude_and_period(law):
    """Fig 6: sqrt(K - K_H) amplitude law (log-log) and period approaching T_0."""
    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
    dK = law["dK"]
    ax[0].loglog(dK, law["amplitude"], "o", color=HARE, label="simulated half-amplitude")
    ax[0].loglog(dK, law["coefficient"] * dK ** law["slope"], color=LYNX, lw=1.5,
                 label=f"fit: slope {law['slope']:.3f}")
    ax[0].set(xlabel="K - K_H", ylabel="half-amplitude of H", title="Cycle size grows like sqrt(K - K_H)")
    ax[0].legend()
    ax[1].plot(dK, law["period"], "o-", color=NULL_P, label="simulated period")
    ax[1].axhline(law["onset_period"], color="#777777", ls="--", label=f"T_0 = {law['onset_period']:.2f} yr")
    ax[1].set(xlabel="K - K_H", ylabel="period (years)", title="Period tends to T_0 as K -> K_H")
    ax[1].legend()
    fig.tight_layout()
    return fig
