# Proposed model handoff from Arnav

Prepared 26 October 2026 against [repository commit 7d17deee](https://github.com/FriedelCraft/lynx-hare-project/tree/7d17deee1cb685f016ff16cb6706e8db12ebe6b2), including Joel's added analysis. This is a proposed contract for team review, not evidence that teammates have approved it.

**Update, 27 October 2026:** the [observation-model follow-up](observation_model_followup.md) supplements this dated handoff after the historical-data merges. It recommends direct pelt-state units under O1, adds the explicit observation equation, and distinguishes the current implementation from group agreement. The [units sheet](equations_and_units.md) contains that clarification. The historical-run status and remaining questions in the follow-up supersede the older status statements below; the dimensional interface and scaling are unchanged.

## Keep the current dimensional interface

- States in order H, P; parameters named r, K, a, b, e, m.
- dH/dt = rH(1−H/K) − aHP/(b+H).
- dP/dt = eaHP/(b+H) − mP.
- Time in years since the first training observation; for this protocol, Year − 1900.
- Historical measurement proposal: thousands of pelts as effective abundance indices, subject to Advay's source verification. Synthetic indices have no verified physical conversion.
- All parameters positive; initial states nonnegative. Bounds remain a separate inference decision. Do not impose e ≤ 1 merely by calling it an efficiency.

## Add the theoretical scaling without changing the PINN

Use s = rt, x = H/K, y = aP/(rK), beta = b/K, alpha = ea/r, delta = m/r, matching [Joel's section](https://github.com/FriedelCraft/lynx-hare-project/blob/7d17deee1cb685f016ff16cb6706e8db12ebe6b2/report/joel_stability_section.tex).

Then x_s = x(1−x) − xy/(beta+x), and y_s = alpha xy/(beta+x) − delta y.

Convert back with H = Kx, P = (rK/a)y and Year = 1900 + s/r. A K sweep changes beta and both state scales, so recompute x0 = H0/K and y0 = aP0/(rK) to keep the dimensional initial state fixed. Any change to r or a also changes the mapping.

Yash can retain u = H/sH, v = P/sP and xi = 2t/T − 1, where sH and sP are training maxima and T = 15 years. The bridge and residual-weight conversion are in the report. Do not call either normalized coordinate set by the other's name.

## Decisions still requiring the relevant owner

| Owner | Action before group integration |
|---|---|
| Arnav and all members | Review the units and K-based dimensionless form shared with Joel |
| Joel | Integrate the supplied analysis with the model section; distinguish positive parameter bounds from coexistence conditions |
| Rishi | Confirm the common solver and numerical checks, preserving the dimensional interface or explicitly mapping any dimensionless solver |
| Advay | Freeze the exact source CSV, units, observation convention, missing-data handling and evaluation rules |
| Advay and Yash | Agree fixed versus trainable parameters and bounds for historical fitting; synthetic K=60, b=20, e=0.6 are not measured historical constants |
| Rishi, Advay and Yash | Keep the same initial-state convention, forecast origin and tolerances for both fitting methods |

The existing synthetic experiments infer r, a, m while fixing K, b, e. Their solver uses RK45, rtol 1e−8, atol 1e−10 and max_step 0.1 years. Forecasts are integrated from the first training observation, then scored at 1916–1920; there is no restart from a held-out state. These are compatibility facts from the existing repository, not new choices made on another member's behalf.

## Notes prompted by the new analysis

Joel's formulas map directly: x* = beta·delta/(alpha−delta), and the threshold becomes beta·(alpha+delta)/(alpha−delta) = 1, with alpha > delta. These are restatements of his results, not a replacement Hopf derivation.

Use a stability ratio only after checking feasible coexistence. Below its threshold, a stable equilibrium may be a node or a focus; it need not display damped oscillations. Unknown pelt-to-population scales prevent interpreting a and e as uniquely recovered absolute biological rates. That does not alone prove they are unidentifiable as effective coefficients when the observation units are fixed and known. Do not automatically constrain all fits to coexistence without stating that ecological assumption; it excludes extinction regimes from the inverse problem.

Joel's illustrative parameter set and long-run tolerances differ from Yash's synthetic recovery experiment. Keep their labels and purposes distinct. The current paper draft is aligned with Joel's coordinates, while leaving Yash's code and dummy data unchanged.

## Validation and submission boundaries

This contribution supplies model reasoning, dimensional checks and exact arithmetic transformation checks. It does not supply new historical predictions, fitted parameters, RMSE/MAE or a Hopf proof. Those belong in the combined project after the relevant work is performed.

For prediction claims, retain the held-out years and use separate hare/lynx MAE and RMSE with comparison graphs in original evaluation units. Include the dataset and its provenance, the complete group notebook, the combined report source and PDF, all report EPS figures and any external diagram assets in the final ZIP. This section uses no external images, graphs or datasets.
