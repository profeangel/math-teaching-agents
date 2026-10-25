"""
Tests unitarios para el motor de maquetación LaTeX.
"""

from pathlib import Path
from math_teaching_agents.engines.latex_engine import LatexEngine


def test_latex_engine_render():
    engine = LatexEngine()
    assessment_data = {
        "metadata": {
            "title": "Control Formativo N° 1: Álgebra y Ecuaciones",
            "total_points": 15
        },
        "items": [
            {
                "item_id": 1,
                "format": "MULTIPLE_CHOICE",
                "points": 3,
                "stem": "Resuelva la ecuación $x^2 - 9 = 0$ en el conjunto de los números reales.",
                "options": [
                    {"label": "A", "text": "$-3$ y $3$"},
                    {"label": "B", "text": "Solo $3$"},
                    {"label": "C", "text": "Solo $-3$"},
                    {"label": "D", "text": "$9$"}
                ]
            },
            {
                "item_id": 2,
                "format": "OPEN_DEVELOPMENT",
                "points": 6,
                "stem": "Demuestre formalmente que la suma de dos números impares consecutivos es siempre un múltiplo de 4."
            }
        ]
    }

    rendered_tex = engine.render_document(assessment_data)

    assert "Control Formativo" in rendered_tex
    assert "15 pts" in rendered_tex
    assert "Resuelva la" in rendered_tex
    assert "\\begin{tasks}(2)" in rendered_tex
    assert "Espacio reservado para desarrollo" in rendered_tex
    assert "\\end{document}" in rendered_tex


def test_latex_engine_didactic_unit():
    engine = LatexEngine()
    unit_data = {
        "metadata": {
            "unit_title": "Modelización y Raíces de Funciones Cuadráticas",
            "target_grade": "2° Medio / Grado 10",
            "topic": "Ecuaciones Cuadráticas y Parábolas",
            "estimated_sessions": 4,
            "minutes_per_session": 90,
            "curriculum_expectation_ref": "Bases Curriculares Mineduc - OA 04"
        },
        "theoretical_alignment": {
            "active_frameworks": ["brousseau-tds", "duval-trrs"],
            "networking_justification": "Articulación entre TDS y TRRS."
        },
        "epistemological_diagnostics": {
            "target_misconceptions": [
                {
                    "code": "CONFUSION_VERTICE_CON_RAIZ",
                    "description": "Confusión entre vértice y corte con el eje X.",
                    "confrontation_strategy": "Uso de GeoGebra dinámico."
                }
            ],
            "prerequisites_required": ["Ecuaciones lineales", "Funciones"]
        },
        "phases": [
            {
                "phase_id": 1,
                "phase_name": "Situación de Acción: Lanzamiento Experimental",
                "cognitive_demand": "HACIENDO_MATEMATICA",
                "example_choice_rationale": "Función con raíces enteras.",
                "teacher_role": "Devuelve preguntas al medio.",
                "student_activity": "Tabulación y conjeturas.",
                "udl_guidelines": {
                    "representation": "Gráfica y tabla",
                    "action_expression": "Bosquejo libre",
                    "engagement": "Desafío gamificado"
                }
            }
        ]
    }

    rendered = engine.render_document(unit_data)
    assert "PLANIFICACIÓN DE UNIDAD DIDÁCTICA" in rendered
    assert "Modelización y Raíces de Funciones Cuadráticas" in rendered
    assert "Situación de Acción: Lanzamiento Experimental" in rendered
    assert "HACIENDO_MATEMATICA" in rendered
    assert "Pautas DUA" in rendered
    assert "\\end{document}" in rendered
