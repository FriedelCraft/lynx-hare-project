# Equation and units sheet

State order: **Hare H, Lynx P**. Elapsed time t = Year − 1900, in years. For the historical convention reviewed on 27 October 2026, UH means thousands of hare pelts and UP means thousands of lynx pelts. These are abundance-index units, not animal counts. This matches the current historical fitting configuration; group approval remains separate. Synthetic demonstrations retain their own declared index units. See the [observation follow-up](observation_model_followup.md) for decisions, alternatives and sources.

## Observation model

For observation year Year_i, let t_i = Year_i − 1900:

\[
Y_{H,i}=H(t_i)+\varepsilon_{H,i},\qquad
Y_{P,i}=P(t_i)+\varepsilon_{P,i}.
\]

Here Y denotes the recorded annual pelt count in thousands, H and P the model's noiseless pelt indices, and ε the observation discrepancy in the corresponding pelt units. Under the working proportional-index assumption O1,

\[
H(t)=c_H N_H(t),\qquad P(t)=c_P N_P(t),\qquad c_H,c_P>0.
\]

N denotes latent animal abundance. The factors cH and cP are constant and unknown, and are absorbed into the effective coefficients; they are not fitted or assumed numerically equal to one. Annual totals are approximated as point samples. No seasonal observation integral is introduced. This follows [Advay's proposed convention](https://github.com/FriedelCraft/lynx-hare-project/blob/bcc0a2b1ba4a277712ccd43ee3ff81e1397e7f03/docs/advay_observation_convention.md) and matches [Yash's historical configuration](https://github.com/FriedelCraft/lynx-hare-project/blob/bcc0a2b1ba4a277712ccd43ee3ff81e1397e7f03/configs/historical.json).

H and P are in thousands of pelts; their time derivatives are in thousands of pelts per year. The annual collection interval does not add a second time denominator to the model states. The additive discrepancy notation alone does not establish a Gaussian error distribution or independent observations. Training-maximum normalization supplies comparison weights, not measured noise standard deviations.

## Dimensional model

\[
\dot H=rH(1-H/K)-aHP/(b+H),\qquad
\dot P=eaHP/(b+H)-mP.
\]

| Symbol | Meaning | Unit |
|---|---|---|
| H, P | Hare and lynx states | UH, UP |
| r | Intrinsic prey net growth | year⁻¹ |
| K | Effective prey carrying-capacity index | UH |
| a | Effective maximum consumption coefficient | UH / UP / year |
| b | Half-saturation prey index | UH |
| e | Effective predator conversion | UP / UH |
| m | Predator mortality | year⁻¹ |

All parameters are positive. H0 and P0 are nonnegative. e is not automatically an efficiency between zero and one in these index units. a/b, not a, is the low-density predation coefficient.

r and m retain their growth/mortality-rate interpretation only conditional on O1 and the adequacy of the dynamical model. K, b, a and e are effective coefficients in pelt units. Invariance to observation scaling does not establish that any fitted parameter is accurate or well determined.

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

The dimensionless variables and groups are unchanged. This does not determine unknown conversion factors from pelts to animal populations. The same invariance holds for Joel's σ = K/K_H where the coexistence threshold is applicable. These are model-based stability quantities, not independent confirmation of ecological mechanisms. Fixing the observation convention removes the free predator-scale ambiguity; it does not by itself establish identifiability of all six effective coefficients from the available annual observations.

## Synthetic example only

(r,K,a,b,e,m) = (1,60,2,20,0.6,0.5), (H0,P0) = (35,9).
Then (β,α,δ) = (1/3,1.2,0.5), (x0,y0) = (7/12,0.3), predator scale rK/a = 30.
These numbers reproduce Yash's example; they are not historical estimates.

Model attribution: [Rosenzweig and MacArthur (1963)](https://doi.org/10.1086/282272). Notation follows [Joel's section](https://github.com/FriedelCraft/lynx-hare-project/blob/7d17deee1cb685f016ff16cb6706e8db12ebe6b2/report/joel_stability_section.tex); synthetic values and numerical coordinates follow [Yash's method](https://github.com/FriedelCraft/lynx-hare-project/blob/7d17deee1cb685f016ff16cb6706e8db12ebe6b2/docs/method.md). Full derivation and source discussion are in the report.
