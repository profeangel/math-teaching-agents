"""
Módulo de Gestión de Perfil Docente y Configuración Inicial (Onboarding).
Permite configurar el nivel educativo, currículo base, tono pedagógico y preferencias
del docente para que los agentes en harnesses o CLI adapten su lenguaje y asistencia.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import yaml


PROFILE_FILE_NAME = ".math-agent.yaml"

TONE_DESCRIPTIONS = {
    "pragmatic": (
        "Práctico y Directo: Lenguaje cotidiano de aula, sin jerga teórica innecesaria. "
        "Aplica el rigor de MTSK y Brousseau 'silenciosamente' bajo el capó."
    ),
    "mentoring": (
        "Formativo / Mentoría: Estilo colaborativo y formativo. Sugiere estrategias pedagógicas "
        "y de gestión de aula con empatía y cercanía."
    ),
    "academic": (
        "Investigación / Didáctica Formal: Emplea el aparato conceptual completo de la investigación "
        "en educación matemática (MTSK, EOS, Duval, Brousseau, taxonomías formales)."
    ),
}

DEFAULT_PROFILE: Dict[str, Any] = {
    "version": "1.1",
    "educator": {
        "name": "Docente",
        "school": "Liceo / Colegio",
        "level": "secondary",
        "curriculum_default": "chile-mineduc",
        "framework_default": "brousseau-tsd",
    },
    "interaction_mode": {
        "tone": "pragmatic",
        "collaboration": "co-design",
    },
    "tooling_preferences": {
        "output_format": "typst",
        "auto_compile": True,
        "cas_strictness": "high",
    },
}


def get_profile_path(root_dir: Optional[Path] = None) -> Path:
    """
    Retorna la ruta del archivo de configuración.
    Prioridad:
    1. Archivo `.math-agent.yaml` en `root_dir` (si se especifica).
    2. Archivo `.math-agent.yaml` en el directorio de trabajo actual.
    3. Fallback a directorio de usuario `~/.config/math-agent/profile.yaml`.
    """
    if root_dir:
        candidate = Path(root_dir) / PROFILE_FILE_NAME
        if candidate.exists():
            return candidate

    cwd_candidate = Path.cwd() / PROFILE_FILE_NAME
    if cwd_candidate.exists():
        return cwd_candidate

    home_dir = Path.home() / ".config" / "math-agent"
    return home_dir / "profile.yaml"


def load_profile(root_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Carga el perfil docente si existe, o retorna None si no se ha configurado."""
    paths_to_check = []
    if root_dir:
        paths_to_check.append(Path(root_dir) / PROFILE_FILE_NAME)
    paths_to_check.append(Path.cwd() / PROFILE_FILE_NAME)
    paths_to_check.append(Path.home() / ".config" / "math-agent" / "profile.yaml")

    for p in paths_to_check:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if isinstance(data, dict):
                        return data
            except Exception:
                pass
    return None


def save_profile(data: Dict[str, Any], path: Optional[Path] = None, root_dir: Optional[Path] = None) -> Path:
    """Guarda los datos del perfil en formato YAML."""
    target_path = path or (Path(root_dir or Path.cwd()) / PROFILE_FILE_NAME)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)
    return target_path


