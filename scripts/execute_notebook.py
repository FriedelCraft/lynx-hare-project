"""Execute the delivered notebook in a kernel bound to the current Python environment."""
from pathlib import Path
import argparse
import json
import os
import sys
import nbformat

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT.parent / ".notebook-runtime"
RUNTIME.mkdir(exist_ok=True)
os.environ["JUPYTER_RUNTIME_DIR"] = str(RUNTIME / "runtime")
os.environ["IPYTHONDIR"] = str(RUNTIME / "ipython")
os.environ["MPLCONFIGDIR"] = str(RUNTIME / "matplotlib")
os.environ["JUPYTER_PATH"] = str(RUNTIME)
kernel = RUNTIME / "kernels/lynx-hare-local"
kernel.mkdir(parents=True, exist_ok=True)
(kernel / "kernel.json").write_text(json.dumps({
    "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
    "display_name": "Lynx Hare local", "language": "python"}), encoding="utf-8")
from nbclient import NotebookClient
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--notebook", type=Path, default=ROOT / "notebooks/yash_pinn.ipynb")
args = parser.parse_args()
notebook_path = args.notebook.resolve()
notebook = nbformat.read(notebook_path, as_version=4)
client = NotebookClient(notebook, timeout=900, kernel_name="lynx-hare-local",
                        startup_timeout=60, resources={"metadata": {"path": str(ROOT)}})
client.on_cell_start = lambda cell, cell_index, **kwargs: print(f"Executing cell {cell_index + 1}", flush=True)
print("Starting local notebook kernel", flush=True)
client.execute()
notebook.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
nbformat.write(notebook, notebook_path)
print(f"Executed {sum(c.cell_type == 'code' for c in notebook.cells)} code cells without errors")
