# Arnav's model formulation and scaling

This package prepares Arnav's assigned scientific foundation for the MAC F314 lynx-hare project. It explains and checks the common model so the team's theory, simulations and fitting can use consistent equations. The original report and notebook were aligned with [repository commit 7d17deee](https://github.com/FriedelCraft/lynx-hare-project/tree/7d17deee1cb685f016ff16cb6706e8db12ebe6b2), checked on 26 October 2026, including Joel's stability analysis. Yash's results at that revision used dummy data.

**27 October update:** [bcc0a2b](https://github.com/FriedelCraft/lynx-hare-project/tree/bcc0a2b1ba4a277712ccd43ee3ff81e1397e7f03) includes Advay's historical data, Rishi's simulations and Yash's historical fits. Start with the [observation-model follow-up](observation_model_followup.md) for the response to Advay's questions, decisions, alternatives and citations. The [units sheet](equations_and_units.md) now explicitly connects pelt observations to the model states. This supplement does not change the report's equations or its synthetic algebra examples, and does not record group approval. The phases below document the original foundation work; historical-status statements there refer to the earlier revision.

Read the phases below, then the report in `main.tex` and the notebook. The work is prepared for your review and explanation; no teammate approval or personal understanding is assumed. The proposed observation convention and dimensionless notation still need the team's agreement before being called frozen.

## Phase 1 Establish the question and what is observed

**Step 1.** State the question: can a mechanistic predator-prey model reproduce recurring fluctuations, explain their stability, and support useful forecasts beyond calibration?

**Step 2.** Separate a model state from a measurement. The historical source contains annual pelt totals. We propose treating these as noisy abundance indices and using thousands of pelts, matching the Stan transcription. Advay must confirm the exact CSV, source version and units. Existing repository values remain explicitly synthetic.

**Step 3.** Keep the existing split: 1900–1915 for fitting and 1916–1920 for final evaluation. Set elapsed time to Year minus 1900. Do not choose a model or scales using the held-out years.

**Decision and reason.** Use two effective index states, H for hare and P for lynx, with time in years. This fits the existing code and avoids pretending that a trade record is a population census.

**Alternative and tradeoff.** A latent population model with unknown capture fractions would represent observations more explicitly, but adds unknown quantities and possible confounding. A seasonal observation integral would also be more faithful to annual totals. Both are outside this contribution. The effective index model is simpler, at the cost of weaker biological interpretation.

**Result.** The report introduction and source notes define the question, observation caveat and split. No dataset has been fitted, cleaned or replaced.

## Phase 2 Derive the dimensional model

**Step 1.** Explain Lotka–Volterra term by term: exponential prey growth, encounter-based consumption, predator gain and mortality.

**Step 2.** Derive a conserved quantity to justify neutral cycles. Do not argue that imaginary eigenvalues alone prove a nonlinear centre. The conserved level curves supply the missing reasoning: a perturbation changes the orbit rather than producing a return to one attracting cycle.

**Step 3.** Replace unlimited prey growth with logistic growth. Start from a per-capita rate that falls linearly to zero at carrying capacity K.

**Step 4.** Motivate the type II response through a search-and-handling time budget. The consumption rate is aH/(b+H); a is its maximum and b is the hare abundance at half maximum.

**Step 5.** Combine prey growth, consumption, predator conversion and mortality. Check units in each equation and explain every parameter.

**Decision and reason.** Keep exactly the Rosenzweig–MacArthur equations and names already used by Yash. Here a is a maximum consumption rate, not the low-density encounter coefficient. The latter is a/b.

**Alternative and tradeoff.** Lotka–Volterra is easier but lacks resource limitation and saturation. A type III response, explicit vegetation or seasonal forcing could represent other mechanisms, but would change the agreed model and expand the analysis. The chosen model adds two interpretable mechanisms while preserving a tractable two-state system.

**Result.** The report derives the equations, lists assumptions and verifies nonnegative states and the prey bound. Full Rosenzweig–MacArthur equilibrium and Hopf analysis stays with Joel.

## Phase 3 Derive the dimensionless form

**Step 1.** Choose time scale 1/r, prey scale K and predator scale rK/a. Define s = rt, x = H/K and y = aP/(rK), matching Joel's existing notation.

**Step 2.** Apply the chain rule explicitly: dH/dt = rK dx/ds and dP/dt = (r²K/a) dy/ds.

**Step 3.** Substitute into both dimensional equations and divide through. The result is

\[
\frac{dx}{ds}=x(1-x)-\frac{xy}{\beta+x},\qquad
\frac{dy}{ds}=\alpha\frac{xy}{\beta+x}-\delta y,
\]

where beta = b/K, alpha = ea/r and delta = m/r.

**Step 4.** State how to transform initial conditions and recover years and index units. Explain that three groups cannot reconstruct all six physical parameters without additional scale information.

**Step 5.** Use the existing synthetic parameter values as one arithmetic example, not as historical estimates. The notebook checks several additional values so the calculation does not rely on r accidentally being one.

**Decision and reason.** Use K as the prey scale to match [Joel's dimensionless analysis](https://github.com/FriedelCraft/lynx-hare-project/blob/7d17deee1cb685f016ff16cb6706e8db12ebe6b2/report/joel_stability_section.tex). The initial draft used b; the repository update supplied a concrete reason to change the main convention before integration. The mathematical model itself is unchanged.

**Alternative and tradeoff.** Scaling H by b and P by rb/a keeps the state scales fixed when only K changes. The selected K-based form makes carrying capacity one and avoids competing notation in the report, but a K sweep must recompute scaled initial conditions to hold physical initial states fixed. Both forms describe identical trajectories.

**Result.** A complete chain-rule derivation, reverse transformations, units, example and comparison with the b-based alternative.

## Phase 4 Connect the theory to Yash's implementation

**Step 1.** Identify the existing numerical coordinates: u = H/sH, v = P/sP, and xi = 2t/T − 1, with T = 15 years. The state scales are training-only maxima.

**Step 2.** Derive the normalized right-hand sides in elapsed years and map them to x, y and s.

**Step 3.** Show the chain-rule factor 2/T when differentiation is with respect to xi. A residual in xi is T/2 times the corresponding residual in years; squaring it changes the penalty scale. A matching loss weight would multiply by (2/T)², under the same averaging convention.

**Step 4.** Derive how all parameters change under constant measurement rescaling. This explains why e is not automatically a dimensionless number below one and why different species units affect a and e.

**Decision and reason.** Preserve the dimensional solver and fixed PINN normalization. Since r and a are trainable, using rt and aP/(rK) as fixed training coordinates would make preprocessing depend on parameters being inferred.

**Alternative and tradeoff.** Training directly in parameter-dependent dimensionless variables is possible, but would require a carefully redefined inverse problem and loss. It adds work without being necessary for your objective.

**Result.** Compatibility equations and a proposed team handoff. No shared source code, recorded results or configuration has been changed.

## Phase 5 Check the mathematics and state the evidence limits

**Step 1.** Audit dimensions and zero-species limits on paper.

**Step 2.** Run the notebook's short exact-arithmetic checks: transformed derivatives, initial-state round trips, measurement-unit changes, numerical normalization, time-derivative factors, the Lotka–Volterra conserved derivative and the low-density approximation.

**Step 3.** Compare the direct and transformed right-hand sides at multiple parameter/state combinations. Fraction arithmetic makes an equality exact at each tested input, rather than obscuring it with floating-point rounding. Finite checks support the written derivation; they are not a general symbolic proof.

**Step 4.** Keep algebra verification distinct from ecological validation. Historical forecasts still require untouched test data, separate hare/lynx MAE and RMSE, comparison graphs and a fair baseline. Synthetic recovery alone cannot validate the biological model.

**Decision and reason.** Include only lightweight checking code, with an explanation before each cell. It does not train a PINN, integrate an ODE or duplicate Rishi's solver.

**Alternative and tradeoff.** A symbolic-algebra library could automate identities, but adds a dependency and hides some steps. The report gives the general derivation, and a standard-library notebook provides transparent checks.

**Result.** A rerunnable notebook and recorded verification summary. These checks support mathematical correctness; they do not guarantee bonus marks, parameter identifiability or predictive success.

## Phase 6 Prepare the contribution and team handoff

**Step 1.** Supply an integrable LaTeX section and bibliography, with unique equation labels and citation keys.

**Step 2.** Supply an equation-and-units sheet, notebook explanation, a two-minute presentation script and questions with answers.

**Step 3.** Record AI assistance accurately. The log distinguishes checks performed by the assistant from the review and explanation you still need to do yourself.

**Step 4.** Give the team the proposed model contract. It identifies each member's next integration responsibility without claiming their agreement.

**Decision and reason.** Deliver a separate local package rather than changing shared results. It can be reviewed and then merged into the group report and notebook.

**Alternative and tradeoff.** Editing the shared repository immediately would reduce copying later but could silently replace scientific decisions that have not been agreed. A separate contribution makes the review boundary explicit.

## Files and integration

| File | Use |
|---|---|
| `main.pdf` | Six-page compiled report, visually reviewed on every page |
| `main.tex` | Standalone report entry point; open this folder in the LaTeX editor |
| `sections/arnav_model.tex` | Introduction, model, assumptions, scaling and compatibility section to merge |
| `references.bib` | Literature and data-source entries; `arnav_` prefixes reduce collisions |
| `equations_and_units.md` | Compact reference sheet |
| `arnav_model_explained.ipynb` | Explanatory notebook with executed algebra checks; Python standard library only |
| `team_handoff.md` | Proposed decisions, exact mappings and owner responsibilities |
| `presentation_notes.md` | Two-minute script and short oral-exam preparation |
| `source_notes.md` | What was verified and what each source supports |
| `ai_acknowledgement.md` | Honest assistance and review record |
| `verification_summary.json` | Machine-generated outcomes of the notebook checks |

To integrate the report, copy the section and merge its bibliography entries into the group's bibliography. Add `\input{sections/arnav_model}` at the appropriate location. The host document needs `amsmath`, `amssymb`, `booktabs`, `array`, `tabularx` and `hyperref`. Do not copy the standalone document preamble into another document. Remove or shorten the compatibility and validation sections if the final report has a separate methods section; keep the reasoning in the notebook.

The contribution has no graphs or external diagrams, so it has no EPS or diagram dependencies. It uses no observation dataset; source links identify the proposed historical series for Advay. The group's final ZIP must include the actual dataset, EPS figures, combined notebook, LaTeX and PDF after integration.

## What you should be able to explain before submission

1. Why neutral Lotka–Volterra cycles do not return to a unique attracting orbit.
2. Why aH/(b+H) saturates and what b means.
3. The units of a and e when the states are separately scaled indices.
4. Every factor of r, K and a in the two derivative transformations.
5. Why dimensionless groups do not by themselves identify six physical parameters.
6. Why the theory scales and PINN training scales can differ consistently.
7. What has been checked here, and what requires real held-out observations later.

Personal review and team agreement are outstanding integration actions. This folder contains Arnav's contribution for repository integration; it is not the complete group submission.

## Verification completed

All six notebook code cells executed in order with Python 3.12.14. The 558 exact equality assertions passed; the discrepancy at the tested rational inputs was zero. The checks cover multiple parameter and state values, not observations or training runs. The six-page report compiled with resolved citations and no overfull text or equations; all six rendered pages were inspected. Bibliography wrapping produces non-fatal spacing warnings only.

The notebook can run without the source repository. To rebuild the report in a normal LaTeX installation, run `pdflatex main.tex`, `bibtex main`, then `pdflatex main.tex` twice, or compile `main.tex` with Tectonic. The included `main.bbl` is the generated bibliography; `references.bib` remains the editable source. The archive contains this contribution only, not the complete group submission.

## Sources used

The phase guide summarizes the derivations in the report, which cites [Rosenzweig and MacArthur (1963)](https://doi.org/10.1086/282272), [Holling (1959)](https://doi.org/10.4039/Ent91385-7), [Carpenter's Stan case study](https://mc-stan.org/learn-stan/case-studies/lotka-volterra-predator-prey.html), and the pinned team contributions linked above. Exact-arithmetic code uses Python's [Fraction documentation](https://docs.python.org/3/library/fractions.html). Full attribution, including the supplied assignment and professor instructions, is in `source_notes.md`; no unlisted textbook is claimed as a source.
