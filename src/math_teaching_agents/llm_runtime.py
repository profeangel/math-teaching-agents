"""
Runtime de Ejecución y Conexión de Agentes LLM.
Orquesta los roles docentes (MTSK, GPK, Evaluador) con proveedores de LLM
(Gemini, OpenAI, Claude, Ollama y Mock Determinista) bajo la arquitectura Zero-Trust.
Incluye Bucle Autónomo de Autocorrección (Self-Healing Loop), orquestación multi-etapa
y generación dual: Instrumentos de Evaluación (assessment-spec.json) y Unidades Didácticas (didactic-unit.json).
"""

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Callable
import urllib.request
import urllib.error
import yaml

from math_teaching_agents.validators.schema_validator import SchemaValidator
from math_teaching_agents.validators.math_verifier import SymbolicMathVerifier
from math_teaching_agents.engines.latex_engine import LatexEngine
from math_teaching_agents.engines.typst_engine import TypstEngine
from math_teaching_agents.engines.moodle_engine import MoodleEngine
from math_teaching_agents.profile import load_profile, inject_profile_into_prompt


@dataclass
class AgentSpec:
    id: str
    name: str
    file_path: Path
    mission: str
    system_prompt: str


class AgentLoader:
    """Carga y parsea especificaciones de agentes desde archivos Markdown en agents/."""

    def __init__(self, root_dir: Optional[Path] = None):
        if root_dir:
            self.root_dir = Path(root_dir)
        else:
            self.root_dir = Path(__file__).resolve().parents[2]
        self.agents_dir = self.root_dir / "agents"

    def list_agents(self) -> List[str]:
        if not self.agents_dir.exists():
            return []
        return [f.stem for f in self.agents_dir.rglob("*.md")]

    def load_agent(self, name_or_id: str) -> Optional[AgentSpec]:
        """Localiza un agente por nombre de archivo o id y extrae sus metadatos."""
        for md_file in self.agents_dir.rglob("*.md"):
            if md_file.stem == name_or_id:
                return self._parse_file(md_file)
        # Búsqueda secundaria si no coincide el stem
        for md_file in self.agents_dir.rglob("*.md"):
            if name_or_id.lower() in md_file.name.lower():
                return self._parse_file(md_file)
        return None

    def _parse_file(self, path: Path) -> AgentSpec:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extraer nombre / ID del título
        first_line = content.splitlines()[0] if content else ""
        agent_id = path.stem
        agent_name = first_line.replace("# Agente:", "").strip()

        # Extraer Misión
        mission_match = re.search(r"## 1\. Misi[oó]n.*?\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
        mission = mission_match.group(1).strip() if mission_match else ""

        # Extraer System Prompt
        prompt_match = re.search(r"## 4\. System Prompt Oficial.*?\n```markdown\n(.*?)\n```", content, re.DOTALL)
        if prompt_match:
            system_prompt = prompt_match.group(1).strip()
        else:
            # Fallback a búsqueda de cualquier bloque de código markdown
            alt_match = re.search(r"```markdown\n(.*?)\n```", content, re.DOTALL)
            system_prompt = alt_match.group(1).strip() if alt_match else mission

        return AgentSpec(
            id=agent_id,
            name=agent_name,
            file_path=path,
            mission=mission,
            system_prompt=system_prompt
        )


class LLMProvider:
    """Clase base abstracta para proveedores de modelos de lenguaje."""

    def generate(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        raise NotImplementedError


class MockLLMProvider(LLMProvider):
    """Proveedor determinista fuera de línea para pruebas unitarias, CI/CD y prototipado rápido."""

    def __init__(self, canned_response: Optional[str] = None, responses_sequence: Optional[List[str]] = None):
        self.canned_response = canned_response
        self.responses_sequence = list(responses_sequence) if responses_sequence else []
        self.call_history: List[Dict[str, str]] = []

    def generate(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        self.call_history.append({"system_prompt": system_prompt, "user_prompt": user_prompt})

        # Si hay una secuencia de respuestas encoladas, despachar la siguiente
        if self.responses_sequence:
            return self.responses_sequence.pop(0)

        if self.canned_response:
            return self.canned_response

        # Si el prompt solicita una unidad didáctica, despachar borrador canónico de unidad
        if "didactic-unit.json" in user_prompt or "Unidad Didáctica" in user_prompt or "PLANIFICACIÓN DE UNIDAD" in user_prompt:
            return self._canonical_didactic_unit_yaml()

        # Si es una llamada con feedback correctivo de Gate 1 y no hay respuesta encolada,
        # autogenerar la corrección determinista
        if "GATE 1" in user_prompt and "RECHAZADO" in user_prompt:
            return self._canonical_draft_yaml()

        return self._canonical_draft_yaml()

    def _canonical_draft_yaml(self) -> str:
        """Borrador canónico válido acorde a assessment-spec.json."""
        draft_dict = {
            "metadata": {
                "title": "Evaluación Formativa: Ecuaciones Cuadráticas y Álgebra",
                "assessment_type": "FORMATIVA",
                "modality": "INDIVIDUAL",
                "target_grade": "2° Medio / Fase 6",
                "curriculum_code": "chile-mineduc",
                "total_points": 10,
                "passing_threshold_percentage": 60,
                "estimated_duration_minutes": 45
            },
            "specification_table": {
                "cognitive_process_distribution": {
                    "comprender": 40.0,
                    "aplicar": 60.0
                },
                "knowledge_type_distribution": {
                    "conceptual": 40.0,
                    "procedural": 60.0
                }
            },
            "items": [
                {
                    "item_id": 1,
                    "format": "MULTIPLE_CHOICE",
                    "bloom_anderson_level": "APLICAR_PROCEDURAL",
                    "mtsk_subdomain": "KoT",
                    "points": 4,
                    "stem": "Determine el conjunto solución en $\\mathbb{R}$ de la ecuación cuadrática $x^2 - 5x + 6 = 0$.",
                    "options": [
                        {
                            "key": "A",
                            "text": "$\\{2, 3\\}$",
                            "is_correct": True,
                            "feedback_clue": "Correcto: factorizando como $(x-2)(x-3)=0$."
                        },
                        {
                            "key": "B",
                            "text": "$\\{-2, -3\\}$",
                            "is_correct": False,
                            "misconception_ref": "Error de cambio de signos al despejar raíces",
                            "feedback_clue": "Revisa los signos al igualar los factores a cero."
                        },
                        {
                            "key": "C",
                            "text": "$\\{1, 6\\}$",
                            "is_correct": False,
                            "misconception_ref": "Búsqueda de factores que multipliquen 6 sin verificar la suma -5",
                            "feedback_clue": "Recuerda que la suma de las raíces debe ser 5."
                        },
                        {
                            "key": "D",
                            "text": "$\\{-1, -6\\}$",
                            "is_correct": False,
                            "misconception_ref": "Confusión en los signos de la regla de Vieta",
                            "feedback_clue": "Comprueba sustituyendo los valores en la ecuación original."
                        }
                    ]
                },
                {
                    "item_id": 2,
                    "format": "OPEN_DEVELOPMENT",
                    "bloom_anderson_level": "ANALIZAR_CONCEPTUAL",
                    "mtsk_subdomain": "KPM",
                    "points": 6,
                    "stem": "Demuestre algebraicamente por el método de completación de cuadrados que la ecuación $x^2 + 6x + 5 = 0$ tiene por soluciones $x = -1$ y $x = -5$.",
                    "rubric": {
                        "criterion_name": "Rigor en Completación de Cuadrados",
                        "levels": {
                            "avanzado": "Agrupa términos, suma 9 en ambos miembros reconociendo el trinomio cuadrado perfecto $(x+3)^2=4$ y deduce correctamente ambas raíces.",
                            "competente": "Realiza la completación de cuadrados pero comete imprecisiones menores de notación formal.",
                            "en_desarrollo": "Aplica la fórmula cuadrática general en lugar de la técnica solicitada de completación.",
                            "inicial": "No logra transformar la ecuación o confunde conceptos algebraicos de base."
                        }
                    }
                }
            ]
        }
        return yaml.dump(draft_dict, sort_keys=False, allow_unicode=True)

    def _canonical_didactic_unit_yaml(self) -> str:
        """Borrador canónico de unidad didáctica conforme a schemas/didactic-unit.json."""
        unit_dict = {
            "metadata": {
                "unit_title": "Modelización y Raíces de Funciones Cuadráticas",
                "target_grade": "2° Medio / Grado 10",
                "topic": "Ecuaciones Cuadráticas y Parábolas en Contextos de Lanzamiento de Proyectiles",
                "estimated_sessions": 4,
                "minutes_per_session": 90,
                "curriculum_expectation_ref": "Bases Curriculares Mineduc - OA 04 / SEP NEM Fase 6"
            },
            "theoretical_alignment": {
                "active_frameworks": ["brousseau-tds", "duval-trrs"],
                "networking_justification": (
                    "Articulación entre la Teoría de Situaciones Didácticas (Brousseau) para la gestión del medio a-didáctico "
                    "y los Registros de Representación Semiótica (Duval) para la conversión entre registro gráfico, algebraico y tabular."
                )
            },
            "epistemological_diagnostics": {
                "target_misconceptions": [
                    {
                        "code": "CONFUSION_VERTICE_CON_RAIZ",
                        "description": "El estudiante asume que el tiempo en que el proyectil toca el suelo coincide con la altura máxima.",
                        "confrontation_strategy": "Contrastar con simulador GeoGebra la simetría de la parábola respecto al eje vertical del vértice."
                    },
                    {
                        "code": "SIGNO_MENOS_CUADRATICO",
                        "description": "Al evaluar $-5t^2$ para $t=2$, calcula $(-5 \\cdot 2)^2 = 100$ en lugar de $-5 \\cdot 4 = -20$.",
                        "confrontation_strategy": "Uso de paréntesis explícitos y discusión de la jerarquía de operaciones de potencias frente al producto."
                    }
                ],
                "prerequisites_required": [
                    "Resolución de ecuaciones de primer grado",
                    "Concepto de función y evaluación de imágenes numéricas",
                    "Teorema de Pitágoras y plano cartesiano"
                ]
            },
            "phases": [
                {
                    "phase_id": 1,
                    "phase_name": "Situación de Acción: Lanzamiento Experimental e Indagación",
                    "cognitive_demand": "HACIENDO_MATEMATICA",
                    "example_choice_rationale": "Se escoge la función $h(t) = -5t^2 + 20t$ porque sus raíces ($0$ y $4$) y vértice ($t=2, h=20$) son enteros fácilmente manipulables.",
                    "teacher_role": "Presenta el problema del proyectil sin enunciar fórmulas de vértice ni factorización. Devuelve las preguntas al medio experimental.",
                    "student_activity": "En parejas, tabulan tiempos y alturas buscando deducir cuándo el objeto deja de subir y cuándo impacta el suelo.",
                    "udl_guidelines": {
                        "representation": "Gráfica interactiva animada y tabla numérica comparativa.",
                        "action_expression": "Construcción libre de tablas, bosquejos o diagramas de dispersión.",
                        "engagement": "Desafío gamificado de predicción del tiempo de vuelo."
                    },
                    "dynamic_artifact_ref": "geogebra-projectile-motion-applet"
                },
                {
                    "phase_id": 2,
                    "phase_name": "Situación de Formulación y Validación: Conjetura de Simetría",
                    "cognitive_demand": "PROCEDIMIENTOS_CON_CONEXIONES",
                    "example_choice_rationale": "Comparación entre $t=1$ ($h=15$) y $t=3$ ($h=15$) para evidenciar la simetría axial respecto a $t=2$.",
                    "teacher_role": "Media el debate plenario sin validar directamente; solicita a los grupos defender por qué las alturas son idénticas a distancias iguales del vértice.",
                    "student_activity": "Los equipos formulan la conjetura de que el punto máximo ocurre exactamente en el punto medio entre el despegue y el impacto.",
                    "udl_guidelines": {
                        "representation": "Trazado del eje de simetría sobre la parábola.",
                        "action_expression": "Debate guiado y registro en pizarra compartida.",
                        "engagement": "Colaboración estructurada con roles rotativos."
                    }
                },
                {
                    "phase_id": 3,
                    "phase_name": "Institucionalización y Formalización Deductiva",
                    "cognitive_demand": "PROCEDIMIENTOS_CON_CONEXIONES",
                    "example_choice_rationale": "Generalización a $f(x) = ax^2 + bx + c$ deduciendo la abscisa del vértice $x_v = -b/(2a)$.",
                    "teacher_role": "Formaliza el estatus del saber matemático institucional, conecta la conjetura de los estudiantes con la completación de cuadrados.",
                    "student_activity": "Registran la síntesis conceptual y aplican la relación formal a nuevos casos paramétricos.",
                    "udl_guidelines": {
                        "representation": "Mapa conceptual síntesis que vincula registro gráfico, analítico y canónico.",
                        "action_expression": "Bitácora reflexiva de aprendizaje y formulario de síntesis.",
                        "engagement": "Autoevaluación de metacognición con rúbrica Förster."
                    }
                }
            ]
        }
        return yaml.dump(unit_dict, sort_keys=False, allow_unicode=True)


class HTTPLLMProvider(LLMProvider):
    """Conector universal HTTP para APIs de modelos (Gemini, OpenAI, Claude, Ollama)."""

    def __init__(self, provider_type: str = "ollama", api_key: Optional[str] = None, model: Optional[str] = None):
        self.provider_type = provider_type.lower()
        self.api_key = api_key or os.environ.get(f"{provider_type.upper()}_API_KEY", "")
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        if self.provider_type == "ollama":
            return self._call_ollama(system_prompt, user_prompt)
        elif self.provider_type in ("openai", "gemini", "anthropic"):
            return self._call_cloud_api(system_prompt, user_prompt)
        else:
            raise ValueError(f"Proveedor no soportado: {self.provider_type}")

    def _call_ollama(self, system_prompt: str, user_prompt: str) -> str:
        model = self.model or "llama3"
        url = "http://localhost:11434/api/chat"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("message", {}).get("content", "")
        except Exception as e:
            raise RuntimeError(f"Error conectando a Ollama ({url}): {e}")

    def _call_cloud_api(self, system_prompt: str, user_prompt: str) -> str:
        if not self.api_key:
            raise ValueError(f"API key requerida para el proveedor {self.provider_type}")
        raise NotImplementedError(f"Conexión directa {self.provider_type} requiere configuración de endpoint")


def get_provider(name: Optional[str] = None, **kwargs) -> LLMProvider:
    """Fábrica de proveedores de LLM."""
    if not name or name == "mock":
        return MockLLMProvider(**kwargs)
    return HTTPLLMProvider(provider_type=name, **kwargs)


class DidacticPipeline:
    """Orquestador integral del ciclo didáctico multiagente bajo Zero-Trust."""

    def __init__(self, root_dir: Optional[Path] = None, provider: Optional[LLMProvider] = None):
        if root_dir:
            self.root_dir = Path(root_dir)
        else:
            self.root_dir = Path(__file__).resolve().parents[2]

        self.loader = AgentLoader(self.root_dir)
        self.validator = SchemaValidator(self.root_dir)
        self.math_verifier = SymbolicMathVerifier()
        self.provider = provider or MockLLMProvider()

    def _evaluate_gate1(self, draft_data: Dict[str, Any], schema_name: str = "assessment-spec.json") -> Dict[str, Any]:
        """Ejecuta la auditoría semántica y simbólica CAS en el borrador."""
        gate1_report = {
            "gate": 1,
            "status": "APPROVED",
            "schema_check": {"status": "PASS", "errors": []},
            "math_symbolic_check": {"status": "PASS", "details": []}
        }

        # 1. Validar Schema contra el contrato correspondiente
        schema_ok, schema_errors = self.validator.validate_instance(draft_data, schema_name)
        if not schema_ok:
            gate1_report["status"] = "REJECTED"
            gate1_report["schema_check"]["status"] = "FAIL"
            gate1_report["schema_check"]["errors"] = schema_errors

        # 2. Si es una evaluación, validar matemáticamente con SymPy CAS e invariantes
        items = draft_data.get("items", [])
        for item in items:
            v_res = self.math_verifier.verify_item(item)
            gate1_report["math_symbolic_check"]["details"].append(v_res)
            if v_res.get("status") != "PASS":
                gate1_report["status"] = "REJECTED"
                gate1_report["math_symbolic_check"]["status"] = "FAIL"

        return gate1_report

    def _extract_gate1_feedback(self, gate1_report: Dict[str, Any]) -> List[str]:
        """Extrae viñetas de retroalimentación estructurada a partir del reporte de rechazo."""
        notes = []
        if gate1_report.get("schema_check", {}).get("status") != "PASS":
            for err in gate1_report["schema_check"].get("errors", []):
                notes.append(f"- [Inconsistencia de Schema]: {err}")
        if gate1_report.get("math_symbolic_check", {}).get("status") != "PASS":
            for det in gate1_report["math_symbolic_check"].get("details", []):
                if det.get("status") != "PASS":
                    for dup in det.get("duplicates", []):
                        notes.append(f"- [Fallo Matemático SymPy]: {dup}")
                    if det.get("error_detail"):
                        notes.append(f"- [Fallo Matemático SymPy]: {det['error_detail']}")
        return notes

    def run(
        self,
        topic: str,
        curriculum_id: str = "chile-mineduc",
        framework_id: str = "duval-trrs",
        output_format: str = "latex",
        output_dir: Optional[Path] = None,
        compile_pdf: bool = False,
        max_retries: int = 3,
        multi_stage: bool = False,
        artifact_type: str = "assessment",
        profile: Optional[Dict[str, Any]] = None,
        tone: Optional[str] = None,
        interactive_review: bool = False,
        review_callback: Optional[Callable[[Dict[str, Any], Path], Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta el ciclo de vida didáctico completo con Self-Healing Loop,
        soporte multi-etapa y selección de artefacto (assessment vs didactic_unit).
        """
        out_dir = Path(output_dir) if output_dir else self.root_dir / "output"
        out_dir.mkdir(parents=True, exist_ok=True)

        is_didactic_unit = (artifact_type in ("didactic_unit", "didactic-unit", "unit"))
        target_schema = "didactic-unit.json" if is_didactic_unit else "assessment-spec.json"

        # Cargar perfil docente y modular tono
        active_profile = profile if profile is not None else load_profile(self.root_dir)
        if active_profile and tone:
            active_profile = dict(active_profile)
            active_profile["interaction_mode"] = dict(active_profile.get("interaction_mode", {}))
            active_profile["interaction_mode"]["tone"] = tone

        # 1. Cargar Agentes Especialistas
        orchestrator = self.loader.load_agent("orchestrator")
        evaluator = self.loader.load_agent("evaluator")
        mtsk_kot = self.loader.load_agent("mtsk-kot")
        mtsk_kflm = self.loader.load_agent("mtsk-kflm")
        gpk_assessment = self.loader.load_agent("gpk-assessment")
        gpk_learning = self.loader.load_agent("gpk-learning")

        # 2. Orquestación Multi-Etapa o Unificada según tipo de artefacto
        if is_didactic_unit:
            # UNIDAD DIDÁCTICA / SECUENCIA DE CLASE
            if multi_stage:
                stage1_agent = mtsk_kflm or orchestrator
                stage1_sys = stage1_agent.system_prompt if stage1_agent else "Especialista en didáctica y epistemología."
                stage1_sys = inject_profile_into_prompt(active_profile, stage1_sys)
                stage1_prompt = (
                    f"FASE 1: Análisis Epistemológico y Diagnóstico de Obstáculos para Unidad Didáctica.\n"
                    f"Tema: '{topic}'. Currículo: {curriculum_id}. Marco: {framework_id}.\n"
                    f"Determina: 1) Prerrequisitos cognitivos indispensables, 2) Concepciones erróneas típicas (KFLM) con "
                    f"estrategias de confrontación, 3) Justificación de articulación teórica (Networking)."
                )
                stage1_output = self.provider.generate(system_prompt=stage1_sys, user_prompt=stage1_prompt)

                stage2_agent = gpk_learning or orchestrator
                sys_prompt = stage2_agent.system_prompt if stage2_agent else "Diseñador de secuencias de clase y situaciones a-didácticas."
                sys_prompt = inject_profile_into_prompt(active_profile, sys_prompt)
                base_prompt = (
                    f"FASE 2: Planificación de Unidad Didáctica e Ingeniería de Situaciones Matemáticas.\n"
                    f"Tema: '{topic}'. Currículo: {curriculum_id}. Marco: {framework_id}.\n"
                    f"Insumos de la Fase 1:\n{stage1_output}\n\n"
                    f"Estructura la unidad estrictamente en YAML conforme a 'schemas/didactic-unit.json'. "
                    f"Asegura fases completas de Brousseau (Acción, Formulación, Validación, Institucionalización), "
                    f"demanda cognitiva de Stein & Smith, rol docente, actividad del estudiante y pautas DUA."
                )
            else:
                unit_agent = gpk_learning or orchestrator
                sys_prompt = unit_agent.system_prompt if unit_agent else "Diseñador de unidades didácticas."
                sys_prompt = inject_profile_into_prompt(active_profile, sys_prompt)
                base_prompt = (
                    f"Diseña una Unidad Didáctica y Secuencia de Aprendizaje sobre el tema: '{topic}'.\n"
                    f"Marco curricular: {curriculum_id}.\n"
                    f"Marco didáctico de referencia: {framework_id}.\n"
                    f"Estructura la respuesta estrictamente en YAML o JSON conforme a 'schemas/didactic-unit.json'."
                )
        else:
            # INSTRUMENTO DE EVALUACIÓN
            if multi_stage:
                stage1_agent = mtsk_kflm or mtsk_kot or orchestrator
                stage1_sys = stage1_agent.system_prompt if stage1_agent else "Eres un especialista en didáctica de la matemática."
                stage1_sys = inject_profile_into_prompt(active_profile, stage1_sys)
                stage1_prompt = (
                    f"FASE 1: Análisis Didáctico y Epistemológico Preliminar.\n"
                    f"Tema: '{topic}'.\n"
                    f"Currículo: {curriculum_id} | Marco: {framework_id}.\n"
                    f"Establece: 1) Matriz de demanda cognitiva Anderson-Krathwohl, "
                    f"2) Prerrequisitos y conexiones (KSM), y 3) Concepciones erróneas típicas (KFLM)."
                )
                stage1_output = self.provider.generate(system_prompt=stage1_sys, user_prompt=stage1_prompt)

                stage2_agent = gpk_assessment or orchestrator
                sys_prompt = stage2_agent.system_prompt if stage2_agent else "Eres un diseñador de evaluaciones matemáticas formativas."
                sys_prompt = inject_profile_into_prompt(active_profile, sys_prompt)
                base_prompt = (
                    f"FASE 2: Construcción de Instrumento de Evaluación.\n"
                    f"Tema: '{topic}'. Currículo: {curriculum_id}. Marco: {framework_id}.\n"
                    f"Insumos de la Fase 1:\n{stage1_output}\n\n"
                    f"Estructura el instrumento estrictamente en YAML o JSON conforme a 'schemas/assessment-spec.json'. "
                    f"Asegura que los distractores de opción múltiple sean matemáticamente únicos y diagnostiquen concepciones erróneas."
                )
            else:
                sys_prompt = orchestrator.system_prompt if orchestrator else "Eres un diseñador de evaluaciones matemáticas."
                if mtsk_kot:
                    sys_prompt += "\n" + mtsk_kot.system_prompt
                sys_prompt = inject_profile_into_prompt(active_profile, sys_prompt)
                base_prompt = (
                    f"Diseña un borrador de evaluación matemática sobre el tema: '{topic}'.\n"
                    f"Marco curricular: {curriculum_id}.\n"
                    f"Marco didáctico de referencia: {framework_id}.\n"
                    f"Estructura la respuesta estrictamente en YAML o JSON conforme a 'schemas/assessment-spec.json'."
                )

        # 3. Bucle Autónomo de Autocorrección (Self-Healing Loop)
        attempt = 1
        history_repairs = []
        draft_data = None
        raw_draft = ""
        gate1_report = None
        current_user_prompt = base_prompt

        while attempt <= max_retries:
            raw_draft = self.provider.generate(system_prompt=sys_prompt, user_prompt=current_user_prompt)

            # Parsear borrador YAML o JSON
            try:
                clean_draft = re.sub(r"^```(?:yaml|json)?\n", "", raw_draft.strip(), flags=re.MULTILINE)
                clean_draft = re.sub(r"\n```$", "", clean_draft, flags=re.MULTILINE)
                draft_data = yaml.safe_load(clean_draft)
            except Exception as e:
                history_repairs.append({"attempt": attempt, "error": f"Error parseando borrador: {e}"})
                attempt += 1
                current_user_prompt = (
                    f"El intento previo falló al parsear YAML/JSON: {e}.\n"
                    f"Por favor devuelve ÚNICAMENTE un bloque YAML o JSON válido sin texto introductorio ni decoraciones."
                )
                continue

            # Evaluar Gate 1 contra el esquema destino
            gate1_report = self._evaluate_gate1(draft_data, schema_name=target_schema)
            gate1_report["attempt"] = attempt

            if gate1_report["status"] == "APPROVED":
                gate1_report["attempts_needed"] = attempt
                gate1_report["history_repairs"] = history_repairs
                break

            # Si Gate 1 rechazó, extraer retroalimentación y construir prompt correctivo
            feedback_notes = self._extract_gate1_feedback(gate1_report)
            history_repairs.append({
                "attempt": attempt,
                "notes": feedback_notes,
                "draft_snippet": raw_draft[:200]
            })

            err_bullet_points = "\n".join(feedback_notes)
            current_user_prompt = (
                f"GATE 1 (Zero-Trust Quality Gatekeeper) ha RECHAZADO tu borrador en el intento {attempt}/{max_retries}.\n"
                f"Observaciones y fallos formales detectados contra '{target_schema}':\n{err_bullet_points}\n\n"
                f"Borrador observado:\n```yaml\n{raw_draft}\n```\n\n"
                f"INSTRUCCIÓN DE AUTORREPARACIÓN: Corrige estrictamente estos fallos conforme a '{target_schema}'."
            )
            attempt += 1

        # Si se agotaron los reintentos sin aprobación
        if not draft_data or (gate1_report and gate1_report["status"] == "REJECTED"):
            final_report = gate1_report or {
                "gate": 1,
                "status": "REJECTED",
                "error": "No se pudo obtener un borrador válido tras agotar intentos de autorreparación."
            }
            final_report["total_attempts_exhausted"] = attempt - 1
            final_report["history_repairs"] = history_repairs

            gate1_path = out_dir / "gate1_verdict.json"
            with open(gate1_path, "w", encoding="utf-8") as f:
                json.dump(final_report, f, indent=2, ensure_ascii=False)

            return {
                "status": "REJECTED_BY_EVALUATOR",
                "gate_1": final_report,
                "attempts_exhausted": attempt - 1,
                "raw_draft": raw_draft,
                "artifact_type": artifact_type
            }

        # Guardar borrador semántico aprobado
        draft_filename = "didactic-unit-draft.yaml" if is_didactic_unit else "assessment-draft.yaml"
        draft_path = out_dir / draft_filename
        with open(draft_path, "w", encoding="utf-8") as f:
            yaml.dump(draft_data, f, sort_keys=False, allow_unicode=True)

        gate1_path = out_dir / "gate1_verdict.json"
        with open(gate1_path, "w", encoding="utf-8") as f:
            json.dump(gate1_report, f, indent=2, ensure_ascii=False)

        # Punto de Control Humano (Human-in-the-Loop Checkpoint)
        if interactive_review or review_callback:
            if review_callback:
                review_result = review_callback(draft_data, draft_path)
            else:
                from math_teaching_agents.human_review import execute_human_review
                review_result = execute_human_review(
                    draft_data=draft_data,
                    draft_path=draft_path,
                    artifact_type=artifact_type
                )

            if review_result.get("status") == "CANCELLED":
                return {
                    "status": "CANCELLED_BY_USER",
                    "gate_1": gate1_report,
                    "draft_path": str(draft_path),
                    "message": "Flujo cancelado por el docente en el Punto de Control Humano."
                }

            if review_result.get("modified"):
                draft_data = review_result.get("draft_data", draft_data)
                # Re-validar Gate 1 bajo principio Zero-Trust para garantizar que la edición humana cumple contratos
                recheck_gate1 = self._evaluate_gate1(draft_data, schema_name=target_schema)
                if recheck_gate1["status"] != "APPROVED":
                    feedback = self._extract_gate1_feedback(recheck_gate1)
                    return {
                        "status": "REJECTED_AFTER_HUMAN_REVIEW",
                        "gate_1": recheck_gate1,
                        "draft_path": str(draft_path),
                        "feedback": feedback,
                        "message": "Las modificaciones introducidas por el docente no superaron la auditoría de Gate 1."
                    }
                gate1_report = recheck_gate1
                # Actualizar archivo YAML y veredicto con datos validados
                with open(draft_path, "w", encoding="utf-8") as f:
                    yaml.dump(draft_data, f, sort_keys=False, allow_unicode=True)
                with open(gate1_path, "w", encoding="utf-8") as f:
                    json.dump(gate1_report, f, indent=2, ensure_ascii=False)

        # 4. Fase 4: Renderizado de Formato
        rendered_path = None
        compile_result = None
        fmt = output_format.lower()
        file_prefix = "didactic-unit-rendered" if is_didactic_unit else "assessment-rendered"

        if fmt == "typst":
            typst_engine = TypstEngine()
            rendered_code = typst_engine.render_document(draft_data)
            rendered_path = out_dir / f"{file_prefix}.typ"
            with open(rendered_path, "w", encoding="utf-8") as f:
                f.write(rendered_code)
            if compile_pdf:
                compile_result = typst_engine.compile_pdf(rendered_path)
            else:
                compile_result = {"status": "SKIPPED", "message": "Compilación a PDF no solicitada."}
        elif fmt == "moodle" and not is_didactic_unit:
            moodle_engine = MoodleEngine()
            rendered_code = moodle_engine.render_document(draft_data)
            rendered_path = out_dir / f"{file_prefix}.xml"
            with open(rendered_path, "w", encoding="utf-8") as f:
                f.write(rendered_code)
            compile_result = {"status": "SUCCESS", "message": "Archivo Moodle XML generado para importación en LMS."}
        else:
            latex_engine = LatexEngine()
            rendered_code = latex_engine.render_document(draft_data)
            rendered_path = out_dir / f"{file_prefix}.tex"
            with open(rendered_path, "w", encoding="utf-8") as f:
                f.write(rendered_code)
            if compile_pdf:
                compile_result = latex_engine.compile_pdf(rendered_path)
            else:
                compile_result = {"status": "SKIPPED", "message": "Compilación a PDF no solicitada."}

        # 5. GATE 2: Auditoría Técnica Post-Render
        gate2_report = {
            "gate": 2,
            "status": "APPROVED" if rendered_path.exists() else "REJECTED",
            "format": output_format,
            "rendered_file": str(rendered_path),
            "compile_result": compile_result
        }
        gate2_path = out_dir / "gate2_verdict.json"
        with open(gate2_path, "w", encoding="utf-8") as f:
            json.dump(gate2_report, f, indent=2, ensure_ascii=False)

        return {
            "status": "COMPLETED",
            "gate_1": gate1_report,
            "gate_2": gate2_report,
            "draft_path": str(draft_path),
            "rendered_path": str(rendered_path),
            "output_format": output_format,
            "attempts_needed": gate1_report.get("attempts_needed", 1),
            "multi_stage": multi_stage,
            "artifact_type": artifact_type,
            "profile_applied": active_profile
        }
