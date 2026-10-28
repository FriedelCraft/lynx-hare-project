# Integration completion, 28 October 2026

This supersedes the dated 27 October audit for implementation status. Arnav's final
model update and the reviewed Advay #4/#6 and Rishi #5 contributions are integrated.
The acknowledgement merge preserves both contributors' entries. Human review,
understanding, rehearsal and final email submission remain the members' responsibilities.

## Completed technical deliverables

- Arnav: finalized model/observation/scaling source, units, notebook and two slides.
- Joel: theory source, symbolic checks and analytic results. The combined report uses
  `joel_group_section.tex`, an integration copy with explicit equilibrium and observation-
  scale qualifications. The original dated standalone contribution is preserved.
- Rishi: corrected direction field, simulation config, declared pandas dependency,
  historical stability placement, notebook, report and talk notes.
- Advay: independent historical multistart baseline, frozen evaluation, data/limitations
  section, notebook and talk notes. His LaTeX report has now been compiled; the oversized
  metric table and unbreakable file paths were repaired without changing results.
- Yash: completed historical PINN evidence plus two editable historical slides,
  optimization-gap discussion, and group assembly/packaging.
- One 98-cell group notebook, `notebooks/group_project.ipynb`, credits all authors and
  isolates their Python namespaces to prevent variable/function collisions. It includes
  the original executable implementations, symbolic/scaling verification, illustrative
  simulations, live training-only LS demonstrations, and frozen-result reconstruction.
- Combined report: `report/group_main.tex` and `.pdf`, with all five contributions,
  controlled synthetic recovery, bibliography, EPS graphs and matching vector PDFs.
- Group presentation: `presentation/group_presentation.pptx`, ten slides with notes,
  two per member. Yash's separate current segment is `yash_historical_slides.pptx`.
  Existing synthetic slides remain labelled and are not the current talk segment.
- Packaging now follows active TeX input/figure dependencies rather than asserting
  an old fixed graph count. It includes historical data and raw provenance, source,
  all credited notebooks and required EPS/PDF graph pairs. ZIP stays outside Git.

## Reproduction modes and chronology

The group notebook executes the illustrative simulation studies. Repeating the full
historical 3000-60000-year simulations for every saved fit is opt-in through
`FULL_LONG_RUN_REPLAY=True`; by default their frozen figures/tables are displayed
and historical PINN sigma values are independently recomputed. The full regeneration
program remains available. PINN training is not silently restarted in the notebook.
Two LS training demonstrations do not change frozen parameters or selected forecasts.

All original experimental results and selection rules are preserved. Advay's independent
evaluation followed Yash's scored iteration; it is reproduction, not a new blinded test.
Integration does not use the known test errors to change parameters or choose a variant.

The PINN observation cost on its reintegrated trajectory is 1.859/3.396/1.866 times
the LS minima across main/log/fitted-IC variants. This differs from its weighted neural
objective. The final discussion reports this optimization gap and the mixed held-out
comparison without claiming PINN superiority or identified absolute biological rates.

## Validation completed

The full suite passes 53 tests. The group notebook executes all 39 code cells.
All 37 combined-report pages and all 12 slides across the two current decks have
been rendered and visually inspected by the assistant. The decks also pass structural,
font, import and chart/workbook validation. Archive/extracted-copy verification is
recorded in `results/integration/verification.json`; the final ZIP hash is in the
local `submission/submission_verification_group.json` outside the repository.

## Commands

```text
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps
python -m pytest -q
python scripts/execute_notebook.py --notebook notebooks/group_project.ipynb
python scripts/verify_outputs.py
python scripts/verify_historical_outputs.py
python scripts/build_submission.py --scope group --extract-check
```

Compile `report/group_main.tex` from its report directory with a LaTeX engine that
supports the included packages (for example latexmk -pdf or Tectonic). PDF engines
use vector companions; EPS sources remain in the package as required.

The professor asked for the ZIP by email at least one week before the presentation.
No email has been sent and no presentation date has been assumed. Every member should
review their section and record only manual checks actually performed. No automatic
technical check certifies a person's understanding or course-rule compliance.
