"""
Tests unitarios para las herramientas CLI independientes en tools/.
Verifica la ejecución determinista de verify_math.py, validate.py y render.py.
"""

import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT_DIR / "tools"
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(0, str(TOOLS_DIR))

import verify_math
import validate
import render


@pytest.fixture
def example_draft_path():
    return ROOT_DIR / "examples" / "ecuacion-cuadratica" / "assessment-draft.yaml"


def test_verify_math_cli_example_draft(example_draft_path, capsys):
    with patch.object(sys, "argv", ["verify_math.py", str(example_draft_path)]):
        try:
            verify_math.main()
        except SystemExit as e:
            assert e.code == 0
    captured = capsys.readouterr()
    assert "DICTAMEN GATE 1: PASS" in captured.out
    assert "Distractores mutuamente excluyentes" in captured.out


def test_verify_math_cli_json_output(example_draft_path, capsys):
    with patch.object(sys, "argv", ["verify_math.py", str(example_draft_path), "--json"]):
        try:
            verify_math.main()
        except SystemExit as e:
            assert e.code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "PASS"
    assert data["passed"] is True
    assert data["items_total"] == 3


def test_verify_math_cli_expr(capsys):
    with patch.object(sys, "argv", ["verify_math.py", "--expr", "x^2 - 16 = 0"]):
        try:
            verify_math.main()
        except SystemExit as e:
            assert e.code == 0
    captured = capsys.readouterr()
    assert "Soluciones:   ['-4', '4']" in captured.out


def test_verify_math_cli_solve(capsys):
    with patch.object(sys, "argv", ["verify_math.py", "--solve", "3*x - 9 = 0"]):
        try:
            verify_math.main()
        except SystemExit as e:
            assert e.code == 0
    captured = capsys.readouterr()
    assert "Soluciones: ['3']" in captured.out


def test_verify_math_cli_geom(capsys):
    with patch.object(sys, "argv", ["verify_math.py", "--check-geom", "triangle: 3, 4, 5", "--json"]):
        try:
            verify_math.main()
        except SystemExit as e:
            assert e.code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "PASS"
    assert data["detail"]["valid"] is True


def test_verify_math_cli_prob(capsys):
    with patch.object(sys, "argv", ["verify_math.py", "--check-prob", "0.2, 0.5, 0.3", "--json"]):
        try:
            verify_math.main()
        except SystemExit as e:
            assert e.code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "PASS"
    assert data["detail"]["all_valid"] is True


def test_verify_math_cli_comb(capsys):
    with patch.object(sys, "argv", ["verify_math.py", "--check-comb", "n=5, k=2, c=10", "--json"]):
        try:
            verify_math.main()
        except SystemExit as e:
            assert e.code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "PASS"
    assert data["detail"]["true_combinations"] == 10


def test_validate_cli_all(capsys):
    with patch.object(sys, "argv", ["validate.py", "--all"]):
        try:
            validate.main()
        except SystemExit as e:
            assert e.code == 0
    captured = capsys.readouterr()
    assert "DICTAMEN GENERAL: PASS" in captured.out
    assert "assessment-spec.json" in captured.out
    assert "chile-mineduc.yaml" in captured.out


def test_validate_cli_single_file(example_draft_path, capsys):
    with patch.object(sys, "argv", ["validate.py", str(example_draft_path), "--json"]):
        try:
            validate.main()
        except SystemExit as e:
            assert e.code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "PASS"
    assert data["passed"] is True
    assert data["errors_count"] == 0


def test_render_cli_typst(example_draft_path):
    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = Path(tmpdir) / "output.typ"
        with patch.object(sys, "argv", ["render.py", str(example_draft_path), "--format", "typst", "-o", str(out_file), "--json"]):
            try:
                render.main()
            except SystemExit as e:
                assert e.code == 0
        assert out_file.exists()
        content = out_file.read_text(encoding="utf-8")
        assert "Evaluación" in content or "Evaluaci" in content


def test_render_cli_latex(example_draft_path):
    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = Path(tmpdir) / "output.tex"
        with patch.object(sys, "argv", ["render.py", str(example_draft_path), "--format", "latex", "-o", str(out_file), "--json"]):
            try:
                render.main()
            except SystemExit as e:
                assert e.code == 0
        assert out_file.exists()
        content = out_file.read_text(encoding="utf-8")
        assert "\\documentclass" in content


def test_render_cli_moodle(example_draft_path):
    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = Path(tmpdir) / "output.xml"
        with patch.object(sys, "argv", ["render.py", str(example_draft_path), "--format", "moodle", "-o", str(out_file), "--json"]):
            try:
                render.main()
            except SystemExit as e:
                assert e.code == 0
        assert out_file.exists()
        content = out_file.read_text(encoding="utf-8")
        assert "<quiz>" in content
