"""
Tests unitarios para la interfaz de línea de comandos (CLI).
"""

from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
from math_teaching_agents.cli import main


def test_cli_info(capsys):
    with patch.object(sys, "argv", ["math-agent", "info"]):
        try:
            main()
        except SystemExit as e:
            assert e.code == 0
    captured = capsys.readouterr()
    assert "MULTI-AGENT SYSTEM" in captured.out
    assert "Agentes Totales:" in captured.out
    assert "Moodle XML" in captured.out


def test_cli_validate(capsys):
    with patch.object(sys, "argv", ["math-agent", "validate"]):
        try:
            main()
        except SystemExit as e:
            assert e.code == 0
    captured = capsys.readouterr()
    assert "RESULTADO: Todos los contratos y especificaciones son VÁLIDOS." in captured.out


def test_cli_validate_single_file(capsys):
    example_draft = Path(__file__).resolve().parents[1] / "examples" / "ecuacion-cuadratica" / "assessment-draft.yaml"
    with patch.object(sys, "argv", ["math-agent", "validate", str(example_draft)]):
        try:
            main()
        except SystemExit as e:
            assert e.code == 0
    captured = capsys.readouterr()
    assert "VALIDACIÓN DE ESQUEMA DIDÁCTICO" in captured.out
    assert "[OK] El documento cumple estrictamente con el contrato" in captured.out


def test_cli_render_moodle(capsys):
    example_draft = Path(__file__).resolve().parents[1] / "examples" / "ecuacion-cuadratica" / "assessment-draft.yaml"
    with tempfile.TemporaryDirectory() as tmpdir:
        out_xml = Path(tmpdir) / "output.xml"
        with patch.object(sys, "argv", ["math-agent", "render", str(example_draft), "--format", "moodle", "-o", str(out_xml)]):
            try:
                main()
            except SystemExit as e:
                assert e.code == 0
        captured = capsys.readouterr()
        assert "[OK] Archivo Moodle XML generado con éxito" in captured.out
        assert out_xml.exists()


def test_cli_run_multi_stage_and_moodle(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch.object(sys, "argv", [
            "math-agent", "run",
            "--topic", "Teorema de Pitágoras",
            "--format", "moodle",
            "--multi-stage",
            "--max-retries", "2",
            "-o", str(tmpdir)
        ]):
            try:
                main()
            except SystemExit as e:
                assert e.code == 0
        captured = capsys.readouterr()
        assert "Estado Global:     COMPLETED" in captured.out
        assert "Gate 1 (CAS):      APPROVED" in captured.out


def test_cli_run_didactic_unit(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch.object(sys, "argv", [
            "math-agent", "run",
            "--type", "didactic-unit",
            "--topic", "Modelización y Funciones Cuadráticas",
            "--framework", "brousseau-tds",
            "--format", "typst",
            "--multi-stage",
            "-o", str(tmpdir)
        ]):
            try:
                main()
            except SystemExit as e:
                assert e.code == 0
        captured = capsys.readouterr()
        assert "Tipo de Artefacto: didactic-unit" in captured.out
        assert "Estado Global:     COMPLETED" in captured.out
        assert "Gate 1 (CAS):      APPROVED" in captured.out
        assert (Path(tmpdir) / "didactic-unit-draft.yaml").exists()
        assert (Path(tmpdir) / "didactic-unit-rendered.typ").exists()
