"""
Tests unitarios para el Punto de Control Humano (Human-in-the-Loop Checkpoint)
y su integración con el pipeline didáctico y el evaluador Zero-Trust.
"""

from pathlib import Path
import tempfile
import yaml
from math_teaching_agents.human_review import format_didactic_summary, execute_human_review
from math_teaching_agents.llm_runtime import DidacticPipeline, MockLLMProvider


def test_format_didactic_summary_assessment():
    draft = {
        "metadata": {
            "title": "Evaluación Diagnóstica: Álgebra",
            "assessment_type": "DIAGNOSTICA",
            "modality": "INDIVIDUAL",
            "target_grade": "1ro Medio",
            "total_points": 20,
            "passing_threshold_percentage": 60,
            "estimated_duration_minutes": 40
        },
        "specification_table": {
            "cognitive_process_distribution": {"comprender": 50, "aplicar": 50}
        },
        "items": [
            {
                "item_id": 1,
                "format": "MULTIPLE_CHOICE",
                "stem": "Resuelve $2x + 4 = 10$",
                "bloom_anderson_level": "APLICAR_PROCEDURAL",
                "mtsk_subdomain": "KoT",
                "points": 2,
                "options": [
                    {"key": "A", "text": "3", "is_correct": True},
                    {"key": "B", "text": "7", "is_correct": False, "misconception_ref": "MISCON_ADD_INSTEAD_SUB"}
                ]
            }
        ]
    }
    summary = format_didactic_summary(draft, artifact_type="assessment")
    assert "PUNTO DE CONTROL HUMANO" in summary
    assert "Evaluación Diagnóstica: Álgebra" in summary
    assert "Resuelve $2x + 4 = 10$" in summary
    assert "CLAVE CORRECTA" in summary
    assert "MISCON_ADD_INSTEAD_SUB" in summary


def test_format_didactic_summary_didactic_unit():
    draft = {
        "metadata": {
            "title": "Unidad Didáctica: Geometría Analítica",
            "target_grade": "3ro Medio",
            "didactic_framework": "Brousseau TDS",
            "estimated_duration_sessions": 4,
            "hours_per_session": 2
        },
        "phases": [
            {
                "phase_id": 1,
                "phase_name": "Situación de Acción: Medición",
                "cognitive_demand": "HACIENDO_MATEMATICA",
                "teacher_role": "Presenta el problema sin fórmulas.",
                "student_activity": "Miden distancias sobre planos.",
                "example_choice_rationale": "Uso de triángulos 3-4-5."
            }
        ]
    }
    summary = format_didactic_summary(draft, artifact_type="didactic-unit")
    assert "Unidad Didáctica: Geometría Analítica" in summary
    assert "Situación de Acción" in summary
    assert "HACIENDO_MATEMATICA" in summary


def test_execute_human_review_non_interactive():
    draft = {"metadata": {"title": "Test non interactive"}}
    res = execute_human_review(draft, non_interactive=True)
    assert res["status"] == "APPROVED"
    assert res["modified"] is False


def test_execute_human_review_approve():
    draft = {"metadata": {"title": "Test approval"}}
    res = execute_human_review(draft, simulated_choice="1")
    assert res["status"] == "APPROVED"
    assert res["modified"] is False


def test_execute_human_review_cancel():
    draft = {"metadata": {"title": "Test cancel"}}
    res = execute_human_review(draft, simulated_choice="4")
    assert res["status"] == "CANCELLED"
    assert res["modified"] is False


def test_execute_human_review_modify_console():
    draft = {"metadata": {"title": "Título Original", "estimated_duration_minutes": 45}}
    simulated_inputs = ["Nuevo Título de Evaluación", "60"]
    input_iter = iter(simulated_inputs)

    res = execute_human_review(
        draft_data=draft,
        simulated_choice="3",
        console_input_fn=lambda prompt: next(input_iter)
    )
    assert res["status"] == "MODIFIED"
    assert res["modified"] is True
    assert res["draft_data"]["metadata"]["title"] == "Nuevo Título de Evaluación"
    assert res["draft_data"]["metadata"]["estimated_duration_minutes"] == 60


def test_didactic_pipeline_with_human_review_approval():
    root = Path(__file__).resolve().parents[1]
    pipeline = DidacticPipeline(root_dir=root, provider=MockLLMProvider())

    with tempfile.TemporaryDirectory() as tmpdir:
        res = pipeline.run(
            topic="Ecuaciones Lineales",
            output_dir=Path(tmpdir),
            interactive_review=True,
            review_callback=lambda data, path: {"status": "APPROVED", "modified": False, "draft_data": data}
        )
        assert res["status"] == "COMPLETED"
        assert res["gate_1"]["status"] == "APPROVED"
        assert "gate_2" in res


def test_didactic_pipeline_with_human_review_cancellation():
    root = Path(__file__).resolve().parents[1]
    pipeline = DidacticPipeline(root_dir=root, provider=MockLLMProvider())

    with tempfile.TemporaryDirectory() as tmpdir:
        res = pipeline.run(
            topic="Ecuaciones Lineales",
            output_dir=Path(tmpdir),
            interactive_review=True,
            review_callback=lambda data, path: {"status": "CANCELLED", "modified": False, "draft_data": data}
        )
        assert res["status"] == "CANCELLED_BY_USER"
        assert "gate_2" not in res


def test_didactic_pipeline_with_human_review_modification_passes_gate1():
    root = Path(__file__).resolve().parents[1]
    pipeline = DidacticPipeline(root_dir=root, provider=MockLLMProvider())

    def custom_mod(data, path):
        # Modificar título legítimamente sin romper contratos
        mod_data = dict(data)
        mod_data["metadata"] = dict(mod_data["metadata"])
        mod_data["metadata"]["title"] = "Evaluación Personalizada por el Docente"
        return {"status": "MODIFIED", "modified": True, "draft_data": mod_data}

    with tempfile.TemporaryDirectory() as tmpdir:
        res = pipeline.run(
            topic="Ecuaciones Lineales",
            output_dir=Path(tmpdir),
            interactive_review=True,
            review_callback=custom_mod
        )
        assert res["status"] == "COMPLETED"
        assert res["gate_1"]["status"] == "APPROVED"
        # Verificar que el borrador persistido contiene el título modificado
        saved_yaml = Path(res["draft_path"]).read_text(encoding="utf-8")
        assert "Evaluación Personalizada por el Docente" in saved_yaml


def test_didactic_pipeline_with_human_review_zero_trust_rejects_bad_math():
    root = Path(__file__).resolve().parents[1]
    pipeline = DidacticPipeline(root_dir=root, provider=MockLLMProvider())

    def bad_math_mod(data, path):
        # Modificación humana con error matemático: hace dos distractores equivalentes
        import copy
        mod_data = copy.deepcopy(data)
        # Forzar distractor duplicado en el primer ítem
        mod_data["items"][0]["options"][1]["text"] = mod_data["items"][0]["options"][0]["text"]
        return {"status": "MODIFIED", "modified": True, "draft_data": mod_data}

    with tempfile.TemporaryDirectory() as tmpdir:
        res = pipeline.run(
            topic="Ecuaciones Lineales",
            output_dir=Path(tmpdir),
            interactive_review=True,
            review_callback=bad_math_mod
        )
        # Debe fallar en Gate 1 tras la edición humana (Zero-Trust)
        assert res["status"] == "REJECTED_AFTER_HUMAN_REVIEW"
        assert res["gate_1"]["status"] == "REJECTED"
        assert len(res["feedback"]) > 0