def inject_profile_into_prompt(profile: Optional[Dict[str, Any]], system_prompt: str) -> str:
    """
    Inyecta la modulación de tono, nivel educativo y estilo de asistencia
    del docente en el System Prompt de cualquier agente.
    """
    if not profile:
        return system_prompt

    educator = profile.get("educator", {})
    interaction = profile.get("interaction_mode", {})
    name = educator.get("name", "Docente")
    level = educator.get("level", "secondary")
    tone = interaction.get("tone", "pragmatic")

    instructions = [f"\n\n--- PERFIL Y DIRECTRICES DE ATENCIÓN AL DOCENTE ({name.upper()}) ---"]
    instructions.append(f"- Nivel Educativo Objetivo: {level}")
    instructions.append(f"- Modo de Interacción / Tono: {tone.upper()}")

    if tone == "pragmatic":
        instructions.append(
            "- INSTRUCCIÓN MANDATORIA DE TONO (MODO PRÁCTICO): Comunícate con un lenguaje cotidiano, "
            "directo y funcional para la sala de clases. Aplica rigurosamente el modelo MTSK y los marcos "
            "didácticos de forma interna en la construcción de ítems, pero NO abrumes al docente con siglas "
            "o jerga teórica (evita 'KoT', 'KFLM', 'TSD', 'praxeología') a menos que lo solicite. Explica el "
            "sentido de los ejercicios en términos de utilidad práctica docente."
        )
    elif tone == "mentoring":
        instructions.append(
            "- INSTRUCCIÓN MANDATORIA DE TONO (MODO FORMATIVO / MENTORÍA): Actúa como un colega mentor empático. "
            "Explica brevemente el 'por qué' pedagógico de cada sugerencia y ofrece tips concretos de gestión de "
            "aula, preguntas de mediación y detección formativa de errores en un tono cercano y constructivo."
        )
    elif tone == "academic":
        instructions.append(
            "- INSTRUCCIÓN MANDATORIA DE TONO (MODO ACADÉMICO / INVESTIGACIÓN): Desarrolla el análisis con "
            "el máximo rigor epistemológico e ingeniería didáctica formal. Explicita los subdominios MTSK, "
            "las fases de Brousseau (acción, formulación, validación, institucionalización), las configuraciones "
            "ontosemióticas de Godino y la conversión de registros de Duval."
        )

    return system_prompt + "\n".join(instructions)


