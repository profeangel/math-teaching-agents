"""
Línea de Comandos (CLI) de Math Teaching Agents.
Interfaz unificada para validación de contratos, auditoría matemática SymPy, compilación y dashboard interactivo.
"""

import sys
import argparse
from pathlib import Path
import yaml
import json

# Asegurar codificación UTF-8 en consolas Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from math_teaching_agents.validators.schema_validator import SchemaValidator
from math_teaching_agents.validators.math_verifier import SymbolicMathVerifier
from math_teaching_agents.engines.latex_engine import LatexEngine
from math_teaching_agents.engines.typst_engine import TypstEngine
from math_teaching_agents.engines.moodle_engine import MoodleEngine
from math_teaching_agents.llm_runtime import DidacticPipeline, get_provider
from math_teaching_agents.profile import load_profile, run_init_wizard


def get_root_dir() -> Path:
    """Calcula la raíz del repositorio."""
    return Path(__file__).resolve().parents[2]


def cmd_validate(args):
    """Comando: Valida todos los schemas, curriculums y frameworks, o un borrador específico."""
    root = get_root_dir()
    validator = SchemaValidator(root)

    target_file = getattr(args, "file", None)
    if target_file:
        path = Path(target_file)
        if not path.exists():
            print(f"Error: Archivo no encontrado: {path}")
            return 1
        with open(path, "r", encoding="utf-8") as f:
            if path.suffix in (".yaml", ".yml"):
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        schema_name = "didactic-unit.json" if ("phases" in data or "didactic_phases" in data) else "assessment-spec.json"
        ok, errors = validator.validate_instance(data, schema_name=schema_name)
        print("=" * 65)
        print(f"  VALIDACIÓN DE ESQUEMA DIDÁCTICO: {path.name}")
        print(f"  Esquema empleado: {schema_name}")
        print("=" * 65)
        if ok:
            print("  [OK] El documento cumple estrictamente con el contrato del esquema.")
            print("=" * 65)
            return 0
        else:
            print(f"  [FAIL] Se detectaron {len(errors)} errores:")
            for err in errors:
                print(f"    - {err}")
            print("=" * 65)
            return 1

    print("=" * 65)
    print("  MATH TEACHING AGENTS: AUDITORÍA DE CONTRATOS DIDÁCTICOS Y SCHEMAS")
    print("=" * 65)

    all_passed = True

    # 1. Schemas JSON
    print("\n[1] Verificando Esquemas JSON (Draft 2020-12)...")
    json_results = validator.validate_all_json_schemas()
    for name, ok, msg in json_results:
        symbol = "OK" if ok else "FAIL"
        print(f"  [{symbol:<4}] {name:<26} -> {msg}")
        if not ok:
            all_passed = False

    # 2. Curriculums YAML
    print("\n[2] Verificando Adaptadores Curriculares...")
    curr_results = validator.validate_curriculums()
    for name, ok, msg in curr_results:
        symbol = "OK" if ok else "FAIL"
        print(f"  [{symbol:<4}] {name:<26} -> {msg}")
        if not ok:
            all_passed = False

    # 3. Frameworks Didácticos YAML
    print("\n[3] Verificando Marcos Teóricos Didácticos...")
    fw_results = validator.validate_frameworks()
    for name, ok, msg in fw_results:
        symbol = "OK" if ok else "FAIL"
        print(f"  [{symbol:<4}] {name:<26} -> {msg}")
        if not ok:
            all_passed = False

    print("\n" + "-" * 65)
    if all_passed:
        print("  RESULTADO: Todos los contratos y especificaciones son VÁLIDOS.")
        print("=" * 65)
        return 0
    else:
        print("  RESULTADO: Se detectaron inconsistencias en las especificaciones.")
        print("=" * 65)
        return 1


