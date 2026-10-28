# Group submission package

This package contains the combined MAC F314 lynx-hare project by Arnav, Joel, Rishi,
Yash and Advay. It follows Prof. Amit's requested file categories. The ZIP is a local
artifact, has not been emailed, and is not pushed to GitHub.

| Required item | Entry point |
|---|---|
| Complete Jupyter analysis with Markdown | `notebooks/group_project.ipynb` |
| Detailed report PDF | `report/group_main.pdf` |
| LaTeX and bibliography | `report/group_main.tex`, its section/table inputs, `group_references.bib` |
| All report graphs in EPS | Active graph dependencies under `report/graphs/`, with vector PDF companions |
| All external diagram files | No external diagram assets; analytic diagrams are included as EPS graphs |
| Complete datasets | `data/historical/` including raw sources, split and provenance; `data/synthetic/` for controlled validation |

The source modules, independent baseline, experimental logs, frozen forecasts, scores,
tests, credited individual notebooks and per-person AI acknowledgements are included.
`SUBMISSION_MANIFEST.json` records every packaged file's hash. Python environments,
Git metadata, caches, local binary checkpoints and private review images are excluded.

Extract the entire archive and preserve the directory structure. With Python 3.12:

```text
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps
python -m pytest -q
python scripts/execute_notebook.py --notebook notebooks/group_project.ipynb
```

The combined notebook has 39 executed code cells. It includes full model/PINN
implementations, exact scaling and symbolic checks, live numerical demonstrations,
training-only LS demonstrations and independent frozen-result checks. PINN training
is not silently repeated. Full historical 3000-60000-year numerical regeneration is
opt-in through `FULL_LONG_RUN_REPLAY=True`; default execution audits and displays its
frozen evidence and independently recomputes sigma. Individual full regeneration
programs remain in `scripts/`.

Compile `report/group_main.tex` from the report directory using latexmk -pdf or
Tectonic. Keep EPS and vector PDF companions together. No additional dataset download
or separate EPS converter is needed for PDF compilation.

The historical split is 1900-1915 training and 1916-1920 evaluation. Existing scored
results are frozen; any later experimental change must preserve that evidence and
be labelled as a later revision. Advay's independent evaluation followed Yash's
published scored iteration, so it is reproduction rather than a new blinded test.
The synthetic study is separate controlled validation, not historical observations.

The presentation contains ten slides with speaker notes, about two minutes per member.
Every member should verify their interpretation, rehearse, and record only personal
checks actually performed. The professor requested email submission at least one week
before the scheduled presentation; no presentation date or recipient is assumed here.