def run_init_wizard(
    root_dir: Optional[Path] = None,
    non_interactive: bool = False,
    answers: Optional[Dict[str, Any]] = None,
    force: bool = False
) -> Dict[str, Any]:
    """
    Ejecuta el asistente interactivo (o modo silencioso con flags)
    y genera el archivo de perfil .math-agent.yaml.
    """
    target_path = Path(root_dir or Path.cwd()) / PROFILE_FILE_NAME
    if target_path.exists() and not force:
        existing = load_profile(root_dir=root_dir)
        if existing:
            return existing

    answers = answers or {}

    if non_interactive:
        name = answers.get("name", DEFAULT_PROFILE["educator"]["name"])
        school = answers.get("school", DEFAULT_PROFILE["educator"]["school"])
        level = answers.get("level", DEFAULT_PROFILE["educator"]["level"])
        curriculum = answers.get("curriculum", DEFAULT_PROFILE["educator"]["curriculum_default"])
        framework = answers.get("framework", DEFAULT_PROFILE["educator"]["framework_default"])
        tone = answers.get("tone", DEFAULT_PROFILE["interaction_mode"]["tone"])
        output_format = answers.get("format", DEFAULT_PROFILE["tooling_preferences"]["output_format"])
    else:
        print("=" * 65)
        print("  BIENVENIDO A MATH TEACHING AGENTS: CONFIGURACIÓN INICIAL")
        print("  Personalicemos el asistente para adaptarlo a tu estilo de clase")
        print("=" * 65)

        try:
            name_input = input("1. ¿Cómo te gustaría que te llame el asistente? [Docente]: ").strip()
            name = name_input if name_input else "Docente"
        except (EOFError, KeyboardInterrupt):
            name = "Docente"

        try:
            school_input = input("2. ¿En qué colegio o institución educativa trabajas? [Liceo / Colegio]: ").strip()
            school = school_input if school_input else "Liceo / Colegio"
        except (EOFError, KeyboardInterrupt):
            school = "Liceo / Colegio"

        print("\n3. ¿En qué nivel educativo enseñas principalmente?")
        print("   [1] Primaria / Básica (primary)")
        print("   [2] Secundaria / Media (secondary)")
        print("   [3] Preuniversitario / Bachillerato (high_school)")
        print("   [4] Universidad / Superior (university)")
        try:
            lvl_in = input("   Selecciona (1-4) [2]: ").strip()
        except (EOFError, KeyboardInterrupt):
            lvl_in = "2"
        levels = {"1": "primary", "2": "secondary", "3": "high_school", "4": "university"}
        level = levels.get(lvl_in, "secondary")

        print("\n4. ¿Cuál es tu currículo base de referencia?")
        print("   [1] Chile (Mineduc - chile-mineduc)")
        print("   [2] México (NEM - mexico-nem)")
        print("   [3] Colombia (MEN - colombia-men)")
        print("   [4] España (LOMLOE - spain-lomloe)")
        print("   [5] Estándar Internacional / Bachillerato Internacional (international-standard)")
        try:
            cur_in = input("   Selecciona (1-5) [1]: ").strip()
        except (EOFError, KeyboardInterrupt):
            cur_in = "1"
        curriculums = {
            "1": "chile-mineduc",
            "2": "mexico-nem",
            "3": "colombia-men",
            "4": "spain-lomloe",
            "5": "international-standard",
        }
        curriculum = curriculums.get(cur_in, "chile-mineduc")

        print("\n5. ¿Cuál es tu marco teórico o enfoque didáctico preferido?")
        print("   [1] Teoría de Situaciones Didácticas (Brousseau - brousseau-tsd)")
        print("   [2] Enfoque Ontosemiótico (Godino, Batanero & Font - godino-eos)")
        print("   [3] Teoría APOE (Dubinsky & RUMEC - dubinsky-apoe)")
        print("   [4] Registros de Representación Semiótica (Duval - duval-trrs)")
        print("   [5] Pragmático / Abierto de Aula (sin atadura teórica fija)")
        try:
            fw_in = input("   Selecciona (1-5) [1]: ").strip()
        except (EOFError, KeyboardInterrupt):
            fw_in = "1"
        frameworks = {
            "1": "brousseau-tsd",
            "2": "godino-eos",
            "3": "dubinsky-apoe",
            "4": "duval-trrs",
            "5": "pragmatic-open",
        }
        framework = frameworks.get(fw_in, "brousseau-tsd")

        print("\n6. ¿Qué estilo de comunicación y lenguaje prefieres con los agentes?")
        print("   [1] Práctico y Directo (pragmatic): Lenguaje cotidiano de aula, sin jerga teórica.")
        print("   [2] Colaborativo/Formativo (mentoring): Sugerencias pedagógicas explicadas de forma cercana.")
        print("   [3] Académico/Didáctico (academic): Nivel formal de investigación (MTSK, Brousseau, Duval, EOS).")
        try:
            tone_in = input("   Selecciona (1-3) [1]: ").strip()
        except (EOFError, KeyboardInterrupt):
            tone_in = "1"
        tones = {"1": "pragmatic", "2": "mentoring", "3": "academic"}
        tone = tones.get(tone_in, "pragmatic")

        print("\n7. ¿Cuál es tu formato predilecto para los materiales finales?")
        print("   [1] Typst (PDF moderno, ultrarrápido y limpio) [Recomendado]")
        print("   [2] LaTeX (Código fuente .tex editable)")
        print("   [3] Moodle XML (Para importar en Canvas, Moodle o Blackboard)")
        try:
            fmt_in = input("   Selecciona (1-3) [1]: ").strip()
        except (EOFError, KeyboardInterrupt):
            fmt_in = "1"
        formats = {"1": "typst", "2": "latex", "3": "moodle"}
        output_format = formats.get(fmt_in, "typst")

    profile_data: Dict[str, Any] = {
        "version": "1.1",
        "educator": {
            "name": name,
            "school": school,
            "level": level,
            "curriculum_default": curriculum,
            "framework_default": framework,
        },
        "interaction_mode": {
            "tone": tone,
            "collaboration": "co-design",
        },
        "tooling_preferences": {
            "output_format": output_format,
            "auto_compile": True,
            "cas_strictness": "high",
        },
    }

    save_profile(profile_data, target_path)

    if not non_interactive:
        print("\n" + "=" * 65)
        print(f"  [OK] Perfil guardado con éxito en: {target_path.resolve()}")
        print(f"  A partir de ahora, los agentes se comunicarán contigo en modo: {tone.upper()}")
        print("=" * 65)

    return profile_data
