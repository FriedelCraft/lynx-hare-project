# Joel → team handoffs (equilibria, stability, Hopf)

## What is in this branch

| Path | What |
|---|---|
| `report/joel_stability_section.tex` | Section 2 for the report (`\input{joel_stability_section}`; needs amsthm environments, see `joel_main.tex`) |
| `report/joel_main.tex`, `joel_main.pdf` | Standalone build of the section |
| `report/graphs/joel_*.{eps,pdf}` | Three analytic figures (EPS + PDF companion, same convention as Yash's) |
| `report/references.bib` | Five new entries appended; nothing existing changed |
| `src/lynx_hare/stability.py` | Closed forms: H*, P*, K_H, σ, Jacobian, regime classifier |
| `tests/test_stability.py` | Checks the closed forms against the shared `model.rhs` |
| `scripts/joel_symbolic_derivation.py` | SymPy proof-checks of every formula (needs `pip install sympy`) |
| `scripts/joel_stability_analysis.py` | Eigenvalues, first Lyapunov coefficient, simulations, figures (uses shared `model.rhs`) |
| `results/stability/` | Validation targets JSON and figure PNG/EPS/PDF |

No existing source file or config was modified, so Yash's hash checks are unaffected.

Model and symbols exactly as in the work-distribution doc:
dH/dt = rH(1 − H/K) − aHP/(b+H),  dP/dt = eaHP/(b+H) − mP.
If Arnav's frozen notation or scaling differs, tell me and I'll re-map; every result is a one-line substitution.

## Key formulas (everyone)

| Quantity | Formula |
|---|---|
| Coexistence prey level | H* = mb/(ea − m) (independent of r and K) |
| Coexistence lynx level | P* = (r/a)(1 − H*/K)(b + H*) |
| Coexistence possible iff | ea > m and K > H*, i.e. m < eaK/(b+K) |
| Trace at E* | tr = rH*(K − K_H) / (K(b+H*)) |
| Det at E* | det = rmb(K − H*) / (K(b+H*)) > 0 whenever E* exists |
| Hopf threshold | K_H = b + 2H* = b(ea+m)/(ea−m) |
| Onset frequency / period | ω0 = √(rmb/K_H), T0 = 2π/ω0 |
| Stability margin | σ = K/K_H (σ<1 damped, σ>1 limit cycle) |

## To Rishi: parameter regimes and validation targets

Illustrative (not fitted) parameters: r=1.5, a=4, b=30, e=0.4, m=0.8 (H, P in thousand pelts; t in years).
H* = 30, K_H = 90, T0 = 9.94 yr. Solver used: RK45, rtol 1e-10, atol 1e-12, burn-in 3000 yr, start (20, 5).

| | K | Expect | Eigenvalues | Target |
|---|---|---|---|---|
| A | 25 | lynx extinct | J(E1): −1.5, −0.073 | → (25, 0) |
| B | 60 | stable focus | −0.188 ± 0.515i | → (30, 11.25) |
| C | 85 | slow damping | −0.022 ± 0.623i | → (30, 14.56), e-fold ≈ 45 yr |
| D | 90 | Hopf point | ±0.632i | very slow t^(−1/2) decay; residual H-amplitude ≈ 1.5 after 3000 yr is expected, not a cycle |
| E | 95 | small cycle | +0.020 ± 0.640i | H ∈ [15.8, 50.9], P ∈ [9.8, 20.8], T = 10.25 yr |
| F | 150 | large cycle | +0.150 ± 0.676i | H ∈ [1.1, 134.3], P ∈ [1.7, 41.2], T = 13.91 yr |

Checks for your bifurcation sweep:
- Branch should leave the equilibrium line exactly at K = 90 (supercritical: l1 ≈ −4.0e−4).
- Half-amplitude of H ≈ 7.8·√(K − 90) for K − 90 ≤ 8 (log–log slope 0.5).
- Period → 9.94 yr as K ↓ 90, and grows with K.
- Flow is counter-clockwise in (H, P); lynx peak lags hare peak by ≈ T/4 near onset (2.5 yr), ≈ 4.5 yr at K=150.
- Node→focus switch at K ≈ 42.5 (below that, no overshoot).
- Burn-in near K_H must be long (weak focus); use ≥ 20,000 yr for K within 1 of K_H.
Machine-readable copy: `results/stability/validation_targets.json`. Closed forms as code: `src/lynx_hare/stability.py` (`hopf_threshold`, `stability_margin`, `regime`, ...). Figures I produced are analytic only (nullclines, trace/det vs K, (K, m) regime map), so they don't overlap with your simulation plots.

## To Yash: constraints and identifiability for inverse fitting

Hard constraints (enforce via parameterisation, not penalties):
- all of r, K, a, b, e, m > 0 (softplus)
- ea > m, otherwise lynx cannot persist. Suggest ea = m·(1 + softplus(θ)).
- K > H* = mb/(ea − m) for coexistence. Suggest K = H*·(1 + softplus(φ)).

Soft constraints / sanity checks:
- On the attractor H < K, so K should be at least the largest training-window hare value (allowing for noise).
- Near onset, period ≈ 2π√(K_H/(rmb)); a ~10-year cycle means rmb/K_H ≈ 0.4. Use as a check on fitted values, not a constraint.

Identifiability (important):
- a and e enter H*, K_H and all stability conditions only through ea.
- With pelt indices (unknown scale c on lynx), (P, a, e) → (cP, a/c, ec) leaves the ODE unchanged. a and e cannot be separately identified. Fix e (or fit ea plus a lynx scale) and say so; Advay's baseline must use the same choice.
- r doesn't affect where the stability boundary is, only speed and damping, so r and the K/K_H question are partly decoupled.
- Please report σ = K/K_H for every seed/multistart. Over 1900–1915 a damped oscillation (σ slightly < 1) can fit nearly as well as a limit cycle, so the claim "the data show a limit cycle" needs σ > 1 robustly across fits.

## Notes on the current synthetic config (`configs/synthetic.json`) — for Yash

I have not edited the config (its hash is locked by the saved results). Two findings:

1. **The synthetic truth is in the limit-cycle regime.** With r=1, K=60, a=2, b=20, e=0.6, m=0.5:
   ea = 1.2, H* = 14.29, K_H = 48.57, so σ = K/K_H = 1.235. That is fine for a recovery test, but worth one
   sentence in the PINN section, and a σ < 1 truth would be a useful second test case (damped oscillations are
   the harder identification problem). `tests/test_stability.py` pins this so it is caught if the truth changes.
2. **The bounds include infeasible parameter sets.** With e fixed at 0.6, a ∈ [0.3, 4] and m ∈ [0.1, 1.2]
   allow ea ≤ m (e.g. a=0.5, m=0.5 gives ea=0.3), where lynx cannot persist at all, and also H* ≥ K = 60.
   Fits starting or wandering there sit in the extinction regime. Either reparameterise as suggested below or
   at least report `regime()` for every fitted run.

## 2-minute talk outline (Joel: theory)

1. (20 s) Three equilibria: extinction (always a saddle), hares only, coexistence. Coexistence needs ea > m and K > H*.
2. (30 s) Jacobian at E*: det > 0 always, so stability is just the sign of the trace, which is the sign of K − K_H with K_H = b + 2H*.
3. (30 s) Picture it: predator nullcline vertical at H*, prey nullcline a hump peaking at (K−b)/2. Right of hump: stable. Left: unstable. Show nullcline figure.
4. (25 s) Hopf at K_H: transversality holds, l1 < 0 so it's supercritical; Poincaré–Bendixson gives a cycle, Cheng (1981) gives uniqueness. Show (K, m) regime map.
5. (15 s) Paradox of enrichment: more K, same H*, more P*, bigger swings, deeper troughs. And the honest caveat: whether the real data are on a cycle depends on σ = K/K_H at the fitted values.

Likely questions: Why is LV a special case? (trace ≡ 0, sits on the Hopf boundary.) Why does r not matter for stability? (Only a positive prefactor.) Is the Hopf subcritical anywhere? (Not for RM; uniqueness theorem plus l1 < 0 numerically.)

## AI-acknowledgement log entry (draft, edit to match the official format)

- Tool: Claude (Anthropic), Opus 5.5
- Task assisted: symbolic derivation of equilibria/Jacobian/Hopf for the RM model; SymPy verification script; first-Lyapunov-coefficient calculation; illustrative parameter selection and RK45 checks; analytic figures; LaTeX draft of section 2; literature lookup for Hsu (1978) and Cheng (1981).
- Generated material: scripts/joel_symbolic_derivation.py, scripts/joel_stability_analysis.py, src/lynx_hare/stability.py, tests/test_stability.py, report/joel_stability_section.tex, report/joel_main.tex, bibliography entries, three figures, this note.
- Manually checked: (fill in — e.g. re-derived trace/det by hand, re-ran scripts, read the cited theorem statements)
