"""Numerical verification for Joel's section. Run: python scripts/joel_stability_analysis.py
Model: Rosenzweig-MacArthur (shared src/lynx_hare/model.py).

Illustrative parameters (NOT fitted): H, P in thousands of pelts, t in years.
Prints eigenvalue table, first Lyapunov coefficient at K_H, simulated
post-transient amplitudes/periods, and writes the analytic figures.
"""
import json
import sys
from pathlib import Path
import numpy as np
import sympy as sp
from scipy.integrate import solve_ivp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = dict(r=1.5, a=4.0, b=30.0, e=0.4, m=0.8)   # e*a = 1.6 = 2m  ->  H* = b
RTOL, ATOL = 1e-10, 1e-12
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lynx_hare.model import Parameters, rhs as shared_rhs  # noqa: E402  single shared RHS
OUT = ROOT / "results" / "stability"
FIG = OUT / "figures"
GRAPHS = ROOT / "report" / "graphs"


def Hstar(p): return p["m"] * p["b"] / (p["e"] * p["a"] - p["m"])
def Pstar(p, K): h = Hstar(p); return p["r"] / p["a"] * (1 - h / K) * (p["b"] + h)
def KH(p): ea = p["e"] * p["a"]; return p["b"] * (ea + p["m"]) / (ea - p["m"])


def rhs(t, y, p, K):
    """Thin wrapper so every simulation here uses the team's shared model.rhs."""
    return shared_rhs(t, y, Parameters(K=K, **p))


def jac(H, P, p, K):
    r, a, b, e, m = (p[k] for k in "rabem")
    return np.array([[r * (1 - 2 * H / K) - a * b * P / (b + H) ** 2, -a * H / (b + H)],
                     [e * a * b * P / (b + H) ** 2, e * a * H / (b + H) - m]])


def classify(ev):
    re, im = ev.real, ev.imag
    if np.all(np.abs(im) > 1e-12):
        if abs(re[0]) < 1e-9: return "centre (linear) / Hopf point"
        return "stable focus" if re[0] < 0 else "unstable focus"
    if re.min() < 0 < re.max(): return "saddle"
    if abs(re).min() < 1e-9: return "non-hyperbolic"
    return "stable node" if re.max() < 0 else "unstable node"


def first_lyapunov(p, K):
    """Kuznetsov (2004) eq. (3.20) for the first Lyapunov coefficient l1."""
    H, P = sp.symbols("H P")
    r, a, b, e, m = (sp.nsimplify(p[k]) for k in "rabem")
    F = sp.Matrix([r * H * (1 - H / K) - a * H * P / (b + H), e * a * H * P / (b + H) - m * P])
    x0 = {H: sp.nsimplify(Hstar(p)), P: sp.nsimplify(Pstar(p, K))}
    v = [H, P]
    A = np.array(F.jacobian(v).subs(x0), dtype=float)
    d2 = [[[float(sp.diff(F[i], v[j], v[k]).subs(x0)) for k in range(2)] for j in range(2)] for i in range(2)]
    d3 = [[[[float(sp.diff(F[i], v[j], v[k], v[l]).subs(x0)) for l in range(2)] for k in range(2)]
           for j in range(2)] for i in range(2)]
    B = lambda x, y: np.array([sum(d2[i][j][k] * x[j] * y[k] for j in range(2) for k in range(2)) for i in range(2)])
    C = lambda x, y, z: np.array([sum(d3[i][j][k][l] * x[j] * y[k] * z[l] for j in range(2) for k in range(2)
                                      for l in range(2)) for i in range(2)])
    w, V = np.linalg.eig(A)
    i = np.argmax(w.imag); om = w[i].imag; q = V[:, i]
    wT, W = np.linalg.eig(A.T)
    j = np.argmin(wT.imag); pv = W[:, j]
    pv = pv / np.conj(np.conj(pv) @ q)          # normalise <p,q> = conj(p).q = 1
    ip = lambda u, v_: np.conj(u) @ v_
    qb = np.conj(q)
    term = (ip(pv, C(q, q, qb))
            - 2 * ip(pv, B(q, np.linalg.solve(A, B(q, qb))))
            + ip(pv, B(qb, np.linalg.solve(2j * om * np.eye(2) - A, B(q, q)))))
    return float(np.real(term) / (2 * om)), om, A


