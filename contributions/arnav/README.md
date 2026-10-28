# Arnav's final model contribution

Updated 28 October 2026 after pulling the latest main, revision [28dbe1e](https://github.com/FriedelCraft/lynx-hare-project/tree/28dbe1e2a611719f3d65e5922db528ae423724f2). This is Arnav's model section for the completed historical iteration. It incorporates the observation follow-up into the report and notebook, using `configs/historical.json` as the reference. It changes no fitting settings or saved results.

## Phase 1: Reconcile the observation convention

**Step and decision.** Read Advay's provenance and observation notes alongside the current configuration. Define H and P in thousands of pelts, model observations as state plus discrepancy, and state O1 explicitly. Unknown constant pelt-to-animal factors are absorbed into effective coefficients; no observation-scale factor is fitted. Annual totals are approximated as point observations.

**Tradeoff.** This preserves the current two-state model and makes both fitting methods comparable. Estimated trapping factors or seasonal observation integrals would add assumptions and unknowns. We document the limitations rather than change a completed experiment. Keep the frozen Stan compilation; the alternative source disagreement remains a limitation.

## Phase 2: Align equations, units and implementation

**Step and decision.** Retain the exact shared equations and Joel's s=rt, x=H/K, y=aP/(rK), beta=b/K, alpha=ea/r, delta=m/r. Check the PINN's fixed training normalization and chain rule against the source. Explain that K, b, a and e are effective pelt-unit coefficients; r, m and the dimensionless groups are scale invariant, with biological interpretation conditional on O1 and model adequacy.

**Tradeoff.** Theory scales depend on fitted parameters. Keeping training maxima for PINN normalization avoids making training targets depend on unknowns; the report supplies the conversion. The observation-scale argument does not by itself prove either identifiability or non-identifiability of all six coefficients.

**Current settings.** All six coefficients are fitted with the recorded positive bounds, without e<=1 or a coexistence restriction. Historical comparison uses `model.solve`, RK45, rtol=1e-8, atol=1e-10, max_step=0.1. Main ODE forecasts start at (30,4) in 1900; the network uses a soft initial penalty. The two sensitivity variants remain separate. These are descriptions of the completed iteration, not new parameter choices.

## Phase 3: Prepare material for integration

**Step and decision.** Update the final LaTeX section, bibliography, standalone PDF, notebook explanation and two editable presentation slides. Keep the mathematical derivation explicit and supply oral-exam questions. The slide notes give the spoken explanation and sources.

**Tradeoff.** The report keeps the full derivation; the two slides emphasize the observation convention and scaling within an approximately two-minute slot. Yash can shorten repeated methods material during integration while retaining the reasoning in the notebook.

## Phase 4: Verify and record responsibility

**Step.** Rerun the six notebook code cells in a fresh namespace, check bibliography keys and equation labels, compile the report and inspect rendered pages/slides. The notebook checks 558 exact equalities at finite rational inputs. This is algebra verification, not a general proof or empirical validation. No historical fitting or scoring is rerun.

**Personal review.** The AI/manual-check log records assistant work separately from Arnav's own understanding and rehearsal. Only Arnav can complete the personal-review entries. The presence of generated material is not evidence that this review happened.

## Files to give Yash

| File | Purpose |
|---|---|
| `sections/arnav_model.tex` | Final introduction, observation model, derivation, units, scaling and compatibility |
| `references.bib` | All literature and repository sources, with `arnav_` keys |
| `main.tex`, `main.pdf`, `main.bbl` | Standalone compiled model section and bibliography |
| `arnav_model_explained.ipynb` | Explanations and executed standard-library algebra checks |
| `arnav_model_slides.pptx` | Two editable slides with speaking notes and source links |
| `presentation_notes.md` | Speaking script, timing guidance and oral-exam preparation |
| `equations_and_units.md` | Compact notation and observation reference |
| `team_handoff.md` | Exact integration instructions and boundaries |
| `source_notes.md` | Source scope and provenance |
| `verification_summary.json` | Executed notebook checks and notebook hash |
| `ai_acknowledgement.md` | Assistance record and personal checks still to complete |
| `observation_model_followup.md` | Dated 27 October decision history, superseded where the final section records current settings |

This contribution uses equations and a native table, so it has no EPS figure dependencies. It supplies no new dataset or empirical figure. The complete group submission remains Yash's integration task.

For a standalone build, compile `main.tex` with Tectonic or run `pdflatex main.tex`, `bibtex main`, and `pdflatex main.tex` twice. To rerun the notebook, use a Python 3 kernel and Restart Kernel and Run All; no third-party package is needed.

## Sources

The report cites [Rosenzweig and MacArthur (1963)](https://doi.org/10.1086/282272), [Holling (1959)](https://doi.org/10.4039/Ent91385-7), [Carpenter's case study](https://mc-stan.org/learn-stan/case-studies/lotka-volterra-predator-prey.html), and the pinned data, theory and implementation files listed in `source_notes.md`. The source-selection decision and computational settings come from those project records. The explicit derivations and finite algebra checks are this contribution's explained mathematical work; they do not claim a new predator-prey model.
