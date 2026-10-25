"""
pedagogical_judge.py
Evaluador Pedagógico Semántico (Capa 2: LLM-as-a-Judge).
Evalúa borradores didácticos y reactivos contra las dimensiones de Brousseau (TSD),
Duval (TRRS), Anderson-Krathwohl (Bloom) y evaluación auténtica (Förster/Brookhart).
"""

import json
import re
from typing import Any, Dict, List, Optional
from math_teaching_agents.llm_runtime import LLMProvider, MockLLMProvider

SYSTEM_PROMPT_JUDGE = """Eres el Auditor Pedagógico de Élite (zero-trust-evaluator / math-auditor) de math-teaching-agents.
Tu labor es realizar una auditoría adversarial estricta e implacable de un borrador didáctico o de evaluación matemática.

Debes evaluar el material en 4 dimensiones críticas puntuando de 1.0 (deficiente) a 4.0 (sobresaliente):
1. brousseau_devolution (0.30 de peso): Ausencia total de Efecto Topaze (el enunciado NO debe adelantar la respuesta ni la técnica) y presencia de fases a-didácticas.
2. duval_multiregister (0.25 de peso): Conversión activa entre al menos 2 registros semióticos (gráfico, tabular, verbal, algebraico).
3. bloom_cognitive_demand (0.25 de peso): Balance de demanda cognitiva (mínimo 40% en análisis, justificación o modelación).
4. assessment_quality (0.20 de peso): Calidad diagnóstica de los distractores (basados en errores reales de la literatura, no azar) y pauta observable.

Umbral de aprobación: Puntaje ponderado >= 3.00 y brousseau_devolution >= 2.50.

Debes responder ÚNICAMENTE con un objeto JSON válido con la siguiente estructura exacta:
{
  "status": "APPROVED" o "REJECTED",
  "weighted_score": float,
  "scores": {
    "brousseau_devolution": float,
    "duval_multiregister": float,
    "bloom_cognitive_demand": float,
    "assessment_quality": float
  },
  "registers_detected": ["Gráfico/Geométrico", "Tabular", ...],
  "feedback": [
    "observación 1",
    "observación 2"
  ],
  "required_actions": [
    "acción correctiva concreta 1"
  ]
}
"""