def post_transient(p, K, T_burn=3000.0, T_rec=200.0, y0=None):
    if y0 is None:
        y0 = [1.1 * Hstar(p), 1.1 * Pstar(p, K) if Pstar(p, K) > 0 else 5.0]
    s1 = solve_ivp(rhs, (0, T_burn), y0, args=(p, K), method="RK45", rtol=RTOL, atol=ATOL)
    t = np.linspace(0, T_rec, 20001)
    s2 = solve_ivp(rhs, (0, T_rec), s1.y[:, -1], args=(p, K), method="RK45", rtol=RTOL, atol=ATOL, t_eval=t)
    H, P = s2.y
    # period from successive upward crossings of H through its mean
    mu = H.mean(); idx = np.where((H[:-1] < mu) & (H[1:] >= mu))[0]
    per = float(np.diff(t[idx]).mean()) if len(idx) > 2 and H.max() - H.min() > 1e-3 else float("nan")
    # lag: time from hare peak to next lynx peak
    lag = float("nan")
    if not np.isnan(per):
        ih = np.argmax(H[: int(len(t) * per / T_rec) + 1]);
        seg = P[ih: ih + int(len(t) * per / T_rec)]
        lag = float(t[ih + np.argmax(seg)] - t[ih])
    return dict(Hmin=H.min(), Hmax=H.max(), Pmin=P.min(), Pmax=P.max(), period=per, lag=lag)


