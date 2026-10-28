"""Assemble credited team sections without changing frozen scientific experiments."""
import hashlib
import json
import re
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]


def build_nullcline_graph():
    import sys
    sys.path.insert(0, str(ROOT / 'src'))
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from lynx_hare.model import Parameters
    from lynx_hare.simulation_plots import direction_field
    from lynx_hare.stability import coexistence_prey, coexistence_predator
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.7))
    for ax, K in zip(axes, (60, 150)):
        p=Parameters(r=1.5,K=K,a=4,b=30,e=0.4,m=0.8)
        H=np.linspace(0,K,401)
        ax.plot(H,p.r/p.a*(1-H/K)*(p.b+H),color='#215e9c',label='prey nullcline')
        ax.axvline(coexistence_prey(p),color='#c0392b',label='predator nullcline')
        ax.axvline((K-p.b)/2,color='#888888',ls=':',label='hump peak')
        grid, vectors=direction_field(p,K,52,nH=13,nP=11)
        ax.quiver(*grid,*vectors,angles='xy',scale_units='xy',scale=1,color='#aaaaaa',width=0.003)
        ax.plot(coexistence_prey(p),coexistence_predator(p),'o',mec='black',mfc='black' if K<90 else 'white')
        ax.plot([0,K],[0,0],'ko',ms=3)
        ax.set(xlim=(0,K),ylim=(0,52),xlabel='hare H (thousand pelts)',title=f'K = {K}, '+('stable' if K<90 else 'unstable'))
    axes[0].set_ylabel('lynx P (thousand pelts)')
    axes[0].legend(fontsize=7)
    fig.tight_layout()
    folder=ROOT/'results/integration/figures';folder.mkdir(parents=True,exist_ok=True)
    for ext in ('eps','pdf','png'):
        target=folder/f'group_nullclines.{ext}'
        fig.savefig(target,dpi=180)
        if ext!='png':(ROOT/'report/graphs'/target.name).write_bytes(target.read_bytes())
    plt.close(fig)


