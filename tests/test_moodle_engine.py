"""
Tests unitarios para el motor de exportación a Moodle XML (MoodleEngine).
"""

from math_teaching_agents.engines.moodle_engine import MoodleEngine


def test_moodle_engine_render():
    engine = MoodleEngine()
    assessment_data = {
        "metadata": {
            "title": "Evaluación Diagnóstica: Álgebra",
            "target_grade": "1° Medio",
            "total_points": 10
        },
        "items": [
            {
                "item_id": 1,
                "format": "MULTIPLE_CHOICE",
                "bloom_anderson_level": "APLICAR",
                "mtsk_subdomain": "KoT",
                "points": 4,
                "stem": "Resuelva la ecuación $x^2 - 4 = 0$.",
                "options": [
                    {
                        "key": "A",
                        "text": r"$\{2, -2\}$",
                        "is_correct": True,
                        "feedback_clue": "Correcto: raíces simétricas."
                    },
                    {
                        "key": "B",
                        "text": r"$\{2\}$",
                        "is_correct": False,
                        "feedback_clue": "Olvidó la raíz negativa.",
                        "misconception_ref": "Olvido de raíz negativa en raíz cuadrada"
                    }
                ]
            },
            {
                "item_id": 2,
                "format": "OPEN_DEVELOPMENT",
                "bloom_anderson_level": "ANALIZAR",
                "mtsk_subdomain": "KPM",
                "points": 6,
                "stem": "Justifique el procedimiento.",
                "rubric": {
                    "criterion_name": "Rigor Demostrativo",
                    "levels": {
                        "avanzado": "Explicación completa con rigor deductivo.",
                        "inicial": "Respuesta incompleta."
                    }
                }
            }
        ]
    }

    xml_output = engine.render_document(assessment_data)

    assert "<?xml version=" in xml_output
    assert "<quiz>" in xml_output
    assert "</quiz>" in xml_output
    assert '<question type="category">' in xml_output
    assert '<question type="multichoice">' in xml_output
    assert '<question type="essay">' in xml_output
    assert '<answer fraction="100"' in xml_output
    assert '<answer fraction="0"' in xml_output
    assert "Diagnóstico didáctico" in xml_output
    assert "Rúbrica de Corrección" in xml_output
    # Verificación de normalización de MathJax para LMS: $...$ -> \( ... \)
    assert r"\(x^2 - 4 = 0\)" in xml_output
