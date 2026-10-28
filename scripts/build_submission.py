"""Build audited group ZIP (default), or separately labelled historical/synthetic ZIP.

Archives stay outside Git and are never emailed by this script.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = ("configs", "contributions", "data", "diagrams", "docs", "notebooks", "presentation", "report", "results", "scripts", "src", "tests")
ROOT_FILES = ("README.md", "SUBMISSION_README.md", "requirements.txt", "pyproject.toml", ".gitignore", ".gitattributes")
SKIP_SUFFIXES = {".pyc", ".pyo", ".pt", ".aux", ".blg", ".out", ".log", ".gz", ".fls", ".fdb_latexmk", ".toc", ".xdv", ".zip"}
SCOPES = {
    "group": ("Lynx_Hare_Group_Project", "notebooks/group_project.ipynb", "report/group_main.tex"),
    "historical": ("Lynx_Hare_Yash_PINN_Historical", "notebooks/yash_historical_pinn.ipynb", "report/yash_historical_main.tex"),
    "synthetic": ("Lynx_Hare_Yash_PINN_Synthetic", "notebooks/yash_pinn.ipynb", "report/main.tex")}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sources():
    files = [ROOT / name for name in ROOT_FILES if (ROOT / name).exists()]
    for folder in FOLDERS:
        for path in sorted((ROOT / folder).rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(ROOT)
            if any(p.startswith((".pytest", ".codex", "__pycache__", ".ipynb_checkpoints")) or p in {".git", ".venv", ".python-packages", "smoke"} for p in rel.parts):
                continue
            if path.suffix in SKIP_SUFFIXES or rel.parts[:2] == ("report", "images"):
                continue
            files.append(path)
    return sorted(set(files))


def resolve_relative(parent, value):
    path = PurePosixPath(parent).parent / value
    assert not path.is_absolute(), "Absolute TeX dependency"
    parts = []
    for part in path.parts:
        if part == "..":
            assert parts, "TeX dependency escapes package"
            parts.pop()
        elif part not in (".", ""):
            parts.append(part)
    return "/".join(parts)


def tex_dependencies(payload, main):
    """Follow actual section/table inputs; validate each literal EPS/PDF plot pair."""
    seen, graphs = set(), set()
    def visit(name):
        if name in seen:
            return
        assert name in payload, f"Missing TeX input: {name}"
        seen.add(name)
        text = re.sub(r"(?<!\\)%[^\n]*", "", payload[name].decode("utf-8"))
        for target in re.findall(r"\\(?:input|include)\{([^}]+)\}", text):
            if "#" not in target and "\\" not in target:
                visit(resolve_relative(name, target if target.endswith(".tex") else target+".tex"))
        refs = re.findall(r"\\ReportGraphEPS(?:\[[^\]]*\])?\{([^}]+)\}", text)
        refs += re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", text)
        for target in refs:
            if "#" in target or "\\" in target:
                continue
            base = PurePosixPath(target).stem
            eps, pdf = "report/graphs/"+base+".eps", "report/graphs/"+base+".pdf"
            assert eps in payload and pdf in payload, f"Missing EPS/PDF graph pair: {target}"
            assert payload[eps].startswith(b"%!PS-Adobe") and payload[pdf].startswith(b"%PDF-")
            graphs.add(eps)
        for bib in re.findall(r"\\bibliography\{([^}]+)\}", text):
            for target in bib.split(","):
                assert resolve_relative(name, target+".bib") in payload, f"Missing bibliography {target}"
    visit(main)
    return seen, graphs


def audit_payload(payload, scope="group"):
    _, nbname, main = SCOPES[scope]
    pdf = str(PurePosixPath(main).with_suffix(".pdf"))
    assert nbname in payload and main in payload and pdf in payload
    assert payload[pdf].startswith(b"%PDF-")
    nb = json.loads(payload[nbname])
    code = [c for c in nb["cells"] if c["cell_type"] == "code"]
    assert code, "Empty notebook"
    for cell in code:
        source = cell["source"] if isinstance(cell["source"], str) else "".join(cell["source"])
        if source.startswith("%%team "):
            source = source.split("\n", 1)[1]
        ast.parse(source)
        assert cell.get("execution_count") is not None, "Unexecuted notebook cell"
        assert not any(o.get("output_type") == "error" for o in cell.get("outputs", []))
    for name, sha in nb["metadata"].get("embedded_source_sha256", {}).items():
        assert digest(payload["src/lynx_hare/"+name]) == sha, f"Embedded source mismatch: {name}"
    for name, sha in nb["metadata"].get("source_notebook_sha256", {}).items():
        assert digest(payload[name]) == sha, f"Credited notebook changed: {name}"
    tex, graphs = tex_dependencies(payload, main)
    if scope == "synthetic":
        datasets = [n for n in payload if n.startswith("data/synthetic/") and n.endswith(".csv")]
        assert len(datasets) == 5
    else:
        record = json.loads(payload["data/historical/split.json"])
        datasets = []
        for part in ("master", "train", "test"):
            name = "data/historical/"+record[part]["file"]
            assert digest(payload[name]) == record[part]["sha256"], f"Dataset hash mismatch: {name}"
            datasets.append(name)
        provenance = json.loads(payload["data/historical/provenance.json"])
        for key in ("source", "cross_check"):
            entry = provenance[key]
            name = "data/historical/"+entry["raw_copy"]
            assert digest(payload[name]) == entry["raw_sha256"]
            datasets.append(name)
    assert "diagrams/README.md" in payload
    if scope == "group":
        assert "presentation/group_presentation.pptx" in payload
        assert "presentation/yash_historical_slides.pptx" in payload
    return {"status": "passed", "scope": scope, "notebook": nbname,
            "executed_notebook_code_cells": len(code), "main_tex": main, "report_pdf": pdf,
            "tex_inputs": sorted(tex), "referenced_eps_graphs": sorted(graphs),
            "datasets": sorted(datasets), "separate_diagrams_used": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT.parent / "submission")
    parser.add_argument("--extract-check", action="store_true")
    parser.add_argument("--scope", choices=SCOPES, default="group")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    payload = {p.relative_to(ROOT).as_posix(): p.read_bytes() for p in sources()}
    audit = audit_payload(payload, args.scope)
    manifest = {"audit": audit, "files": [{"path": n, "sha256": digest(v), "bytes": len(v)} for n,v in sorted(payload.items())]}
    payload["SUBMISSION_MANIFEST.json"] = (json.dumps(manifest, indent=2)+"\n").encode()
    archive_root = SCOPES[args.scope][0]
    dest = args.output / (archive_root+".zip")
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, body in sorted(payload.items()):
            z.writestr(archive_root+"/"+name, body)
    extracted = None
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        readback = {str(PurePosixPath(n).relative_to(archive_root)): z.read(n) for n in z.namelist()}
        assert readback == payload
        audit_payload(readback, args.scope)
        if args.extract_check:
            parent = ROOT.parent / ".submission-build"
            parent.mkdir(exist_ok=True)
            check = Path(tempfile.mkdtemp(prefix="group_check_", dir=parent)).resolve()
            for member in z.namelist():
                assert (check/member).resolve().is_relative_to(check), "Unsafe ZIP member"
            z.extractall(check)
            extracted = str(check/archive_root)
    receipt = {**audit, "zip": str(dest.resolve()), "bytes": dest.stat().st_size,
               "sha256": digest(dest.read_bytes()), "archive_files": len(payload),
               "extracted_check_root": extracted, "sent_by_email": False, "zip_pushed_to_github": False}
    (args.output / ("submission_verification_"+args.scope+".json")).write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