def build_report():
    # Preserve individual source files and put the model section in the same TeX root.
    arnav = ROOT / "contributions/arnav/sections/arnav_model.tex"
    (ROOT / "report/arnav_model_section.tex").write_text(
        "% Integration copy; canonical source: contributions/arnav/sections/arnav_model.tex\n"
        + arnav.read_text(encoding="utf-8"), encoding="utf-8")
    joel = (ROOT / "report/joel_stability_section.tex").read_text(encoding="utf-8")
    joel = joel.replace("Take any initial condition in the open quadrant.",
                        "Take any initial condition in the open quadrant other than $E^*$.")
    joel = joel.replace('{joel_nullclines}', '{group_nullclines}')
    joel = joel.replace("$\\sigma=K/K_H$: $\\sigma<1$ means damped oscillations, $\\sigma>1$ a limit cycle.",
                        "$\\sigma=K/K_H$, when coexistence is feasible: $\\sigma<1$ gives a locally stable equilibrium (node or focus), while $\\sigma>1$ gives an unstable equilibrium and the model's attracting cycle.")
    start = joel.index("Two structural facts matter for inference.")
    end = joel.index("% ---------------------------------------------------------------------", start)
    joel = joel[:start] + r"""For inference, $a$ and $e$ enter $H^*$ and $K_H$ through $ea$.
If an additional unknown predator observation scale is fitted, the transformation
$(P,a,e)\mapsto(cP,a/c,ec)$ introduces a scale ambiguity. In this historical iteration,
the observed pelt-state units are fixed and no scale factor is fitted, so this
transformation changes the observed predator values and does not by itself prove
non-identifiability of the effective coefficients. All six are fitted. Their practical
uncertainty is assessed using training diagnostics and the declared sensitivity runs,
and $a,e$ are not interpreted as uniquely recovered absolute biological rates.

""" + joel[end:]
    (ROOT / "report/joel_group_section.tex").write_text(
        "% Integration copy: feasibility/observation-scale qualifications reconciled with Arnav and the frozen protocol.\n"+joel, encoding="utf-8")
    bibliography = (ROOT / "report/references.bib").read_text(encoding="utf-8")
    bibliography += "\n" + (ROOT / "contributions/arnav/references.bib").read_text(encoding="utf-8")
    keys = re.findall(r"@\w+\{([^,]+)", bibliography)
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate bibliography keys require reconciliation")
    (ROOT / "report/group_references.bib").write_text(bibliography, encoding="utf-8")
    preamble = (ROOT / "report/main.tex").read_text().split(r"\title{")[0]
    preamble += r"""
\usepackage{amsthm,array,tabularx}
\setlength{\emergencystretch}{2em}
\newtheorem{theorem}{Theorem}
\newtheorem{proposition}{Proposition}
\newtheorem{lemma}{Lemma}
\theoremstyle{remark}\newtheorem{remark}{Remark}
\title{Lynx and Hare Dynamics\\Model, Stability, Numerical Simulation and Inverse Inference}
\author{Arnav \and Joel \and Rishi \and Yash \and Advay}
\date{28 October 2026}
\begin{document}\maketitle
\begin{abstract}
We combine a Rosenzweig--MacArthur model, equilibrium and Hopf analysis, numerical
experiments, and historical parameter fitting using least squares and an inverse PINN.
The Stan pelt-index compilation is split into 1900--1915 training and 1916--1920
evaluation. Primary held-out RMSE is 3.07/3.04 thousand pelts for least squares and
2.85/4.32 for the PINN-derived ODE (hare/lynx). The comparison is mixed; observation-model
and bound sensitivity prevent precise biological recovery or a robust ecological
limit-cycle claim. Frozen numerical evidence, sources and all sensitivity variants
are retained. No final integration step retunes a model using test-year errors.
\end{abstract}
\paragraph{Contributions and evaluation chronology.}
Arnav: model and units. Joel: theory. Rishi: numerical validation. Yash: PINN and
integration. Advay: data and independent least squares/evaluation. Historical forecasts
use the same dimensional RHS and solver configuration. Advay's independent reproduction
followed Yash's published scored iteration, so it is not a new blinded test. Training
demonstrations in the combined notebook do not overwrite the frozen forecasts.
\tableofcontents\clearpage
\input{arnav_model_section}\clearpage
\input{joel_group_section}\clearpage
\input{rishi_simulation_section}\clearpage
\input{yash_historical_section}
\paragraph{PINN optimization gap.}
Advay independently evaluated the training observation objective on the frozen
PINN-derived ODE trajectories. Their costs are 1.859, 3.396 and 1.866 times the
least-squares minima for main, log-error and fitted-initial-state variants. These
are observation costs, not the PINN's weighted neural training loss. The PINN optimizes
a soft-physics network objective, and reintegration can accumulate phase error; it
does not attain the least-squares optimum here. These diagnostics motivate the
reported limitations and do not trigger post-test retuning.
\clearpage\input{advay_data_validation_section}\clearpage
\section{Controlled synthetic validation}
The separate synthetic study tests implementation recovery with known parameters and
3\% observation noise. Across three annual-data seeds, the largest relative error in
the three inferred rates is below 0.36\%. K, b and e are correctly fixed at generating
values for that controlled test; historical fitting instead estimates all six.
This favorable recovery experiment is not evidence of historical parameter accuracy.
Its complete program, recovery tables, residuals and sensitivity runs remain in
\path{notebooks/yash_pinn.ipynb} and \path{results/synthetic/}.
\ReportGraphEPS[width=\linewidth]{parameter_recovery.eps}
\paragraph{Reproduction and acknowledgement.}
Run the combined notebook \path{notebooks/group_project.ipynb} from a fresh Python
environment using the supplied requirements. Full expensive experiment drivers and
individual notebooks remain alongside the frozen evidence. All report plots have EPS
sources and vector PDF companions. Per-person AI assistance and actual manual-review
records are in \path{docs/ai_acknowledgement.md} and Arnav's contribution folder.
Each member remains responsible for understanding and explaining their own work.
\clearpage\bibliographystyle{plain}\bibliography{group_references}
\end{document}
"""
    (ROOT / "report/group_main.tex").write_text(preamble, encoding="utf-8")


