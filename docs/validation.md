# Verification record

Reference numerical work completed locally on 26 October 2026 before the first project
upload. This record concerns the synthetic work package only. Publication status is
tracked by Git rather than this numerical verification record.

- **Scientific tests:** 12 passed. These cover NumPy/Torch model agreement, a known
  equilibrium, boundary invariance, solver tolerance sensitivity and positivity,
  invalid inputs, the time/state chain rule, gradients to unknown parameters, positive
  bounds, training-only scaling, deterministic training and clean least-squares recovery.
- **Experiments:** 13 full PINN training runs completed. Nine default runs cover three
  data/noise cases and three seeds each. Four prespecified annual sensitivity runs
  vary physics weights or initial guesses. Actual settings and losses are retained.
- **Notebook:** the expanded complete-program notebook has 15 code cells, all executed
  successfully in order, with outputs saved. Its six implementation cells are generated
  from the canonical modules and carry matching source hashes.
- **Saved evidence:** `scripts/verify_outputs.py` passed. It independently rebuilt each
  exported ODE trajectory, recomputed held-out RMSE/MAE, checked source/config hashes,
  seed selection, training years, fixed parameters, forecast positivity and handoff schema.
  Its machine-readable record is `results/synthetic/verification.json`.
- **Figures:** all seven PNG figures were visually inspected; matching EPS files are
  present. Crowded year ticks in the sensitivity figure were corrected.
- **Report PDF:** the current `report/main.tex` project compiled successfully with the
  bundled Tectonic compiler. The exported seven-page A4 PDF was rendered with Poppler
  and every page was visually inspected. All seven report graph references name supplied
  EPS sources, with matching vector PDF companions for PDF-engine compatibility.
- **Presentation:** two slides include editable text, speaker notes and a native chart.
  Package, layout, font and embedded chart-workbook checks passed. Chart values use
  six-decimal rounding for spreadsheet portability. Slide previews were inspected.
  This does not assert that Microsoft PowerPoint itself was opened and tested.
- **Installation:** editable package installation with the local runtime succeeded.

To repeat the numerical tests, run `python -m pytest -q` in the installed environment.
To audit the delivered results, run `python scripts/verify_outputs.py`. If sources or
configuration change, retrain in a new results directory, rebuild the prose/notebook,
execute the notebook and audit again. These checks are evidence about this implementation,
not proof of biological validity, global optimizer convergence or historical accuracy.
