# Equation and units sheet

State order: **Hare H, Lynx P**. Elapsed time t = Year − 1900, in years. UH and UP are separately declared abundance-index units. Proposed historical units are thousands of pelts, pending the data contract; repository demonstration values are synthetic indices.

## Dimensional model

\[
\dot H=rH(1-H/K)-aHP/(b+H),\qquad
\dot P=eaHP/(b+H)-mP.
\]

| Symbol | Meaning | Unit |
|---|---|---|
| H, P | Hare and lynx states | UH, UP |
| r | Intrinsic prey net growth | year⁻¹ |
| K | Prey carrying capacity | UH |
| a | Maximum consumption per predator | UH / UP / year |
| b | Half-saturation prey abundance | UH |
| e | Effective predator conversion | UP / UH |
| m | Predator mortality | year⁻¹ |

All parameters are positive. H0 and P0 are nonnegative. e is not automatically an efficiency between zero and one in these index units. a/b, not a, is the low-density predation coefficient.

## Theory coordinates

\[
s=rt,\quad x=H/K,\quad y=aP/(rK),\qquad
\beta=b/K,\quad \alpha=ea/r,\quad \delta=m/r.
\]

\[
x_s=x(1-x)-xy/(\beta+x),\qquad
y_s=\alpha xy/(\beta+x)-\delta y.
\]

Back conversion: **Year = 1900 + s/r; H = Kx; P = (rK/a)y.**
Initial states: x0 = H0/K and y0 = aP0/(rK).
Derivative factors: dH/dt = rK xs; dP/dt = (r²K/a)ys.
Given r, K and a separately: b = βK, e = αr/a, m = δr.
During a K sweep, recompute x0 and y0 when holding H0 and P0 fixed.

## Existing numerical coordinates

u = H/sH, v = P/sP, ξ = 2t/T − 1, T = 15 years; sH and sP use training data only.

\[
u_t=ru(1-s_Hu/K)-\frac{a s_Puv}{b+s_Hu},\quad
v_t=\frac{ea s_Huv}{b+s_Hu}-mv.
\]

Bridge: x = (sH/K)u; y = (a sP/(rK))v; s = rT(ξ+1)/2.
Chain rule: d/dt = (2/T)d/dξ = r d/ds.
If a residual is expressed in ξ rather than years, its squared penalty scales by (T/2)²; preserve the original objective with the reciprocal loss-weight adjustment.

## Constant change of observation units

For H̃ = cH H and P̃ = cP P, with time unchanged:

\[
\widetilde K=c_HK,\quad \widetilde b=c_Hb,\quad
\widetilde a=(c_H/c_P)a,\quad \widetilde e=(c_P/c_H)e,
\quad \widetilde r=r,\quad \widetilde m=m.
\]

The dimensionless variables and groups are unchanged. This does not determine unknown conversion factors from pelts to animal populations.

## Synthetic example only

(r,K,a,b,e,m) = (1,60,2,20,0.6,0.5), (H0,P0) = (35,9).
Then (β,α,δ) = (1/3,1.2,0.5), (x0,y0) = (7/12,0.3), predator scale rK/a = 30.
These numbers reproduce Yash's example; they are not historical estimates.

Model attribution: [Rosenzweig and MacArthur (1963)](https://doi.org/10.1086/282272). Notation follows [Joel's section](https://github.com/FriedelCraft/lynx-hare-project/blob/7d17deee1cb685f016ff16cb6706e8db12ebe6b2/report/joel_stability_section.tex); synthetic values and numerical coordinates follow [Yash's method](https://github.com/FriedelCraft/lynx-hare-project/blob/7d17deee1cb685f016ff16cb6706e8db12ebe6b2/docs/method.md). Full derivation and source discussion are in the report.