if __name__ == "__main__":
    p = BASE
    hs, kh = Hstar(p), KH(p)
    print(f"H* = {hs:.4f}, K_H = {kh:.4f}, persistence threshold K = H* = {hs:.4f}")
    print(f"omega0 = sqrt(r m b / K_H) = {np.sqrt(p['r']*p['m']*p['b']/kh):.4f}, "
          f"T0 = {2*np.pi/np.sqrt(p['r']*p['m']*p['b']/kh):.3f} yr")

    l1, om, A = first_lyapunov(p, kh)
    print(f"At K = K_H: J = {A.round(5).tolist()}, omega = {om:.5f}, l1 = {l1:.6e}")
    l1b, *_ = first_lyapunov(dict(p, r=0.7, m=0.5, b=20.0), KH(dict(p, r=0.7, m=0.5, b=20.0)))
    print(f"Second parameter set l1 = {l1b:.6e}")

    regimes = [("A", 25.0, "predator cannot persist"), ("B", 60.0, "stable coexistence"),
               ("C", 85.0, "just below Hopf: slow damping"), ("D", 90.0, "Hopf point"),
               ("E", 95.0, "just above Hopf: small cycle"), ("F", 150.0, "well above: large cycle")]
    rows = []
    for lab, K, note in regimes:
        Ps = Pstar(p, K)
        ev0 = np.linalg.eigvals(jac(0, 0, p, K)); ev1 = np.linalg.eigvals(jac(K, 0, p, K))
        row = dict(label=lab, K=K, note=note, Pstar=Ps,
                   E0=classify(ev0), E1=classify(ev1), E1_eigs=sorted(ev1.real.tolist()))
        if Ps > 0:
            ev = np.linalg.eigvals(jac(hs, Ps, p, K))
            J = jac(hs, Ps, p, K)
            row.update(Estar=classify(ev), eigs=[complex(x) for x in ev], tr=np.trace(J), det=np.linalg.det(J))
        sim = post_transient(p, K, y0=[20.0, 5.0])
        row.update(sim)
        rows.append(row)
        print(f"\n[{lab}] K={K}: {note}")
        print(f"   P* = {Ps:.3f}; E0: {row['E0']}; E1: {row['E1']} eig={np.round(ev1,4)}")
        if Ps > 0:
            print(f"   E*: {row['Estar']}, eig={np.round(ev,5)}, tr={row['tr']:.5f}, det={row['det']:.5f}")
        print(f"   sim (t>3000 yr): H in [{sim['Hmin']:.3f},{sim['Hmax']:.3f}], P in [{sim['Pmin']:.3f},{sim['Pmax']:.3f}], "
              f"period={sim['period']:.3f}, lag={sim['lag']:.3f}")

    # amplitude scaling near onset (supercritical => amp ~ sqrt(K-K_H))
    print("\nAmplitude scaling just above K_H:")
    amps = []
    for dK in [0.5, 1.0, 2.0, 4.0, 8.0]:
        s = post_transient(p, kh + dK, T_burn=20000.0)
        A_ = (s["Hmax"] - s["Hmin"]) / 2; amps.append((dK, A_))
        print(f"   K-K_H={dK:4.1f}: half-amplitude H = {A_:.4f}, A/sqrt(dK) = {A_/np.sqrt(dK):.4f}, period={s['period']:.3f}")
    slope = np.polyfit(np.log([x for x, _ in amps]), np.log([y for _, y in amps]), 1)[0]
    print(f"   log-log slope = {slope:.3f} (theory 0.5)")

    # ---------------- figures (analytic, EPS + PDF + PNG) ----------------
    FIG.mkdir(parents=True, exist_ok=True)

    def save(fig, name):
        for ext in ("eps", "pdf", "png"):
            fig.savefig(FIG / f"joel_{name}.{ext}", dpi=200)
        for ext in ("eps", "pdf"):          # report convention: EPS + PDF companion in report/graphs
            fig.savefig(GRAPHS / f"joel_{name}.{ext}", dpi=200)

    plt.rcParams.update({"font.size": 10, "font.family": "serif", "mathtext.fontset": "cm"})
    ink, muted = "#222222", "#6b6b6b"
    c1, c2, c3 = "#2a6fbb", "#c0392b", "#7a7a7a"

    # Fig 1: nullclines for K below and above K_H
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.1), sharey=True)
    for ax, K, ttl in [(axs[0], 60.0, r"$K=60<K_H$ (stable)"), (axs[1], 150.0, r"$K=150>K_H$ (unstable)")]:
        Hg = np.linspace(0, K, 400)
        ax.plot(Hg, p["r"] / p["a"] * (1 - Hg / K) * (p["b"] + Hg), color=c1, lw=2, label=r"prey nullcline $\dot H=0$")
        ax.axvline(hs, color=c2, lw=2, label=r"predator nullcline $H=H^*$")
        ax.axvline((K - p["b"]) / 2, color=c3, lw=1, ls=":", label=r"hump $H=(K-b)/2$")
        ax.plot(hs, Pstar(p, K), "o", color=ink, ms=6, mfc="white" if K > kh else ink, zorder=5)
        ax.plot([0, K], [0, 0], "o", color=ink, ms=4)
        Hq, Pq = np.meshgrid(np.linspace(4, K * 0.97, 13), np.linspace(1, 50, 11))
        feed = p["a"] * Hq * Pq / (p["b"] + Hq)
        U, Vv = p["r"] * Hq * (1 - Hq / K) - feed, p["e"] * feed - p["m"] * Pq; N = np.hypot(U, Vv) + 1e-12
        ax.quiver(Hq, Pq, U / N, Vv / N, color="#b5b5b5", width=0.004, scale=28)
        ax.set_title(ttl, fontsize=10); ax.set_xlabel(r"hare $H$ (thousand pelts)")
        ax.set_xlim(0, K); ax.set_ylim(0, 52)
        for s_ in ("top", "right"): ax.spines[s_].set_visible(False)
    axs[0].set_ylabel(r"lynx $P$ (thousand pelts)")
    axs[0].legend(loc="upper right", fontsize=7.5, frameon=False)
    fig.tight_layout()
    save(fig, "nullclines")

    # Fig 2: stability regions in (K, m) plane
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    ea, b = p["e"] * p["a"], p["b"]
    Kg = np.linspace(1, 300, 600)
    m_ext = ea * Kg / (b + Kg); m_hopf = np.clip(ea * (Kg - b) / (Kg + b), 0, None)
    ax.fill_between(Kg, m_ext, ea, color="#e8e8e8"); ax.fill_between(Kg, m_hopf, m_ext, color="#d6e6f5")
    ax.fill_between(Kg, 0, m_hopf, color="#f6d9d4")
    ax.plot(Kg, m_ext, color=ink, lw=1.3); ax.plot(Kg, m_hopf, color=c2, lw=1.8)
    ax.text(40, 1.38, "predator extinct\n$E_1=(K,0)$ stable", fontsize=8, color=ink)
    ax.text(160, 1.22, "stable coexistence ($E^*$ stable)", fontsize=7.5, color=c1, rotation=6)
    ax.text(170, 0.45, "limit cycle\n$E^*$ unstable", fontsize=8, color=c2)
    for lab, K, *_ in regimes:
        ax.plot(K, p["m"], "o", color=ink, ms=4)
        if lab not in "CDE":
            ax.annotate(lab, (K, p["m"]), xytext=(2, 4), textcoords="offset points", fontsize=8)
    ax.annotate("C, D, E", (90, p["m"]), xytext=(-8, -14), textcoords="offset points", fontsize=8)
    ax.set_xlim(0, 300); ax.set_ylim(0, ea); ax.set_xlabel(r"carrying capacity $K$")
    ax.set_ylabel(r"lynx mortality $m$ (yr$^{-1}$)")
    ax.set_title(r"Regimes for $b=30$, $ea=1.6$; Hopf curve in red", fontsize=9.5)
    for s_ in ("top", "right"): ax.spines[s_].set_visible(False)
    fig.tight_layout()
    save(fig, "regions")

    # Fig 3: trace and det vs K (analytic) with eigenvalue real part
    fig, ax = plt.subplots(figsize=(5.0, 3.0))
    Kg = np.linspace(hs + 0.5, 200, 500)
    tr = p["r"] * hs * (Kg - kh) / (Kg * (b + hs)); det = p["r"] * p["m"] * b * (Kg - hs) / (Kg * (b + hs))
    ax.plot(Kg, tr, color=c2, lw=2, label=r"$\mathrm{tr}\,J(E^*)$")
    ax.plot(Kg, det, color=c1, lw=2, label=r"$\det J(E^*)$")
    ax.plot(Kg, tr ** 2 / 4 - det, color=c3, lw=1, ls="--", label=r"$\mathrm{tr}^2/4-\det$")
    ax.axhline(0, color=ink, lw=0.6); ax.axvline(kh, color=ink, lw=0.6, ls=":")
    ax.annotate(r"$K_H=b+2H^*$", (kh, -0.15), xytext=(6, 0), textcoords="offset points", fontsize=8)
    ax.set_xlabel(r"carrying capacity $K$"); ax.legend(frameon=False, fontsize=8)
    for s_ in ("top", "right"): ax.spines[s_].set_visible(False)
    fig.tight_layout()
    save(fig, "trace_det")

    json.dump(dict(params=BASE, Hstar=hs, K_H=kh, l1=l1, l1_second_set=l1b, amp_slope=slope,
                   regimes=[{k: (str(v) if isinstance(v, complex) or (isinstance(v, list) and v and isinstance(v[0], complex)) else v)
                             for k, v in r_.items()} for r_ in rows]),
              open(OUT / "validation_targets.json", "w"), indent=2, default=str)
    print("\nwrote results/stability/ and report/graphs/joel_*")
