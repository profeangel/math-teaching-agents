"""
Tests unitarios para la gestión del perfil pedagógico y la inicialización de docente (math-agent init).
"""

from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

from math_teaching_agents.profile import (
    load_profile,
    save_profile,
    inject_profile_into_prompt,
    run_init_wizard,
    DEFAULT_PROFILE,
)
from math_teaching_agents.cli import main
from math_teaching_agents.llm_runtime import DidacticPipeline, MockLLMProvider


def test_default_profile_structure():
    assert "educator" in DEFAULT_PROFILE
    assert "interaction_mode" in DEFAULT_PROFILE
    assert "tooling_preferences" in DEFAULT_PROFILE
    assert DEFAULT_PROFILE["interaction_mode"]["tone"] == "pragmatic"


def test_save_and_load_profile():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        prof_data = {
            "version": "1.0",
            "educator": {"name": "Prof. Soto", "level": "high_school", "curriculum_default": "mexico-nem"},
            "interaction_mode": {"tone": "mentoring", "collaboration": "co-design"},
            "tooling_preferences": {"output_format": "typst", "auto_compile": True}
        }
        saved_file = save_profile(prof_data, root_dir=tmp_path)
        assert saved_file.exists()
        assert saved_file.name == ".math-agent.yaml"

        loaded = load_profile(root_dir=tmp_path)
        assert loaded is not None
        assert loaded["educator"]["name"] == "Prof. Soto"
        assert loaded["interaction_mode"]["tone"] == "mentoring"
        assert loaded["educator"]["curriculum_default"] == "mexico-nem"


def test_inject_profile_into_prompt():
    base_prompt = "Eres un especialista en didáctica de la matemática."

    # Pragmatic
    prof_pragmatic = {
        "educator": {"name": "Prof. Pérez", "level": "secondary"},
        "interaction_mode": {"tone": "pragmatic"}
    }
    injected_prag = inject_profile_into_prompt(prof_pragmatic, base_prompt)
    assert "MODO PRÁCTICO" in injected_prag
    assert "lenguaje cotidiano" in injected_prag

    # Mentoring
    prof_mentor = {
        "educator": {"name": "Prof. Clara", "level": "primary"},
        "interaction_mode": {"tone": "mentoring"}
    }
    injected_ment = inject_profile_into_prompt(prof_mentor, base_prompt)
    assert "MODO FORMATIVO" in injected_ment
    assert "mentor empático" in injected_ment

    # Academic
    prof_acad = {
        "educator": {"name": "Dra. Valenzuela", "level": "university"},
        "interaction_mode": {"tone": "academic"}
    }
    injected_acad = inject_profile_into_prompt(prof_acad, base_prompt)
    assert "MODO ACADÉMICO" in injected_acad
    assert "máximo rigor epistemológico" in injected_acad


def test_run_init_wizard_non_interactive():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        answers = {
            "name": "Profesor Gómez",
            "level": "secondary",
            "curriculum": "colombia-men",
            "tone": "academic",
            "format": "latex"
        }
        res = run_init_wizard(root_dir=tmp_path, non_interactive=True, answers=answers, force=True)
        assert res["educator"]["name"] == "Profesor Gómez"
        assert res["educator"]["curriculum_default"] == "colombia-men"
        assert res["interaction_mode"]["tone"] == "academic"
        assert (tmp_path / ".math-agent.yaml").exists()


def test_cli_init_command(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("math_teaching_agents.cli.get_root_dir", return_value=Path(tmpdir)):
            with patch.object(sys, "argv", [
                "math-agent", "init",
                "--non-interactive",
                "--name", "Prof. Valdés",
                "--level", "secondary",
                "--curriculum", "spain-lomloe",
                "--tone", "mentoring",
                "--format", "typst"
            ]):
                try:
                    main()
                except SystemExit as e:
                    assert e.code == 0

            captured = capsys.readouterr()
            assert "CONFIGURACIÓN INICIAL (MODO DESATENDIDO)" in captured.out
            assert "Prof. Valdés" in captured.out
            assert "spain-lomloe" in captured.out
            assert "MENTORING" in captured.out
            assert (Path(tmpdir) / ".math-agent.yaml").exists()


def test_cli_info_displays_profile(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        prof_data = {
            "version": "1.0",
            "educator": {"name": "Prof. Ana", "level": "university", "curriculum_default": "international-standard"},
            "interaction_mode": {"tone": "academic", "collaboration": "co-design"},
            "tooling_preferences": {"output_format": "typst", "auto_compile": True}
        }
        save_profile(prof_data, root_dir=Path(tmpdir))

        with patch("math_teaching_agents.cli.get_root_dir", return_value=Path(tmpdir)):
            with patch.object(sys, "argv", ["math-agent", "info"]):
                try:
                    main()
                except SystemExit as e:
                    assert e.code == 0

        captured = capsys.readouterr()
        assert "Docente Activo:           Prof. Ana (university)" in captured.out
        assert "Tono de Interacción:      ACADEMIC" in captured.out
        assert "Currículo Preferido:      international-standard" in captured.out


def test_didactic_pipeline_applies_profile_tone():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(__file__).resolve().parents[1]
        out_dir = Path(tmpdir)
        provider = MockLLMProvider()
        pipeline = DidacticPipeline(root_dir=root, provider=provider)

        custom_profile = {
            "version": "1.0",
            "educator": {"name": "Prof. Roberto", "level": "high_school"},
            "interaction_mode": {"tone": "mentoring"},
            "tooling_preferences": {"output_format": "typst"}
        }

        res = pipeline.run(
            topic="Ecuaciones Lineales",
            output_dir=out_dir,
            profile=custom_profile,
            tone="mentoring"
        )
        assert res["status"] == "COMPLETED"
        assert res.get("profile_applied") is not None
        assert res["profile_applied"]["interaction_mode"]["tone"] == "mentoring"
