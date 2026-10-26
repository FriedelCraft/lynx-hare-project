"""Build and audit the professor-format ZIP using only the Python standard library."""
import argparse
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_ROOT = "Lynx_Hare_Yash_PINN_Synthetic"
FOLDERS = ("configs", "data", "diagrams", "docs", "notebooks", "presentation", "report", "results", "scripts", "src", "tests")
ROOT_FILES = ("README.md", "SUBMISSION_README.md", "requirements.txt", "pyproject.toml", ".gitignore")
SKIP_PARTS = {"__pycache__", ".pytest_cache", ".pytest-work", ".git", ".venv", ".python-packages", ".kernels", "smoke"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".pt", ".aux", ".blg", ".out", ".log", ".synctex", ".gz", ".fls", ".fdb_latexmk"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sources():
    files = [ROOT / name for name in ROOT_FILES]
    for folder in FOLDERS:
        for path in sorted((ROOT / folder).rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(ROOT)
            if any(part in SKIP_PARTS for part in relative.parts) or path.suffix in SKIP_SUFFIXES:
                continue
            # Old PNG report previews are not report inputs; retain the original
            # publication/preview exports under results instead.
            if relative.parts[:2] == ("report", "images"):
                continue
            files.append(path)
    return sorted(set(files))


def audit_payload(payload):
    required = {"notebooks/yash_pinn.ipynb", "report/main.pdf", "report/main.tex",
                "report/yash_pinn_section.tex", "report/diagnostics_appendix.tex", "report/references.bib",
                "data/synthetic/provenance.json", "configs/synthetic.json", "diagrams/README.md"}
    assert required.issubset(payload), f"Missing required files: {required-set(payload)}"
    assert payload["report/main.pdf"].startswith(b"%PDF-")
    notebook = json.loads(payload["notebooks/yash_pinn.ipynb"])
    code_cells = [c for c in notebook["cells"] if c["cell_type"] == "code"]
    assert len(code_cells) == 15
    for cell in code_cells:
        source = cell["source"] if isinstance(cell["source"], str) else "".join(cell["source"])
        ast.parse(source)
        assert cell.get("execution_count") is not None, "Unexecuted notebook cell"
        assert not any(o.get("output_type") == "error" for o in cell.get("outputs", []))
    embedded = notebook["metadata"]["embedded_source_sha256"]
    assert len(embedded) == 6
    for name, value in embedded.items():
        assert digest(payload[f"src/lynx_hare/{name}"]) == value, f"Notebook/module mismatch: {name}"
    graphs = set()
    for name, contents in payload.items():
        if name.startswith("report/") and name.endswith(".tex"):
            text = contents.decode("utf-8")
            graphs.update(re.findall(r"\\ReportGraphEPS(?:\[[^\]]*\])?\{([^}]+\.eps)\}", text))
    assert len(graphs) == 7
    for graph in graphs:
        eps_name = f"report/graphs/{graph}"
        pdf_name = eps_name[:-4] + ".pdf"
        assert eps_name in payload and pdf_name in payload, f"Missing graph: {graph}"
        assert payload[eps_name].startswith(b"%!PS-Adobe")
        assert payload[pdf_name].startswith(b"%PDF-")
    datasets = sorted(n for n in payload if n.startswith("data/synthetic/") and n.endswith(".csv"))
    assert len(datasets) == 5
    provenance = json.loads(payload["data/synthetic/provenance.json"])
    assert provenance["historical_data"] is False
    return {"status": "passed", "executed_notebook_code_cells": len(code_cells),
            "embedded_implementation_modules": len(embedded), "referenced_eps_graphs": sorted(graphs),
            "datasets": datasets, "report_pdf_included": True, "latex_sources_included": True,
            "separate_diagrams_used": False, "scope": "Yash PINN component, synthetic data"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT.parent / "submission")
    parser.add_argument("--extract-check", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    payload = {p.relative_to(ROOT).as_posix(): p.read_bytes() for p in sources()}
    audit = audit_payload(payload)
    manifest = {"scope": audit["scope"], "audit": audit,
                "files": [{"path": name, "bytes": len(contents), "sha256": digest(contents)}
                          for name, contents in sorted(payload.items())]}
    payload["SUBMISSION_MANIFEST.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    destination = args.output / f"{ARCHIVE_ROOT}.zip"
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, contents in sorted(payload.items()):
            archive.writestr(f"{ARCHIVE_ROOT}/{name}", contents)
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None, "ZIP integrity failure"
        readback = {PurePosixPath(n).relative_to(ARCHIVE_ROOT).as_posix(): archive.read(n) for n in archive.namelist()}
        assert readback == payload, "ZIP roundtrip did not preserve every file"
        audit_payload(readback)
        extracted_root = None
        if args.extract_check:
            check_parent = ROOT.parent / ".submission-build"
            check_parent.mkdir(exist_ok=True)
            check_dir = Path(tempfile.mkdtemp(prefix="zip_check_", dir=check_parent)).resolve()
            for member in archive.namelist():
                target = (check_dir / member).resolve()
                assert target.is_relative_to(check_dir), "Unsafe ZIP member path"
            archive.extractall(check_dir)
            extracted_root = str(check_dir / ARCHIVE_ROOT)
    receipt = {**audit, "zip": str(destination.resolve()), "bytes": destination.stat().st_size,
               "sha256": digest(destination.read_bytes()), "archive_files": len(payload),
               "extracted_check_root": extracted_root,
               "sent_by_email": False, "pushed_to_github": False}
    (args.output / "submission_verification.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
