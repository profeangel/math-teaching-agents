"""
test_pedagogical_judge.py
Pruebas unitarias para el Evaluador Pedagógico Semántico (Capa 2: LLM-as-a-Judge).
"""

import pytest
from math_teaching_agents.validators.pedagogical_judge import PedagogicalJudge
from math_teaching_agents.llm_runtime import MockLLMProvider

def test_judge_sound_brousseau_approves():
    judge = PedagogicalJudge()
    good_doc = {
        "title": "Optimización del área",
        "phases": [
            {"name": "Acción", "stem": "Explora el área máxima cercada en un gráfico."},
            {"name": "Formulación", "prompt": "Conjetura y justifica por qué la derivada se anula en el vértice."},
            {"name": "Institucionalización", "definition": "Teorema del punto crítico en funciones cuadráticas."}
        ],
        "registers": ["Gráfico/Geométrico", "Algebraico", "Tabular"]
    }
    res = judge.evaluate(good_doc)
    assert res["status"] == "APPROVED"
    assert res["passed"] is True
    assert res["weighted_score"] >= 3.0
    assert res["scores"]["brousseau_devolution"] >= 3.0

def test_judge_topaze_effect_rejection():
    judge = PedagogicalJudge()
    bad_doc = {
        "title": "Ficha con inducción",
        "stem": "Resuelve la ecuación cuadrática. Recuerda que la respuesta es 3 y debes poner x = 3."
    }
    res = judge.evaluate(bad_doc)
    assert res["status"] == "REJECTED"
    assert res["passed"] is False
    assert res["scores"]["brousseau_devolution"] == 1.0
    assert any("Topaze" in fb for fb in res["feedback"])
    assert len(res["required_actions"]) > 0

def test_judge_multiregister_detection():
    judge = PedagogicalJudge()
    doc_with_registers = "Analiza la tabla de valores, dibuja el gráfico en el plano cartesiano y escribe la función f(x) = x^2."
    res = judge.evaluate(doc_with_registers)
    assert "Gráfico/Geométrico" in res["registers_detected"]
    assert "Tabular" in res["registers_detected"]
    assert "Algebraico/Simbólico" in res["registers_detected"]
    assert res["scores"]["duval_multiregister"] == 4.0

def test_judge_with_mock_llm_canned_response():
    canned_llm_json = """
    ```json
    {
      "status": "APPROVED",
      "weighted_score": 3.75,
      "scores": {
        "brousseau_devolution": 4.0,
        "duval_multiregister": 3.5,
        "bloom_cognitive_demand": 4.0,
        "assessment_quality": 3.5
      },
      "registers_detected": ["Gráfico/Geométrico", "Algebraico"],
      "feedback": ["Excelente articulación de situaciones didácticas"],
      "required_actions": []
    }
    ```
    """
    mock_provider = MockLLMProvider(canned_response=canned_llm_json)
    judge = PedagogicalJudge(provider=mock_provider)
    res = judge.evaluate("Borrador didáctico de prueba")
    assert res["status"] == "APPROVED"
    assert res["weighted_score"] == 3.75
    assert res["scores"]["brousseau_devolution"] == 4.0
    assert len(mock_provider.call_history) == 1