def cmd_verify_math(args):
    """Comando: Ejecuta auditoría simbólica SymPy en una evaluación."""
    path = Path(args.file)
    if not path.exists():
        print(f"Error: Archivo no encontrado: {path}")
        return 1

    with open(path, "r", encoding="utf-8") as f:
        if path.suffix in (".yaml", ".yml"):
            data = yaml.safe_load(f)
        else:
            data = json.load(f)

    verifier = SymbolicMathVerifier()
    print("=" * 65)
    print(f"  GATE 1: AUDITORÍA MATEMÁTICA SIMBÓLICA CON SYMPY")
    print(f"  Archivo: {path.name}")
    print("=" * 65)

    items = data.get("items", [])
    all_ok = True

    for item in items:
        item_id = item.get("item_id", "?")
        fmt = item.get("format", "")
        print(f"\n[Ítem {item_id}] Formato: {fmt}")
        res = verifier.verify_item(item)
        status = res.get("status", "PASS")
        if status == "PASS":
            if fmt == "MULTIPLE_CHOICE":
                print("  [OK] Distractores únicos y mutuamente excluyentes.")
            else:
                print("  [OK] Ítem cualitativo verificado.")
            if "equation_check" in res:
                print(f"  [OK] Solución formal: {res['equation_check']['true_solutions']}")
            if "geometric_check" in res:
                print(f"  [OK] Invariante geométrico verificado: {res['geometric_check']}")
            if "probability_check" in res:
                print(f"  [OK] Axiomas de Kolmogorov verificados: {res['probability_check'].get('probabilities')}")
            if "combinatorics_check" in res:
                comb = res['combinatorics_check']
                print(f"  [OK] Cálculo combinatorio verificado: C({comb.get('n')},{comb.get('k')})={comb.get('true_combinations')}")
        else:
            print("  [FAIL] Inconsistencia detectada en el ítem.")
            for dup in res.get("duplicates", []):
                print(f"    - {dup}")
            if res.get("error_detail"):
                print(f"    - {res['error_detail']}")
            all_ok = False

    print("\n" + "=" * 65)
    return 0 if all_ok else 1


def cmd_render(args):
    """Comando: Renderiza un borrador semántico a formato LaTeX, Typst o Moodle XML."""
    path = Path(args.file)
    if not path.exists():
        print(f"Error: Archivo no encontrado: {path}")
        return 1

    with open(path, "r", encoding="utf-8") as f:
        if path.suffix in (".yaml", ".yml"):
            data = yaml.safe_load(f)
        else:
            data = json.load(f)

    fmt = getattr(args, "format", "latex").lower()
    if fmt == "typst":
        engine = TypstEngine()
        rendered_code = engine.render_document(data)
        out_path = Path(args.output) if args.output else path.with_suffix(".typ")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(rendered_code)
        print(f"[OK] Documento Typst generado con éxito en: {out_path}")
    elif fmt == "moodle":
        engine = MoodleEngine()
        rendered_code = engine.render_document(data)
        out_path = Path(args.output) if args.output else path.with_suffix(".xml")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(rendered_code)
        print(f"[OK] Archivo Moodle XML generado con éxito en: {out_path}")
        return 0
    else:
        engine = LatexEngine()
        rendered_code = engine.render_document(data)
        out_path = Path(args.output) if args.output else path.with_suffix(".tex")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(rendered_code)
        print(f"[OK] Documento LaTeX generado con éxito en: {out_path}")

    if args.compile:
        print(f"Intentando compilar PDF con motor del sistema ({fmt})...")
        comp_res = engine.compile_pdf(out_path)
        print(f"Resultado de compilación: {comp_res.get('status')}")
        if comp_res.get("status") == "SUCCESS":
            print(f"[OK] PDF generado: {comp_res.get('pdf_file')}")
        else:
            print(f"ℹ Detalle: {comp_res.get('message', comp_res.get('log'))}")

    return 0


