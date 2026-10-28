# Arnav's final integration handoff

Prepared 28 October 2026 against [28dbe1e](https://github.com/FriedelCraft/lynx-hare-project/tree/28dbe1e2a611719f3d65e5922db528ae423724f2). The user's latest task identifies `configs/historical.json` as the reference for the completed iteration. The final model section now documents that reference; this note does not assert another member's personal approval or manual review.

## Report

Use `sections/arnav_model.tex` before Joel's stability section. It contains the observation-model follow-up, not just a link to it. From a combined entry point inside `report/`, the section can be included without copying:

```latex
\input{../contributions/arnav/sections/arnav_model}
```

The host preamble needs `amsmath`, `amssymb`, `booktabs`, `array`, `tabularx` and `hyperref`. Merge `contributions/arnav/references.bib` into the group bibliography, or include both bibliography databases after checking that no key already appears twice. All of this contribution's keys and equation labels have the `arnav_` or `eq:arnav_` prefix. Keep one bibliography in the combined document; do not paste this contribution's document class or title page into it.

The standalone `main.pdf` is a reading copy. The final group report should use the editable LaTeX section. Its compatibility and responsibility paragraphs can be shortened if Yash's methods section repeats them; retain the observation equations and interpretation limits.

## Notebook and presentation

- Append the cells of `arnav_model_explained.ipynb` as a model-foundation part of the combined notebook. Use a fresh namespace or prefix its helper names during integration: it defines `rhs`, `groups`, `checks`, `F` and other local helpers. Rerun the combined notebook after combining cells to catch name collisions.
- The notebook needs only the Python standard library and reads no observation files. Its worked values and normalization examples are synthetic algebra inputs, explicitly labelled.
- Import the two slides from `arnav_model_slides.pptx` into the group deck. Both slides and their equations are editable text. Speaking notes contain citations; `presentation_notes.md` supplies the script and questions.
- No EPS figures or external artwork are needed for this section. Do not add decorative plots to meet a graph-count requirement.

## Fixed interface for this iteration

| Item | Convention |
|---|---|
| States and time | H then P, in thousands of hare/lynx pelts; t=Year-1900, in years |
| Observation | Y_H=H(t)+error, Y_P=P(t)+error; O1 is constant proportionality to latent abundance; no fitted observation scales |
| Dimensional equations | Hdot=rH(1-H/K)-aHP/(b+H); Pdot=eaHP/(b+H)-mP |
| Joel's coordinates | s=rt, x=H/K, y=aP/(rK); beta=b/K, alpha=ea/r, delta=m/r |
| Back conversion | Year=1900+s/r; H=Kx; P=(rK/a)y |
| PINN coordinates | u=H/sH, v=P/sP, xi=2t/T-1; T=15, historical training maxima (77.4,59.4) |
| Fitted coefficients | All r,K,a,b,e,m, with the bounds in `configs/historical.json` |
| Historical solver | model.solve, RK45, rtol=1e-8, atol=1e-10, max_step=0.1 years |
| Initial state | Main ODE: (30,4) at 1900; PINN uses a soft penalty and reports the gap; sensitivity fits initial states within 0.5 to 1.5 times observed |
| Forecast and evaluation | Integrate from 1900 without a test restart; separate hare/lynx MAE and RMSE in thousands of pelts for 1916-1920 |

Sources: [historical config](https://github.com/FriedelCraft/lynx-hare-project/blob/28dbe1e2a611719f3d65e5922db528ae423724f2/configs/historical.json), [Yash's handoff](https://github.com/FriedelCraft/lynx-hare-project/blob/28dbe1e2a611719f3d65e5922db528ae423724f2/docs/yash_historical_handoff.md), [Advay's convention](https://github.com/FriedelCraft/lynx-hare-project/blob/28dbe1e2a611719f3d65e5922db528ae423724f2/docs/advay_observation_convention.md), and [Joel's notation](https://github.com/FriedelCraft/lynx-hare-project/blob/28dbe1e2a611719f3d65e5922db528ae423724f2/report/joel_stability_section.tex).

K sweeps must recompute x0 and y0 if the dimensional initial state stays fixed. a and e are effective coefficients; fixed observation units remove the free scale ambiguity without proving practical identifiability. Use sigma only with the applicable coexistence conditions, and describe its classification as a property of the fitted model. The completed iteration fits all six coefficients without an e<=1 or coexistence constraint. Bounds are exploratory numerical choices.

## Remaining responsibility

Arnav must personally review and explain the equations and rehearse the talk, then complete the manual-check log honestly. Yash owns combined-package assembly and validation. The other owners retain their analysis, plotting and evaluation tasks. This update changes no shared model code, fitting configuration, data or saved results; later substantive revisions must preserve the scored iteration and be labelled accordingly.
