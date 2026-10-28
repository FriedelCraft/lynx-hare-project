"""Packaging checks follow active TeX inputs and require real EPS sources."""
import importlib.util
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('submission_builder',ROOT/'scripts/build_submission.py')
builder=importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def test_dynamic_graph_discovery_follows_only_active_sections():
    payload={'report/main.tex':br'\input{part}\ReportGraphEPS{one.eps}',
             'report/part.tex':br'\includegraphics[width=1cm]{two}',
             'report/unused.tex':br'\includegraphics{missing}',
             'report/graphs/one.eps':b'%!PS-Adobe', 'report/graphs/one.pdf':b'%PDF-',
             'report/graphs/two.eps':b'%!PS-Adobe', 'report/graphs/two.pdf':b'%PDF-'}
    inputs,graphs=builder.tex_dependencies(payload,'report/main.tex')
    assert inputs=={'report/main.tex','report/part.tex'}
    assert len(graphs)==2


def test_pdf_companion_cannot_replace_required_eps():
    payload={'report/main.tex':br'\includegraphics{one}', 'report/graphs/one.pdf':b'%PDF-'}
    with pytest.raises(AssertionError,match='EPS/PDF'):
        builder.tex_dependencies(payload,'report/main.tex')


def test_tex_dependency_cannot_escape_archive():
    with pytest.raises(AssertionError,match='escapes'):
        builder.resolve_relative('report/main.tex','../../outside.tex')
