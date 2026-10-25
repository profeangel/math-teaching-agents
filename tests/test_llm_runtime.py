"""
Tests unitarios para el runtime de agentes LLM y el orquestador didáctico.
Verifica carga de especificaciones, pipeline Zero-Trust, Self-Healing Loop y multi-etapa.
"""

from pathlib import Path
import tempfile
import yaml

from math_teaching_agents.llm_runtime import (
    AgentLoader,
    DidacticPipeline,
    MockLLMProvider,
    get_provider
)


def test_agent_loader_discovery():
    loader = AgentLoader()
    agents = loader.list_agents()
    assert len(agents) >= 10
    assert "orchestrator" in agents
    assert "evaluator" in agents
    assert "mtsk-kot" in agents

    spec = loader.load_agent("mtsk-kot")
    assert spec is not None
    assert spec.id == "mtsk-kot"
    assert len(spec.system_prompt) > 50


def test_didactic_pipeline_execution_latex():
    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline = DidacticPipeline(provider=MockLLMProvider())
        result = pipeline.run(
            topic="Ecuación cuadrática",
            curriculum_id="chile-mineduc",
            framework_id="duval-trrs",
            output_format="latex",
            output_dir=Path(tmpdir)
        )

        assert result["status"] == "COMPLETED"
        assert result["gate_1"]["status"] == "APPROVED"
        assert result["gate_2"]["status"] == "APPROVED"
        assert Path(result["draft_path"]).exists()
        assert Path(result["rendered_path"]).exists()
        assert result["rendered_path"].endswith(".tex")


def test_didactic_pipeline_execution_typst():
    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline = DidacticPipeline(provider=MockLLMProvider())
        result = pipeline.run(
            topic="Ecuación cuadrática",
            curriculum_id="mexico-nem",
            framework_id="godino-eos",
            output_format="typst",
            output_dir=Path(tmpdir)
        )

        assert result["status"] == "COMPLETED"
        assert result["gate_1"]["status"] == "APPROVED"
        assert result["gate_2"]["status"] == "APPROVED"
        assert Path(result["rendered_path"]).exists()
        assert result["rendered_path"].endswith(".typ")


