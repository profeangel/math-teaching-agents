#!/usr/bin/env python3
"""
tools/pedagogical_judge.py
Herramienta CLI para evaluación pedagógica y semántica (Capa 2: LLM-as-a-Judge)
Audita borradores didácticos y evaluaciones contra Brousseau, Duval, Bloom y Förster.
"""

import sys
import os
import json
import argparse
from pathlib import Path

# UTF-8 encoding
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from math_teaching_agents.validators.pedagogical_judge import PedagogicalJudge
except ImportError as e:
    print(f"Error importando PedagogicalJudge: {e}", file=sys.stderr)
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Auditor Pedagógico Semántico (Capa 2 / LLM-as-a-Judge)")
    parser.add_argument("file", nargs="?", help="Ruta al archivo .yaml, .json, .tex o .typ a evaluar")
    parser.add_argument("--json", action="store_true", help="Salida en formato JSON estructurado")
    parser.add_argument("--sample", action="store_true", help="Ejecutar caso de prueba canónico")
    args = parser.parse_args()

    judge = PedagogicalJudge()

    if args.sample:
        sample_doc = {
            "title": "Unidad de Optimización Cuadrática",
            "phases": [
                {"name": "Acción", "stem": "Explora el área máxima cercada con 40 metros de valla en un gráfico."},
                {"name": "Formulación", "prompt": "Conjetura la relación entre el ancho x y el área total f(x). Justifica por qué."},
                {"name": "Institucionalización", "definition": "Definición formal del vértice de una parábola y su máximo."}
            ],
            "registers": ["Gráfico/Geométrico", "Algebraico", "Tabular"]
        }
        res = judge.evaluate(sample_doc)
        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            print("=== EVALUACIÓN PEDAGÓGICA (CASO DE MUESTRA) ===")
            print(f"Dictamen:        {res['status']}")
            print(f"Puntaje Total:   {res['weighted_score']} / 4.00")
            print("Observaciones:")
            for fb in res["feedback"]:
                print(f"  • {fb}")
        sys.exit(0 if res["passed"] else 1)

    if not args.file:
        parser.print_help()
        sys.exit(1)

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: Archivo no encontrado: {file_path}", file=sys.stderr)
        sys.exit(1)

    content = file_path.read_text(encoding="utf-8")
    c_type = file_path.suffix.lstrip(".").lower()
    res = judge.evaluate(content, content_type=c_type)

    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print(f"=== INFORME DE AUDITORÍA PEDAGÓGICA: {file_path.name} ===")
        print(f"Dictamen Final:      {res['status']}")
        print(f"Puntaje Ponderado:   {res['weighted_score']} / 4.00 (Mínimo: 3.00)")
        print("\nPuntajes por Dimensión:")
        for dim, sc in res["scores"].items():
            print(f"  • {dim:<26}: {sc:.1f} / 4.0")
        print("\nRetroalimentación Didáctica:")
        for fb in res["feedback"]:
            print(f"  • {fb}")
        if res.get("required_actions"):
            print("\nAcciones Requeridas para Aprobación:")
            for act in res["required_actions"]:
                print(f"  ⚠ {act}")
        print("=" * 55)

    sys.exit(0 if res["passed"] else 1)

if __name__ == "__main__":
    main()
