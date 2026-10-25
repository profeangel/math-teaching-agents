#!/usr/bin/env python3
"""
CLI Tool: Renderizador y Compilador Multiformato (Gate 2).
Herramienta determinista para Harnesses de Agentes (Claude Code, OpenCode, Antigravity)
que transforma borradores semánticos neutros (evaluaciones o unidades didácticas)
en documentos maquetados profesionales en Typst (.typ), LaTeX (.tex) o Moodle XML (.xml),
y gestiona la compilación directa a PDF.

Uso:
  python tools/render.py path/to/draft.yaml --format typst
  python tools/render.py path/to/draft.yaml --format typst --compile
  python tools/render.py path/to/draft.yaml --format latex -o evaluacion.tex
  python tools/render.py path/to/draft.yaml --format moodle -o banco_preguntas.xml
  python tools/render.py path/to/draft.yaml --format typst --compile --json
"""

import sys
import argparse
import json
from pathlib import Path

# Asegurar importación del paquete src local sin requerir instalación previa
ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Asegurar codificación UTF-8 en consola
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import yaml
from math_teaching_agents.engines.typst_engine import TypstEngine
from math_teaching_agents.engines.latex_engine import LatexEngine
from math_teaching_agents.engines.moodle_engine import MoodleEngine


def render_and_compile(
    draft_path: Path,
    output_format: str = "typst",
    output_file: Path = None,
    template_path: Path = None,
    compile_pdf: bool = False
) -> dict:
    """Ejecuta la renderización del borrador y opcionalmente compila a PDF."""
    if not draft_path.exists():
        return {
            "status": "ERROR",
            "message": f"Archivo no encontrado: {draft_path}",
            "success": False
        }

    try:
        with open(draft_path, "r", encoding="utf-8") as f:
            if draft_path.suffix in (".yaml", ".yml"):
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"Error al parsear archivo {draft_path.name}: {e}",
            "success": False
        }

    fmt = output_format.lower()
    report = {
        "gate": 2,
        "tool": "render.py",
        "draft_file": str(draft_path),
        "format": fmt,
        "status": "SUCCESS",
        "success": True,
        "rendered_file": None,
        "pdf_file": None,
        "compile_status": None,
        "messages": []
    }

    # Determinación de ruta por defecto
    ext_map = {"typst": ".typ", "latex": ".tex", "moodle": ".xml"}
    target_ext = ext_map.get(fmt, ".txt")
    out_path = Path(output_file) if output_file else draft_path.with_suffix(target_ext)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        if fmt == "typst":
            engine = TypstEngine(template_path=template_path)
            rendered_code = engine.render_document(data)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(rendered_code)
            report["rendered_file"] = str(out_path)

            if compile_pdf:
                comp = engine.compile_pdf(out_path)
                report["compile_status"] = comp.get("status")
                if comp.get("status") == "SUCCESS":
                    report["pdf_file"] = comp.get("pdf_file")
                    report["messages"].append(f"Compilación Typst exitosa: {comp.get('pdf_file')}")
                elif comp.get("status") == "SKIPPED":
                    report["messages"].append(f"Compilación omitida: {comp.get('message')}")
                else:
                    report["status"] = "FAIL"
                    report["success"] = False
                    report["messages"].append(f"Falla de compilación Typst: {comp.get('error', comp.get('message'))}")

        elif fmt == "latex":
            engine = LatexEngine(template_path=template_path)
            rendered_code = engine.render_document(data)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(rendered_code)
            report["rendered_file"] = str(out_path)

            if compile_pdf:
                comp = engine.compile_pdf(out_path)
                report["compile_status"] = comp.get("status")
                if comp.get("status") == "SUCCESS":
                    report["pdf_file"] = comp.get("pdf_file")
                    report["messages"].append(f"Compilación LaTeX exitosa ({comp.get('engine')}): {comp.get('pdf_file')}")
                elif comp.get("status") == "SKIPPED":
                    report["messages"].append(f"Compilación omitida: {comp.get('message')}")
                else:
                    report["status"] = "FAIL"
                    report["success"] = False
                    report["messages"].append(f"Falla de compilación LaTeX: {comp.get('log', comp.get('message'))}")

        elif fmt == "moodle":
            engine = MoodleEngine()
            rendered_code = engine.render_document(data)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(rendered_code)
            report["rendered_file"] = str(out_path)
            report["messages"].append(f"Archivo Moodle XML generado: {out_path}")

        else:
            return {
                "status": "ERROR",
                "message": f"Formato no soportado: '{fmt}'. Use typst, latex o moodle.",
                "success": False
            }

    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"Error durante la renderización: {e}",
            "success": False
        }

    return report


def main():
    parser = argparse.ArgumentParser(
        prog="tools/render.py",
        description="Renderizador y Compilador Multiformato (Typst, LaTeX, Moodle XML) para Gate 2"
    )
    parser.add_argument("file", help="Ruta al borrador .yaml o .json a renderizar")
    parser.add_argument("--format", "-f", choices=["typst", "latex", "moodle"], default="typst",
                        help="Formato de salida (default: typst)")
    parser.add_argument("--output", "-o", help="Ruta del archivo generado")
    parser.add_argument("--template", "-t", help="Ruta a plantilla personalizada")
    parser.add_argument("--compile", "-c", action="store_true", help="Compilar a PDF si el compilador está disponible")
    parser.add_argument("--json", "-j", action="store_true", help="Salida en formato JSON para subagentes")

    args = parser.parse_args()

    draft_path = Path(args.file)
    output_path = Path(args.output) if args.output else None
    template_path = Path(args.template) if args.template else None

    res = render_and_compile(
        draft_path=draft_path,
        output_format=args.format,
        output_file=output_path,
        template_path=template_path,
        compile_pdf=args.compile
    )

    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print("=" * 65)
        print("  GATE 2: RENDERIZADOR Y MAQUETACIÓN MULTIFORMATO")
        print(f"  Borrador: {draft_path.name}")
        print(f"  Formato:  {args.format}")
        print("=" * 65)

        if res.get("rendered_file"):
            print(f"  [OK] Archivo generado: {res.get('rendered_file')}")

        if res.get("compile_status"):
            st = res.get("compile_status")
            pdf = res.get("pdf_file", "")
            print(f"  [{st}] Compilación a PDF: {pdf if pdf else st}")

        for msg in res.get("messages", []):
            print(f"  ℹ {msg}")

        print("\n" + "-" * 65)
        print(f"  DICTAMEN GATE 2: {res.get('status')}")
        print("=" * 65)

    sys.exit(0 if res.get("success") else 1)


if __name__ == "__main__":
    main()