def test_didactic_pipeline_execution_moodle():
    """Verifica la generación directa de archivos Moodle XML para importación LMS."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline = DidacticPipeline(provider=MockLLMProvider())
        result = pipeline.run(
            topic="Ecuaciones Cuadráticas",
            curriculum_id="colombia-men",
            framework_id="brousseau-tds",
            output_format="moodle",
            output_dir=Path(tmpdir)
        )

        assert result["status"] == "COMPLETED"
        assert result["gate_1"]["status"] == "APPROVED"
        assert result["gate_2"]["status"] == "APPROVED"
        assert Path(result["rendered_path"]).exists()
        assert result["rendered_path"].endswith(".xml")

        with open(result["rendered_path"], "r", encoding="utf-8") as f:
            content = f.read()
            assert "<quiz>" in content
            assert '<question type="multichoice">' in content


def test_didactic_pipeline_gate1_rejection_fail_fast():
    """Verifica que si el LLM persiste en alucinar distractores duplicados, se rechaza tras agotar reintentos."""
    flawed_draft = {
        "metadata": {
            "title": "Evaluación con Alucinación",
            "assessment_type": "SUMATIVA",
            "target_grade": "1° Medio",
            "total_points": 5
        },
        "specification_table": {
            "cognitive_process_distribution": {"aplicar": 100},
            "knowledge_type_distribution": {"procedural": 100}
        },
        "items": [
            {
                "item_id": 1,
                "format": "MULTIPLE_CHOICE",
                "bloom_anderson_level": "APLICAR_PROCEDURAL",
                "mtsk_subdomain": "KoT",
                "points": 5,
                "stem": "Resuelva $x^2 - 4 = 0$",
                "options": [
                    {"key": "A", "text": "2 y -2", "is_correct": True},
                    {"key": "B", "text": "2", "is_correct": False},
                    {"key": "C", "text": "2/1", "is_correct": False},  # Duplicado matemático de 2
                    {"key": "D", "text": "0", "is_correct": False}
                ]
            }
        ]
    }

    flawed_provider = MockLLMProvider(canned_response=yaml.dump(flawed_draft))
    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline = DidacticPipeline(provider=flawed_provider)
        result = pipeline.run(
            topic="Alucinación",
            output_dir=Path(tmpdir),
            max_retries=2
        )

        assert result["status"] == "REJECTED_BY_EVALUATOR"
        assert result["gate_1"]["status"] == "REJECTED"
        assert result["gate_1"]["math_symbolic_check"]["status"] == "FAIL"
        # Bloqueo estricto: Gate 2 NO debe haberse ejecutado ni creado render
        assert "gate_2" not in result
        assert result["attempts_exhausted"] == 2


def test_didactic_pipeline_self_healing_loop_success():
    """
    Verifica el bucle de autorreparación:
    Intento 1 falla por distractor duplicado, Intento 2 recibe feedback de Gate 1 y se corrige exitosamente.
    """
    flawed_draft = {
        "metadata": {
            "title": "Evaluación Corregible",
            "assessment_type": "FORMATIVA",
            "target_grade": "2° Medio",
            "total_points": 5
        },
        "specification_table": {
            "cognitive_process_distribution": {"aplicar": 100},
            "knowledge_type_distribution": {"procedural": 100}
        },
        "items": [
            {
                "item_id": 1,
                "format": "MULTIPLE_CHOICE",
                "bloom_anderson_level": "APLICAR_PROCEDURAL",
                "mtsk_subdomain": "KoT",
                "points": 5,
                "stem": "Resuelva $x^2 - 9 = 0$",
                "options": [
                    {"key": "A", "text": r"$\{3, -3\}$", "is_correct": True},
                    {"key": "B", "text": "3", "is_correct": False},
                    {"key": "C", "text": "3/1", "is_correct": False},  # Duplicado en intento 1
                    {"key": "D", "text": "0", "is_correct": False}
                ]
            }
        ]
    }

    valid_draft = {
        "metadata": {
            "title": "Evaluación Reparada",
            "assessment_type": "FORMATIVA",
            "target_grade": "2° Medio",
            "total_points": 5
        },
        "specification_table": {
            "cognitive_process_distribution": {"aplicar": 100},
            "knowledge_type_distribution": {"procedural": 100}
        },
        "items": [
            {
                "item_id": 1,
                "format": "MULTIPLE_CHOICE",
                "bloom_anderson_level": "APLICAR_PROCEDURAL",
                "mtsk_subdomain": "KoT",
                "points": 5,
                "stem": "Resuelva $x^2 - 9 = 0$",
                "options": [
                    {"key": "A", "text": r"$\{3, -3\}$", "is_correct": True},
                    {"key": "B", "text": r"$\{3\}$", "is_correct": False},
                    {"key": "C", "text": r"$\{-3\}$", "is_correct": False},  # Corregido: ya no es 3/1
                    {"key": "D", "text": r"$\{0\}$", "is_correct": False}
                ]
            }
        ]
    }

    # Secuencia: 1ro genera flawed, 2do genera valid tras recibir feedback
    provider = MockLLMProvider(responses_sequence=[yaml.dump(flawed_draft), yaml.dump(valid_draft)])

    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline = DidacticPipeline(provider=provider)
        result = pipeline.run(
            topic="Ecuaciones cuadráticas",
            output_dir=Path(tmpdir),
            max_retries=3
        )

        assert result["status"] == "COMPLETED"
        assert result["gate_1"]["status"] == "APPROVED"
        assert result["attempts_needed"] == 2
        assert len(result["gate_1"]["history_repairs"]) == 1
        assert "Fallo Matemático SymPy" in result["gate_1"]["history_repairs"][0]["notes"][0]


def test_didactic_pipeline_multi_stage_execution():
    """Verifica que la orquestación multi-etapa ejecuta la fase de análisis didáctico previo."""
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = MockLLMProvider()
        pipeline = DidacticPipeline(provider=provider)
        result = pipeline.run(
            topic="Completación de Cuadrados",
            curriculum_id="spain-lomloe",
            framework_id="duval-trrs",
            multi_stage=True,
            output_dir=Path(tmpdir)
        )

        assert result["status"] == "COMPLETED"
        assert result["multi_stage"] is True
        assert len(provider.call_history) >= 2  # Al menos fase 1 análisis y fase 2 redacción


def test_didactic_pipeline_unit_execution():
    """Verifica que el pipeline genere una unidad didáctica conforme a schemas/didactic-unit.json."""
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = MockLLMProvider()
        pipeline = DidacticPipeline(provider=provider)
        result = pipeline.run(
            topic="Modelización de Parábolas y Caída Libre",
            curriculum_id="chile-mineduc",
            framework_id="brousseau-tds",
            output_format="typst",
            multi_stage=True,
            artifact_type="didactic-unit",
            output_dir=Path(tmpdir)
        )

        assert result["status"] == "COMPLETED"
        assert result["artifact_type"] == "didactic-unit"
        assert result["gate_1"]["status"] == "APPROVED"
        assert result["gate_2"]["status"] == "APPROVED"
        assert Path(result["draft_path"]).name == "didactic-unit-draft.yaml"
        assert Path(result["rendered_path"]).name == "didactic-unit-rendered.typ"
        assert Path(result["rendered_path"]).exists()

        # Verificar contenido clave generado
        with open(result["rendered_path"], "r", encoding="utf-8") as f:
            content = f.read()
            assert "PLANIFICACIÓN DE UNIDAD DIDÁCTICA" in content
            assert "Fase 1" in content
            assert "HACIENDO_MATEMATICA" in content
