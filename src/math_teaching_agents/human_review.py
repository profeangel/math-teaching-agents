"""
Módulo de Punto de Control Humano (Human-in-the-Loop Checkpoint).
Permite al docente inspeccionar un resumen didáctico enriquecido del borrador aprobado por Gate 1,
modificar parámetros pedagógicos o texto, o cancelar antes de proceder al renderizado tipográfico (Gate 2).
"""

from typing import Dict, Any, Optional, Callable
from pathlib import Path
import os
import sys
import yaml


def format_didactic_summary(draft_data: Dict[str, Any], artifact_type: str = "assessment") -> str:
    """
    Genera una presentación estructurada y legible en lenguaje natural pedagógico
    para que el docente audite el borrador antes de su maquetación.
    """
    lines = []
    lines.append("=" * 70)
    lines.append("  PUNTO DE CONTROL HUMANO: RESUMEN DIDÁCTICO DEL BORRADOR")
    lines.append("=" * 70)

    is_unit = "phases" in draft_data or artifact_type in ("didactic_unit", "didactic-unit", "unit")

    if is_unit:
        # UNIDAD DIDÁCTICA
        meta = draft_data.get("metadata", {})
        lines.append(f"  Título:            {meta.get('title', 'Sin título')}")
        lines.append(f"  Nivel Destinatario:{meta.get('target_grade', 'N/A')}")
        lines.append(f"  Duración Estimada: {meta.get('estimated_duration_sessions', 1)} sesiones ({meta.get('hours_per_session', 2)} hrs/sesión)")
        lines.append(f"  Marco Didáctico:   {meta.get('didactic_framework', 'No especificado')}")
        lines.append("-" * 70)

        just = draft_data.get("didactic_justification", {})
        if just:
            lines.append("  [Articulación Didáctica & Prerrequisitos]")
            if just.get("prerequisites_required"):
                lines.append("  * Prerrequisitos Clave:")
                for pr in just["prerequisites_required"]:
                    lines.append(f"      - {pr}")
            if just.get("learning_obstacles_addressed"):
                lines.append("  * Obstáculos de Aprendizaje Diagnosticados (KFLM):")
                for obs in just["learning_obstacles_addressed"]:
                    lines.append(f"      - {obs.get('obstacle_name')}: {obs.get('description', '')}")
            lines.append("-" * 70)

        lines.append("  [Fases Metodológicas de la Secuencia de Clase]")
        for phase in draft_data.get("phases", []):
            pid = phase.get("phase_id", "?")
            pname = phase.get("phase_name", "")
            cog = phase.get("cognitive_demand", "")
            lines.append(f"\n  * FASE {pid}: {pname}")
            lines.append(f"    - Demanda Cognitiva (Stein & Smith): {cog}")
            lines.append(f"    - Elección Didáctica: {phase.get('example_choice_rationale', '')}")
            lines.append(f"    - Rol del Docente:   {phase.get('teacher_role', '')}")
            lines.append(f"    - Actividad Alumno:  {phase.get('student_activity', '')}")
            udl = phase.get("udl_guidelines", {})
            if udl:
                lines.append(f"    - Pautas DUA:        Rep: {udl.get('representation', 'N/A')} | Exp: {udl.get('action_expression', 'N/A')}")

    else:
        # INSTRUMENTO DE EVALUACIÓN
        meta = draft_data.get("metadata", {})
        lines.append(f"  Título:            {meta.get('title', 'Sin título')}")
        lines.append(f"  Tipo Evaluación:   {meta.get('assessment_type', 'FORMATIVA')} ({meta.get('modality', 'INDIVIDUAL')})")
        lines.append(f"  Nivel Destinatario:{meta.get('target_grade', 'N/A')}")
        lines.append(f"  Puntaje Total:     {meta.get('total_points', 0)} pts | Exigencia: {meta.get('passing_threshold_percentage', 60)}%")
        lines.append(f"  Tiempo Estimado:   {meta.get('estimated_duration_minutes', 45)} minutos")
        lines.append("-" * 70)

        spec = draft_data.get("specification_table", {})
        if spec:
            cog_dist = spec.get("cognitive_process_distribution", {})
            if cog_dist:
                dist_str = ", ".join(f"{k}: {v}%" for k, v in cog_dist.items() if v)
                lines.append(f"  Matriz Cognitiva (Bloom-Anderson): {dist_str}")
            lines.append("-" * 70)

        items = draft_data.get("items", [])
        lines.append(f"  [Ítems Evaluativos Planificados ({len(items)} ítems)]")
        for item in items:
            iid = item.get("item_id", "?")
            fmt = item.get("format", "")
            pts = item.get("points", 1)
            bloom = item.get("bloom_anderson_level", "")
            mtsk = item.get("mtsk_subdomain", "")
            stem = item.get("stem", "").strip()

            lines.append(f"\n  * ÍTEM {iid} [{fmt}] ({pts} pts) | Bloom: {bloom} | MTSK: {mtsk}")
            lines.append(f"    Enunciado: {stem}")

            if fmt == "MULTIPLE_CHOICE":
                lines.append("    Alternativas de Selección:")
                for opt in item.get("options", []):
                    key = opt.get("key") or opt.get("label", "?")
                    txt = opt.get("text", "")
                    is_corr = opt.get("is_correct", False)
                    if is_corr:
                        lines.append(f"      [{key}] {txt}  <-- CLAVE CORRECTA")
                    else:
                        m_ref = opt.get("misconception_ref") or opt.get("misconception_code", "Error de distractor")
                        lines.append(f"      [{key}] {txt}  (Distractor KFLM: {m_ref})")

            elif fmt in ("OPEN_DEVELOPMENT", "PROOF_ARGUMENT", "TRUE_FALSE_JUSTIFIED"):
                rub = item.get("rubric", {})
                if rub:
                    crit = rub.get("criterion_name", "Desempeño")
                    lines.append(f"    Rúbrica Analítica ({crit}):")
                    levels = rub.get("levels", {})
                    for lvl_name, desc in levels.items():
                        lines.append(f"      - {lvl_name.upper()}: {desc}")

    lines.append("=" * 70)
    return "\n".join(lines)