def cmd_init(args):
    """Comando: Configura el perfil pedagógico y preferencias del docente."""
    root = get_root_dir()
    answers = {}
    if getattr(args, "name", None):
        answers["name"] = args.name
    if getattr(args, "level", None):
        answers["level"] = args.level
    if getattr(args, "curriculum", None):
        answers["curriculum"] = args.curriculum
    if getattr(args, "tone", None):
        answers["tone"] = args.tone
    if getattr(args, "format", None):
        answers["format"] = args.format

    profile = run_init_wizard(
        root_dir=root,
        non_interactive=getattr(args, "non_interactive", False),
        answers=answers,
        force=getattr(args, "force", False)
    )

    if getattr(args, "non_interactive", False):
        print("=" * 65)
        print("  MATH TEACHING AGENTS: CONFIGURACIÓN INICIAL (MODO DESATENDIDO)")
        print("=" * 65)
        print(f"  Docente:         {profile['educator']['name']}")
        print(f"  Nivel:           {profile['educator']['level']}")
        print(f"  Currículo Base:  {profile['educator']['curriculum_default']}")
        print(f"  Tono Didáctico:  {profile['interaction_mode']['tone'].upper()}")
        print(f"  Formato Salida:  {profile['tooling_preferences']['output_format']}")
        print("=" * 65)
    return 0


def cmd_run(args):
    """Comando: Ejecuta el pipeline didáctico multiagente con Self-Healing y soporte multi-etapa."""
    root = get_root_dir()
    provider = get_provider(args.provider)
    pipeline = DidacticPipeline(root_dir=root, provider=provider)

    max_retries = getattr(args, "max_retries", 3)
    multi_stage = getattr(args, "multi_stage", False)
    artifact_type = getattr(args, "type", "assessment")

    # Cargar perfil si existe para defaults contextuales
    profile = load_profile(root_dir=root)
    curriculum = args.curriculum
    output_format = args.format
    tone = getattr(args, "tone", None)

    if profile:
        educator = profile.get("educator", {})
        interaction = profile.get("interaction_mode", {})
        tooling = profile.get("tooling_preferences", {})

        # Si el usuario no modificó el default en CLI pero hay perfil, priorizar perfil
        if args.curriculum == "chile-mineduc" and educator.get("curriculum_default"):
            curriculum = educator.get("curriculum_default")
        if args.format == "latex" and tooling.get("output_format"):
            output_format = tooling.get("output_format")
        if tone is None:
            tone = interaction.get("tone", "pragmatic")
    else:
        if tone is None:
            tone = "pragmatic"

    print("=" * 65)
    print("  MATH TEACHING AGENTS: ORQUESTACIÓN MULTIAGENTE DIDÁCTICA")
    print("=" * 65)
    if profile:
        print(f"  Docente:           {profile.get('educator', {}).get('name', 'Docente')} ({profile.get('educator', {}).get('level', 'secondary')})")
        print(f"  Tono de Soporte:   {tone.upper()}")
    else:
        print(f"  Docente:           [No inicializado - ejecuta 'math-agent init']")
        print(f"  Tono de Soporte:   {tone.upper()} (Por defecto)")
    print(f"  Tipo de Artefacto: {artifact_type}")
    print(f"  Tema:              {args.topic}")
    print(f"  Currículo:         {curriculum}")
    print(f"  Marco Teórico:     {args.framework}")
    print(f"  Formato Salida:    {output_format}")
    print(f"  Proveedor LLM:     {args.provider}")
    print(f"  Max Reintentos:    {max_retries}")
    print(f"  Modo Multi-Etapa:  {multi_stage}")
    print("-" * 65)

    interactive_review = getattr(args, "interactive_review", False)

    out_dir = Path(args.output_dir) if args.output_dir else root / "output"
    res = pipeline.run(
        topic=args.topic,
        curriculum_id=curriculum,
        framework_id=args.framework,
        output_format=output_format,
        output_dir=out_dir,
        compile_pdf=args.compile,
        max_retries=max_retries,
        multi_stage=multi_stage,
        artifact_type=artifact_type,
        profile=profile,
        tone=tone,
        interactive_review=interactive_review
    )

    status = res.get("status")
    print(f"  Estado Global:     {status}")

    if status == "CANCELLED_BY_USER":
        print(f"  ℹ {res.get('message', 'Flujo cancelado por el usuario en el punto de control humano.')}")
        print("=" * 65)
        return 0

    if status == "REJECTED_AFTER_HUMAN_REVIEW":
        print(f"  [ERROR] {res.get('message')}")
        print("  Observaciones de Gate 1 tras edición del docente:")
        for fb in res.get("feedback", []):
            print(f"    {fb}")
        print("=" * 65)
        return 1

    print(f"  Gate 1 (CAS):      {res.get('gate_1', {}).get('status')}")
    print(f"  Intentos Usados:   {res.get('attempts_needed', res.get('attempts_exhausted', 1))}")

    if "gate_2" in res:
        print(f"  Gate 2 (Render):   {res.get('gate_2', {}).get('status')}")
        print(f"  Borrador Semántico:{res.get('draft_path')}")
        print(f"  Artefacto Salida:  {res.get('rendered_path')}")
        if args.compile and output_format != "moodle":
            comp = res.get("gate_2", {}).get("compile_result", {})
            print(f"  Compilación a PDF: {comp.get('status')} - {comp.get('pdf_file', comp.get('message'))}")
    else:
        print(f"  ℹ Pipeline detenido en Gate 1 tras agotar intentos de autorreparación.")
        print(f"  Detalle Gate 1: {json.dumps(res.get('gate_1'), indent=2, ensure_ascii=False)}")

    print("=" * 65)
    return 0 if res.get("status") == "COMPLETED" else 1


