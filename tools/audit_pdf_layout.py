#!/usr/bin/env python3
"""
CLI Tool: Auditor de Layout y Maquetación Visual de PDFs (Gate 2).
Inspecciona documentos PDF compilados mediante pypdf para prevenir la 'ilusión del código 0':
detecta desbordes huérfanos, preguntas partidas, títulos huérfanos, presupuesto de páginas
y corrupción tipográfica residual de LaTeX a Typst.

Uso:
  python tools/audit_pdf_layout.py documento.pdf
  python tools/audit_pdf_layout.py documento.pdf --budget 2
  python tools/audit_pdf_layout.py documento.pdf --json
  python tools/audit_pdf_layout.py documento.pdf --draft borrador.yaml
"""

import sys
import argparse
import json
from pathlib import Path

# Asegurar importación de src local
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
from math_teaching_agents.validators.layout_auditor import LayoutAuditor


def main():
    parser = argparse.ArgumentParser(
        description="Auditor determinista de layout visual y calidad de PDFs para Gate 2."
    )
    parser.add_argument("pdf_path", type=str, help="Ruta al archivo PDF a inspeccionar")
    parser.add_argument(
        "--budget", "-b", type=int, default=None,
        help="Presupuesto máximo de páginas físicas permitido (por defecto: 2)"
    )
    parser.add_argument(
        "--draft", "-d", type=str, default=None,
        help="Ruta al borrador .yaml/.json de origen para extraer presupuesto y contexto"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Retorna el reporte de auditoría en formato estructurado JSON"
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Modo estricto: convierte cualquier advertencia menor en fallo formal"
    )

    args = parser.parse_args()
    pdf_file = Path(args.pdf_path)

    budget = args.budget
    if budget is None and args.draft:
        draft_path = Path(args.draft)
        if draft_path.exists():
            try:
                with open(draft_path, "r", encoding="utf-8") as f:
                    if draft_path.suffix in (".yaml", ".yml"):
                        ddata = yaml.safe_load(f)
                    else:
                        ddata = json.load(f)
                budget = ddata.get("metadata", {}).get("page_budget") or ddata.get("page_budget")
            except Exception:
                pass

    if budget is None:
        budget = 2  # Estándar escolar predeterminado: 1 hoja anverso y reverso

    auditor = LayoutAuditor(default_budget=budget)
    report = auditor.audit_pdf(pdf_file, page_budget=budget, strict=args.strict)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        if report.get("status") == "ERROR":
            sys.exit(2)
        elif report.get("status") == "FAIL":
            sys.exit(1)
        else:
            sys.exit(0)

    # Salida estándar legible para terminal
    print("=" * 65)
    print("  AUDITORÍA DE LAYOUT VISUAL Y CALIDAD DE MAQUETACIÓN (Gate 2)")
    print("=" * 65)
    print(f"Archivo PDF:   {report.get('pdf_path')}")
    print(f"Páginas:       {report.get('total_pages', 0)} / Máximo permitido: {report.get('page_budget', 'N/A')}")
    
    status = report.get("status", "UNKNOWN")
    status_str = f"[{status}]"
    if status == "PASS":
        print(f"Dictamen:      \033[92m{status_str} Aprobado para impresión y aula\033[0m")
    else:
        print(f"Dictamen:      \033[91m{status_str} Anomalías de maquetación detectadas\033[0m")

    metrics = report.get("metrics", {})
    pages = metrics.get("pages", [])
    if pages:
        print("\nDistribución de Caracteres por Página:")
        for p in pages:
            print(f"  - Página {p['page']}: {p['char_count']} caracteres ({p['word_count']} palabras)")
        print(f"  - Ratio de densidad última página: {metrics.get('density_ratio_last_page', 1.0) * 100:.1f}%")

    issues = report.get("issues", [])
    if issues:
        print(f"\nIncidencias Encontradas ({len(issues)}):")
        for idx, iss in enumerate(issues, start=1):
            sev = iss.get("severity", "WARNING")
            print(f"  {idx}. [{sev}] ({iss.get('type')}): {iss.get('message')}")
    else:
        print("\nNo se detectaron desbordes, preguntas partidas ni restos de comandos LaTeX.")

    print("=" * 65)

    if report.get("status") == "ERROR":
        sys.exit(2)
    elif report.get("status") == "FAIL":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