def execute_human_review(
    draft_data: Dict[str, Any],
    draft_path: Optional[Path] = None,
    artifact_type: str = "assessment",
    non_interactive: bool = False,
    simulated_choice: Optional[str] = None,
    console_input_fn: Optional[Callable[[str], str]] = None
) -> Dict[str, Any]:
    """
    Punto de control interactivo donde el docente puede:
    [1] Aprobar borrador e iniciar maquetación (Gate 2).
    [2] Abrir y editar el archivo YAML en el editor del sistema.
    [3] Modificar parámetros textuales rápidamente desde consola.
    [4] Cancelar y abortar la generación.
    """
    input_fn = console_input_fn or input

    # Resumen enriquecido visible
    summary_text = format_didactic_summary(draft_data, artifact_type=artifact_type)
    print("\n" + summary_text + "\n")

    if non_interactive:
        print("  [MODO NO INTERACTIVO] Aprobación automática en punto de control humano.")
        return {"status": "APPROVED", "modified": False, "draft_data": draft_data}

    menu = (
        "  OPCIONES DE REVISIÓN DOCENTE (PUNTO DE CONTROL HUMANO):\n"
        "  [1] Aprobar borrador y continuar directamente a Gate 2 (Maquetación Tipográfica)\n"
        "  [2] Abrir borrador YAML en el editor del sistema para ajustes de aula\n"
        "  [3] Modificar metadatos desde consola (Título, Duración o Enunciados)\n"
        "  [4] Cancelar la entrega y abortar el flujo\n"
        "  Seleccione una opción [1-4] (por defecto: 1): "
    )

    if simulated_choice is not None:
        choice = simulated_choice.strip()
    else:
        try:
            choice = input_fn(menu).strip()
        except (EOFError, KeyboardInterrupt):
            choice = "4"

    if not choice:
        choice = "1"

    # Opción 1: Aprobar directamente
    if choice == "1":
        print("\n  [OK] Borrador aprobado por el docente. Procediendo a Gate 2.")
        return {"status": "APPROVED", "modified": False, "draft_data": draft_data}

    # Opción 2: Abrir en editor externo
    elif choice == "2":
        if not draft_path or not draft_path.exists():
            print("  [AVISO] No se encontró ruta en disco para abrir editor. Procediendo con datos actuales.")
            return {"status": "APPROVED", "modified": False, "draft_data": draft_data}

        print(f"\n  Abriendo {draft_path.name} en el editor del sistema...")
        try:
            if sys.platform.startswith("win"):
                os.system(f'notepad.exe "{draft_path}"')
            else:
                editor = os.environ.get("EDITOR", "nano")
                os.system(f'{editor} "{draft_path}"')
        except Exception as e:
            print(f"  [ERROR] No se pudo lanzar el editor: {e}")

        if simulated_choice is None:
            input_fn("\n  Presione [Enter] una vez que haya guardado y cerrado los cambios en el archivo...")

        # Re-leer archivo modificado
        try:
            with open(draft_path, "r", encoding="utf-8") as f:
                new_data = yaml.safe_load(f)
            print("  [OK] Cambios del docente recargados desde disco.")
            return {"status": "MODIFIED", "modified": True, "draft_data": new_data}
        except Exception as e:
            print(f"  [ERROR] El archivo editado contiene sintaxis YAML inválida: {e}")
            return {"status": "MODIFIED_INVALID_SYNTAX", "modified": False, "error": str(e), "draft_data": draft_data}

    # Opción 3: Modificación interactiva rápida en consola
    elif choice == "3":
        print("\n  --- EDICIÓN RÁPIDA DE METADATOS ---")
        meta = draft_data.get("metadata", {})
        curr_title = meta.get("title", "")
        new_title = input_fn(f"  Nuevo Título [{curr_title}]: ").strip()
        if new_title:
            meta["title"] = new_title

        if "phases" in draft_data:
            curr_dur = meta.get("estimated_duration_sessions", 1)
            new_dur = input_fn(f"  Sesiones estimadas [{curr_dur}]: ").strip()
            if new_dur:
                try:
                    meta["estimated_duration_sessions"] = int(new_dur)
                except ValueError:
                    pass
        else:
            curr_mins = meta.get("estimated_duration_minutes", 45)
            new_mins = input_fn(f"  Minutos estimados [{curr_mins}]: ").strip()
            if new_mins:
                try:
                    meta["estimated_duration_minutes"] = int(new_mins)
                except ValueError:
                    pass

        # Guardar en disco si la ruta existe
        if draft_path:
            with open(draft_path, "w", encoding="utf-8") as f:
                yaml.dump(draft_data, f, sort_keys=False, allow_unicode=True)

        print("  [OK] Parámetros actualizados con éxito.")
        return {"status": "MODIFIED", "modified": True, "draft_data": draft_data}

    # Opción 4: Cancelar
    else:
        print("\n  [CANCELADO] Flujo abortado por el docente.")
        return {"status": "CANCELLED", "modified": False, "draft_data": draft_data}
