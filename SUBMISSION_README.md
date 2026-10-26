# Yash PINN submission package

This ZIP follows the file categories requested by Prof. Amit. It contains **Yash's
PINN component using synthetic data**. It is a prepared component for group integration,
not a claim that the five-person project or historical-data analysis is complete.

## Required files

| Professor's requirement | Included location |
|---|---|
| Complete Jupyter program with Markdown | `notebooks/yash_pinn.ipynb` |
| Detailed report in PDF | `report/main.pdf` |
| LaTeX report and supporting sources | `report/main.tex`, `yash_pinn_section.tex`, `diagnostics_appendix.tex`, `tables/` and `references.bib` |
| Every report graph in EPS | Seven files in `report/graphs/*.eps` |
| Diagram files used in the report | No separate diagrams are used; `diagrams/README.md` records this |
| Complete datasets | All CSV files and `provenance.json` in `data/synthetic/`, with generating parameters in `configs/synthetic.json` |

Source code, configuration, tests, numerical results, presentation slides and the AI
assistance log are included as supporting material. `SUBMISSION_MANIFEST.json` lists
the archive files and their SHA-256 hashes. Git metadata, environments, caches, private
review images and binary model checkpoints are excluded.

## Notebook and program

Extract the entire ZIP before opening the notebook. Keep the folder structure intact.
The notebook includes the full model, solver, data generation, PINN, training loop,
baseline, plotting and evaluation code in executable cells. Its implementation cells
are generated from the included modular source, with matching source hashes recorded.
All 15 code cells have been executed successfully and their outputs are saved.

Install Python 3.12 and the dependencies as described in `README.md`. The notebook can
run from the repository root or the `notebooks/` directory. It uses included reference
results by default. Move `results/synthetic/` aside before rerunning fresh training.
No external dataset download is required. The complete datasets and generation settings
are included. Optional model checkpoints can be regenerated and are not required to
read or rerun the notebook.

## Report compilation and EPS graphs

Open `report/main.tex` as the main LaTeX file. The supplied PDF is compiled from these
sources. All seven plot references name EPS files through the `ReportGraphEPS` macro.
That macro requires each EPS source to be present. For PDF engines it uses the matching
vector PDF companion exported from the identical figure. A traditional latex/dvips
workflow uses the EPS sources directly. This avoids depending on a system EPS converter
when using a PDF engine. Keep both the EPS files and their PDF companions in `report/graphs/`.

For example, from `report/`, compile with Tectonic:

```text
tectonic main.tex
```

Or use a standard XeLaTeX and BibTeX workflow:

```text
xelatex main.tex
bibtex main
xelatex main.tex
xelatex main.tex
```

The bibliography database and generated bibliography are included. No absolute paths
are used by the report. No external diagram assets are required.

## Data scope and group integration

The year labels 1900–1920 reproduce the intended split but **do not represent historical
pelt observations**. The datasets are controlled ODE simulations with recorded noise
and seeds. The primary experiment estimates r, a and m while fixing K, b and e at their
known synthetic values. These assumptions and limitations are stated in the report.

Before the final group submission, merge the other members' sections and replace the
synthetic application with the agreed historical-data analysis if required by the group
project. Retain the synthetic recovery tests as validation. Update the notebook, PDF,
LaTeX, graphs, provenance and ZIP together, so no old and new results are mixed.

## Submission timing

The professor asks for the ZIP **by email at least one week before the scheduled
presentation**. No presentation date or recipient address was supplied here, so no
calendar deadline has been invented. This package has not been emailed or pushed to GitHub.