def build_notebook():
    cells = [nbf.v4.new_markdown_cell("""# Lynx and hare: complete group analysis
**Arnav, Joel, Rishi, Yash and Advay — MAC F314**

This single notebook assembles model/scaling checks, symbolic stability checks, numerical simulations,
the complete historical inverse-PINN implementation, synthetic recovery evidence and independent
least-squares evaluation. Original credited notebooks and batch programs remain in the package.

Run top to bottom from the repository root or `notebooks/`. Long numerical sections can take several
minutes. The PINN section audits completed frozen runs; it does not silently launch new neural fits.
Advay's live least-squares demonstration uses training rows only and never replaces the saved forecasts.
His independent evaluation followed Yash's scored iteration, and is a reproduction rather than a new
blind test. Pelt counts are abundance indices in thousands, not animal censuses.
""")]
    cells.append(nbf.v4.new_code_cell("""from pathlib import Path
import ast, sys
from IPython.core.magic import register_cell_magic
from IPython.display import display
ROOT=Path.cwd().parent if Path.cwd().name=='notebooks' else Path.cwd()
FULL_LONG_RUN_REPLAY=False  # opt in to repeated 3000-60000-year historical simulations
assert (ROOT/'src/lynx_hare').exists(), 'Run in the project root or notebooks/'
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'scripts'))
TEAM_SCOPES={}
@register_cell_magic
def team(owner, source):
    # Independent namespaces preserve each author's function globals and prevent
    # similarly named model, scale and parameter variables from colliding.
    scope=TEAM_SCOPES.setdefault(owner, {'__name__':owner+'_notebook','ROOT':ROOT,'display':display,'FULL_LONG_RUN_REPLAY':FULL_LONG_RUN_REPLAY})
    tree=ast.parse(source)
    if tree.body and isinstance(tree.body[-1],ast.Expr):
        last=tree.body.pop()
        exec(compile(tree,'<'+owner+'>','exec'),scope)
        value=eval(compile(ast.Expression(last.value),'<'+owner+'>','eval'),scope)
        if value is not None and not source.rstrip().endswith(';'): display(value)
    else:
        exec(compile(tree,'<'+owner+'>','exec'),scope)
print('Project root:', ROOT)
"""))
    originals = [("arnav", "contributions/arnav/arnav_model_explained.ipynb"),
                 ("rishi", "notebooks/rishi_simulations.ipynb"),
                 ("yash", "notebooks/yash_historical_pinn.ipynb"),
                 ("advay", "notebooks/advay_data_validation.ipynb")]
    source_hashes = {}
    for owner, name in originals:
        if owner == "rishi":
            cells += [nbf.v4.new_markdown_cell("## Joel: symbolic stability verification\nThe following program verifies equilibria, the Jacobian, Hopf threshold and scaling algebra. The report supplies the derivations and theorem assumptions."),
                      nbf.v4.new_code_cell("%%team joel\nimport runpy\nrunpy.run_path(str(ROOT/'scripts/joel_symbolic_derivation.py'));\n")]
        path = ROOT / name
        source_hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        cells.append(nbf.v4.new_markdown_cell(f"---\n## {owner.title()}: credited contribution\nCanonical notebook: `{name}`. Cells below execute in the `{owner}` namespace."))
        notebook = nbf.read(path, as_version=4)
        for original in notebook.cells:
            if original.cell_type == "code":
                source = original.source
                if owner == "rishi" and 'placement["compute"]()' in source:
                    heavy = '\n'.join('    '+line for line in source.splitlines())
                    source = ('if FULL_LONG_RUN_REPLAY:\n'+heavy+'\nelse:\n'
                              '    import json\n'
                              '    from lynx_hare import simulation as shared_sim\n'
                              '    from lynx_hare.model import Parameters as SharedParameters\n'
                              '    stored=pd.read_csv(ROOT/"results/simulations/historical/fits.csv")\n'
                              '    display(stored)\n'
                              '    summary=json.loads((ROOT/"results/simulations/historical/summary.json").read_text())\n'
                              '    print("Frozen historical long-run summaries:", summary.keys())\n'
                              '    for fitted in json.loads((ROOT/"results/historical/yash_pinn_v1/parameters_for_team.json").read_text()):\n'
                              '        p=SharedParameters(**{k:fitted[k] for k in ["r","K","a","b","e","m"]})\n'
                              '        assert abs(shared_sim.linear_summary(p)["sigma"]-fitted["sigma"])<1e-10\n'
                              '    print("Historical sigma rechecked; set FULL_LONG_RUN_REPLAY=True for expensive long-run regeneration.")')
                elif owner == "rishi" and 'placement["figures"](res)' in source:
                    heavy = '\n'.join('    '+line for line in source.splitlines())
                    source = ('if FULL_LONG_RUN_REPLAY:\n'+heavy+'\nelse:\n'
                              '    from IPython.display import Image\n'
                              '    for stem in ["rishi_historical_sigma","rishi_historical_bifurcation"]:\n'
                              '        display(Image(filename=str(ROOT/"results/simulations/historical/figures"/(stem+".png"))))')
                cells.append(nbf.v4.new_code_cell(f"%%team {owner}\n" + source))
            elif original.cell_type == "markdown":
                cells.append(nbf.v4.new_markdown_cell(original.source))
    cells += [nbf.v4.new_markdown_cell("## Synthetic recovery and final verification\nThe controlled synthetic validation is separate from the historical experiment. These checks reconstruct evidence and scores without fitting or selecting a new model."),
              nbf.v4.new_code_cell("""%%team verification
import subprocess,sys,csv,json
for script in ['verify_outputs.py','verify_historical_outputs.py']:
    subprocess.run([sys.executable,str(ROOT/'scripts'/script)],cwd=ROOT,check=True)
with (ROOT/'results/synthetic/parameter_recovery.csv').open() as f:
    recovery=list(csv.DictReader(f))
display(recovery[:6])
print('Final evaluation retains all declared sensitivities. Seed spread is not a confidence interval.')
""")]
    nb = nbf.v4.new_notebook(cells=cells)
    nb.metadata.kernelspec = {"name": "python3", "display_name": "Python 3", "language": "python"}
    nb.metadata.source_notebook_sha256 = source_hashes
    nb.metadata.execution_note = "Default replays illustrative simulations and live LS demos; historical 3000-60000-year recomputation is opt-in. Frozen historical sigma is independently checked."
    nbf.write(nb, ROOT / "notebooks/group_project.ipynb")
    print(f"Assembled {len(cells)} cells, {sum(c.cell_type=='code' for c in cells)} executable cells")


if __name__ == "__main__":
    build_nullcline_graph()
    build_report()
    build_notebook()