def cmd_ui(args):
    """Comando: Inicia el dashboard interactivo web."""
    from math_teaching_agents.ui import start_server
    start_server(
        host=args.host,
        port=args.port,
        open_browser=not args.no_browser,
        root_dir=get_root_dir()
    )
    return 0


def cmd_info(args):
    """Comando: Muestra estadísticas y componentes activos del sistema."""
    root = get_root_dir()
    agents = list((root / "agents").rglob("*.md"))
    curriculums = list((root / "curriculums").glob("*.yaml"))
    frameworks = list((root / "frameworks").glob("*.yaml"))
    schemas = list((root / "schemas").glob("*.json"))
    profile = load_profile(root_dir=root)

    print("=" * 60)
    print("  MULTI-AGENT SYSTEM FOR MATHEMATICS TEACHING & DIDACTICS")
    print("=" * 60)
    if profile:
        ed = profile.get("educator", {})
        im = profile.get("interaction_mode", {})
        tp = profile.get("tooling_preferences", {})
        print(f"  Docente Activo:           {ed.get('name', 'Docente')} ({ed.get('level', 'secondary')})")
        print(f"  Tono de Interacción:      {im.get('tone', 'pragmatic').upper()}")
        print(f"  Currículo Preferido:      {ed.get('curriculum_default', 'chile-mineduc')}")
        print(f"  Formato Preferido:        {tp.get('output_format', 'typst')}")
    else:
        print(f"  Docente Activo:           [Sin inicializar - usa 'math-agent init']")
    print("-" * 60)
    print(f"  Agentes Totales:          {len(agents)}")
    print(f"  Adaptadores Curriculares: {len(curriculums)} ({', '.join(p.stem for p in curriculums)})")
    print(f"  Marcos Teóricos:          {len(frameworks)} ({', '.join(p.stem for p in frameworks)})")
    print(f"  Contratos Semánticos:     {len(schemas)} ({', '.join(p.stem for p in schemas)})")
    print(f"  Formatos de Renderizado:  LaTeX (.tex), Typst (.typ), Moodle XML (.xml)")
    print("=" * 60)
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="math-agent",
        description="Multi-Agent System for Mathematics Teaching & Didactic Engineering"
    )
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

    # init
    sub_init = subparsers.add_parser("init", help="Configura el perfil pedagógico y preferencias de interacción del docente.")
    sub_init.add_argument("--force", "-f", action="store_true", help="Sobrescribe el perfil existente si ya existe")
    sub_init.add_argument("--non-interactive", "-y", action="store_true", help="Modo desatendido sin preguntas interactivas")
    sub_init.add_argument("--name", help="Nombre o tratamiento del docente (ej. 'Prof. Soto')")
    sub_init.add_argument("--level", choices=["primary", "secondary", "high_school", "university"], help="Nivel educativo principal")
    sub_init.add_argument("--curriculum", help="Currículo por defecto (ej. chile-mineduc, mexico-nem, colombia-men)")
    sub_init.add_argument("--tone", choices=["pragmatic", "mentoring", "academic"], help="Tono de comunicación de los agentes")
    sub_init.add_argument("--format", choices=["typst", "latex", "moodle"], help="Formato de salida predilecto")
    sub_init.set_defaults(func=cmd_init)

    # validate
    sub_val = subparsers.add_parser("validate", help="Valida la integridad de los esquemas, o valida un archivo borrador específico.")
    sub_val.add_argument("file", nargs="?", help="Ruta opcional al archivo borrador para validar contra el schema")
    sub_val.set_defaults(func=cmd_validate)

    # verify-math
    sub_math = subparsers.add_parser("verify-math", help="Ejecuta la auditoría matemática formal de Gate 1 con SymPy.")
    sub_math.add_argument("file", help="Ruta al archivo .yaml o .json de evaluación")
    sub_math.set_defaults(func=cmd_verify_math)

    # render
    sub_ren = subparsers.add_parser("render", help="Renderiza un borrador semántico a formato LaTeX, Typst o Moodle XML.")
    sub_ren.add_argument("file", help="Ruta al borrador semántico")
    sub_ren.add_argument("--format", "-f", choices=["latex", "typst", "moodle"], default="latex", help="Formato de maquetación (por defecto: latex)")
    sub_ren.add_argument("--output", "-o", help="Ruta del archivo de salida")
    sub_ren.add_argument("--compile", "-c", action="store_true", help="Intenta compilar a PDF")
    sub_ren.set_defaults(func=cmd_render)

    # run
    sub_run = subparsers.add_parser("run", help="Ejecuta el ciclo de vida completo de generación y validación multiagente.")
    sub_run.add_argument("--type", "-T", choices=["assessment", "didactic-unit"], default="assessment", help="Tipo de artefacto didáctico: assessment (evaluación) o didactic-unit (unidad didáctica)")
    sub_run.add_argument("--topic", "-t", required=True, help="Tema u objetivo matemático")
    sub_run.add_argument("--curriculum", "-cur", default="chile-mineduc", help="Identificador del adaptador curricular (ej. chile-mineduc, mexico-nem, colombia-men)")
    sub_run.add_argument("--framework", "-fw", default="duval-trrs", help="Marco teórico de referencia (ej. duval-trrs, godino-eos, brousseau-tsd)")
    sub_run.add_argument("--tone", choices=["pragmatic", "mentoring", "academic"], default=None, help="Tono didáctico: pragmatic (aula directa), mentoring (formativo) o academic (investigación)")
    sub_run.add_argument("--format", "-f", choices=["latex", "typst", "moodle"], default="latex", help="Formato de salida (latex, typst o moodle)")
    sub_run.add_argument("--provider", "-p", default="mock", help="Proveedor de LLM (mock, ollama, gemini, openai, anthropic)")
    sub_run.add_argument("--output-dir", "-o", help="Directorio de artefactos generados")
    sub_run.add_argument("--compile", "-c", action="store_true", help="Intenta compilar el documento renderizado a PDF")
    sub_run.add_argument("--max-retries", "-r", type=int, default=3, help="Número máximo de intentos de autorreparación si Gate 1 rechaza (default: 3)")
    sub_run.add_argument("--multi-stage", "-m", action="store_true", help="Activa orquestación multi-etapa (Análisis MTSK previo a redacción GPK)")
    sub_run.add_argument("--interactive-review", "-i", action="store_true", help="Punto de control humano: pausa tras Gate 1 para revisar y editar el borrador antes de maquetar")
    sub_run.set_defaults(func=cmd_run)

    # ui / serve
    sub_ui = subparsers.add_parser("ui", help="Inicia la interfaz gráfica web interactiva en el navegador.")
    sub_ui.add_argument("--port", type=int, default=8501, help="Puerto HTTP local (default: 8501)")
    sub_ui.add_argument("--host", default="127.0.0.1", help="Host de escucha (default: 127.0.0.1)")
    sub_ui.add_argument("--no-browser", action="store_true", help="No abrir automáticamente el navegador")
    sub_ui.set_defaults(func=cmd_ui)

    # info
    sub_info = subparsers.add_parser("info", help="Muestra el resumen de agentes y recursos del ecosistema.")
    sub_info.set_defaults(func=cmd_info)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    code = args.func(args)
    sys.exit(code)


if __name__ == "__main__":
    main()