class PedagogicalJudge:
    """Evaluador Semántico de Calidad Didáctica (Capa 2)."""

    def __init__(self, provider: Optional[LLMProvider] = None):
        self.provider = provider or MockLLMProvider()

    def evaluate(self, content: Any, content_type: str = "yaml") -> Dict[str, Any]:
        """Evalúa el contenido utilizando el proveedor LLM o heurística de respaldo."""
        if isinstance(content, dict):
            text_representation = json.dumps(content, indent=2, ensure_ascii=False)
        else:
            text_representation = str(content)

        # Si el proveedor es MockLLMProvider y no tiene respuesta específica encolada,
        # realizar la evaluación semántica estructurada
        if isinstance(self.provider, MockLLMProvider) and not self.provider.canned_response and not self.provider.responses_sequence:
            return self._evaluate_heuristic(text_representation)

        user_prompt = f"Por favor evalúa el siguiente artefacto didáctico ({content_type}):\n\n```\n{text_representation}\n```"
        
        try:
            raw_response = self.provider.generate(
                system_prompt=SYSTEM_PROMPT_JUDGE,
                user_prompt=user_prompt
            )
            # Extraer JSON de la respuesta
            clean_json = raw_response.strip()
            if "```json" in clean_json:
                clean_json = clean_json.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_json:
                clean_json = clean_json.split("```")[1].split("```")[0].strip()
            
            result = json.loads(clean_json)
            result["passed"] = (result.get("status") == "APPROVED")
            return result
        except Exception:
            # Fallback seguro a evaluación estructurada determinista si falla el parsing
            return self._evaluate_heuristic(text_representation)

    def _evaluate_heuristic(self, text: str) -> Dict[str, Any]:
        """Evaluación estructurada determinista como fallback robusto."""
        lower_text = text.lower()
        feedback = []
        required_actions = []

        # 1. Brousseau & Topaze
        topaze_indicators = ["esos números son", "la respuesta es", "debes poner", "reemplaza directamente", "solo aplica la fórmula"]
        has_topaze = any(t in lower_text for t in topaze_indicators)

        has_action = any(w in lower_text for w in ["acción", "accion", "explora", "problema inicial", "situación", "stem"])
        has_formulation = any(w in lower_text for w in ["formulación", "formulacion", "conjetura", "justifica", "por qué", "analiza"])
        has_institutionalization = any(w in lower_text for w in ["institucionalización", "institucionalizacion", "definición", "definicion", "propiedad formal", "teorema"])

        if has_topaze:
            brousseau_score = 1.0
            feedback.append("ALERTA CRÍTICA (Brousseau): Detectado Efecto Topaze (el enunciado adelanta la solución o reduce la incertidumbre).")
            required_actions.append("Reescribir el ítem como una situación abierta de conjeturación o toma de decisiones.")
        elif has_action and has_formulation and has_institutionalization:
            brousseau_score = 4.0
            feedback.append("Brousseau Óptimo: Se articulan claramente las fases a-didácticas y la institucionalización.")
        elif has_action and (has_formulation or has_institutionalization):
            brousseau_score = 3.0
            feedback.append("Brousseau Favorable: Plantea situación desafiante con fase de formulación adecuada.")
        else:
            brousseau_score = 2.5
            feedback.append("Brousseau Aceptable: Actividad formal estándar.")

        # 2. Duval: Registros Semióticos
        registers = []
        if any(k in lower_text for k in ["tikz", "gráfico", "grafico", "plano cartesiano", "dibuja", "figura", "geometría", "triángulo", "círculo"]):
            registers.append("Gráfico/Geométrico")
        if any(k in lower_text for k in ["tabla", "tabular", "valores de x", "filas y columnas"]):
            registers.append("Tabular")
        if any(k in lower_text for k in ["contexto", "problema", "situación", "metros", "velocidad", "granjero", "costo", "estudiantes"]):
            registers.append("Verbal/Factual")
        if any(k in lower_text for k in ["x^2", "x**2", "f(x)", "ecuación", "ecuacion", "álgebra", "algebra", "$"]):
            registers.append("Algebraico/Simbólico")

        if len(registers) >= 3:
            duval_score = 4.0
            feedback.append(f"Duval Sobresaliente: Articulación activa de {len(registers)} registros ({', '.join(registers)}).")
        elif len(registers) >= 2:
            duval_score = 3.0
            feedback.append(f"Duval Adecuado: Presencia de 2 registros ({', '.join(registers)}).")
        else:
            duval_score = 2.0
            feedback.append("Duval Advertencia: Predominio de un único registro. Requiere apoyo visual o tabular.")
            required_actions.append("Incorporar al menos un registro secundario (gráfico o tabla de valores).")

        # 3. Demanda Cognitiva (Bloom / Anderson-Krathwohl)
        high_verbs = ["justifica", "conjetura", "demuestra", "generaliza", "analiza", "optimiza", "compara", "evalúa"]
        mid_verbs = ["aplica", "calcula en contexto", "determina", "resuelve"]
        has_high = any(v in lower_text for v in high_verbs)
        has_mid = any(v in lower_text for v in mid_verbs)

        if has_high:
            bloom_score = 4.0
            feedback.append("Bloom Alto: Presencia de demandas reflexivas y de justificación formal.")
        elif has_mid:
            bloom_score = 3.0
            feedback.append("Bloom Medio: Predominio de aplicación procedimental en contexto.")
        else:
            bloom_score = 2.0
            feedback.append("Bloom Bajo: Tareas mayormente algorítmicas.")

        # 4. Calidad de Evaluación y Distractores
        has_misconceptions = any(w in lower_text for w in ["misconception_ref", "error cognitivo", "ilusión de linealidad", "confusión", "distractor"])
        if has_misconceptions:
            eval_score = 4.0
            feedback.append("Evaluación Auténtica: Distractores formalmente fundados en concepciones alternativas.")
        else:
            eval_score = 3.0
            feedback.append("Evaluación Estándar: Ítems estructurados.")

        weighted = round(
            brousseau_score * 0.30 +
            duval_score * 0.25 +
            bloom_score * 0.25 +
            eval_score * 0.20,
            2
        )

        passed = (weighted >= 3.0) and (brousseau_score >= 2.5)

        return {
            "status": "APPROVED" if passed else "REJECTED",
            "weighted_score": weighted,
            "scores": {
                "brousseau_devolution": brousseau_score,
                "duval_multiregister": duval_score,
                "bloom_cognitive_demand": bloom_score,
                "assessment_quality": eval_score
            },
            "registers_detected": registers,
            "feedback": feedback,
            "required_actions": required_actions,
            "passed": passed
        }
