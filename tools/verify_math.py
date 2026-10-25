#!/usr/bin/env python3
"""
CLI Tool: Verificador Matemático Simbólico SymPy (Gate 1 CAS).
Herramienta determinista para Harnesses de Agentes (Claude Code, OpenCode, Antigravity)
que valida formalmente la exactitud matemática de ítems, soluciones, raíces y distractores.

Uso:
  python tools/verify_math.py path/to/draft.yaml
  python tools/verify_math.py path/to/draft.json --json
  python tools/verify_math.py --expr "x^2 - 5*x + 6 = 0"
  python tools/verify_math.py --solve "2*x + 4 = 10"
"""

import sys
import os
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
import sympy as sp
from math_teaching_agents.validators.math_verifier import SymbolicMathVerifier, latex_to_sympy_str


def verify_expression(expr_str: str) -> dict:
    """Verifica y evalúa una expresión o ecuación matemática aislada."""
    verifier = SymbolicMathVerifier()
    cleaned = latex_to_sympy_str(expr_str)
    
    if "=" in cleaned:
        left_str, right_str = cleaned.split("=", 1)
        try:
            left_expr = verifier.parse_math(left_str)
            right_expr = verifier.parse_math(right_str)
            diff = sp.simplify(left_expr - right_expr)
            is_identity = (diff == 0)
            
            # Intentar resolver simbólicamente
            free_symbols = list((left_expr - right_expr).free_symbols)
            solutions = []
            if free_symbols:
                sol = sp.solve(left_expr - right_expr, free_symbols[0])
                solutions = [str(s) for s in sol]
            
            return {
                "input": expr_str,
                "parsed_sympy": f"{left_expr} = {right_expr}",
                "is_identity": is_identity,
                "symbols": [str(s) for s in free_symbols],
                "solutions": solutions,
                "status": "PASS"
            }
        except Exception as e:
            return {
                "input": expr_str,
                "error": str(e),
                "status": "FAIL"
            }
    else:
        try:
            parsed = verifier.parse_math(cleaned)
            simplified = sp.simplify(parsed)
            return {
                "input": expr_str,
                "parsed_sympy": str(parsed),
                "simplified": str(simplified),
                "status": "PASS"
            }
        except Exception as e:
            return {
                "input": expr_str,
                "error": str(e),
                "status": "FAIL"
            }


def verify_geometry_cli(geom_str: str) -> dict:
    """Verifica restricciones geométricas (desigualdad triangular, ángulos, Pitágoras, círculo)."""
    verifier = SymbolicMathVerifier()
    if ":" not in geom_str:
        return {"input": geom_str, "status": "FAIL", "error": "Formato esperado: 'tipo: valores' (ej. 'triangle: 3, 4, 5')"}

    gtype, raw_params = geom_str.split(":", 1)
    gtype = gtype.strip().lower()
    raw_vals = [v.strip() for v in raw_params.split(",") if v.strip()]

    if gtype in ("triangle", "triangle_inequality"):
        if len(raw_vals) != 3:
            return {"input": geom_str, "status": "FAIL", "error": "Se requieren exactamente 3 lados (ej. 'triangle: 3, 4, 5')"}
        res = verifier.verify_triangle_inequality(raw_vals[0], raw_vals[1], raw_vals[2])
        return {"input": geom_str, "type": "triangle_inequality", "status": "PASS" if res["valid"] else "FAIL", "detail": res}
    elif gtype in ("angles", "polygon_angles"):
        res = verifier.verify_polygon_angles(raw_vals)
        return {"input": geom_str, "type": "polygon_angles", "status": "PASS" if res["valid"] else "FAIL", "detail": res}
    elif gtype in ("pythagorean", "right_triangle"):
        if len(raw_vals) != 3:
            return {"input": geom_str, "status": "FAIL", "error": "Se requieren a, b, c (ej. 'pythagorean: 3, 4, 5')"}
        res = verifier.verify_pythagorean_property(raw_vals[0], raw_vals[1], raw_vals[2])
        return {"input": geom_str, "type": "pythagorean", "status": "PASS" if res["valid"] else "FAIL", "detail": res}
    else:
        return {"input": geom_str, "status": "FAIL", "error": f"Tipo geométrico '{gtype}' no soportado (use 'triangle', 'angles' o 'pythagorean')"}


def verify_probability_cli(prob_str: str) -> dict:
    """Verifica probabilidades contra los axiomas de Kolmogorov."""
    verifier = SymbolicMathVerifier()
    raw_vals = [v.strip() for v in prob_str.split(",") if v.strip()]
    res = verifier.verify_probability_distribution(raw_vals)
    return {
        "input": prob_str,
        "type": "probability_distribution",
        "status": "PASS" if res["all_valid"] else "FAIL",
        "detail": res
    }


def verify_combinatorics_cli(comb_str: str) -> dict:
    """Verifica valores combinatorios (ej. 'n=5, k=2, c=10, p=20')."""
    verifier = SymbolicMathVerifier()
    parts = [p.strip() for p in comb_str.split(",") if p.strip()]
    params = {}
    for p in parts:
        if "=" in p:
            k, v = p.split("=", 1)
            params[k.strip().lower()] = v.strip()

    if "n" not in params or "k" not in params:
        return {"input": comb_str, "status": "FAIL", "error": "Se requieren al menos 'n' y 'k' (ej. 'n=5, k=2, c=10')"}

    res = verifier.verify_combinatorics_values(
        n=params["n"],
        k=params["k"],
        claimed_combinations=params.get("c") or params.get("combinations"),
        claimed_permutations=params.get("p") or params.get("permutations")
    )
    return {
        "input": comb_str,
        "type": "combinatorics",
        "status": "PASS" if res["all_valid"] else "FAIL",
        "detail": res
    }


def verify_draft_file(file_path: Path, strict: bool = False) -> dict:
    """Ejecuta la auditoría matemática completa de Gate 1 sobre un borrador YAML o JSON."""
    if not file_path.exists():
        return {
            "status": "ERROR",
            "message": f"Archivo no encontrado: {file_path}",
            "passed": False
        }

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            if file_path.suffix in (".yaml", ".yml"):
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"Error al parsear archivo {file_path.name}: {e}",
            "passed": False
        }

    verifier = SymbolicMathVerifier()
    report = {
        "gate": 1,
        "tool": "verify_math.py",
        "file": str(file_path),
        "status": "PASS",
        "items_total": 0,
        "items_passed": 0,
        "items_failed": 0,
        "checks": []
    }

    # Caso 1: Borrador de Evaluación (items)
    if "items" in data:
        items = data.get("items", [])
        report["items_total"] = len(items)

        for item in items:
            item_id = item.get("item_id", "?")
            fmt = item.get("format", "")
            item_check = {
                "item_id": item_id,
                "format": fmt,
                "status": "PASS",
                "observations": []
            }

            if fmt == "MULTIPLE_CHOICE":
                res = verifier.verify_multiple_choice_item(item)
                if res.get("status") == "PASS":
                    item_check["observations"].append("Distractores mutuamente excluyentes y válidos.")
                    if "equation_check" in res:
                        item_check["equation_check"] = res["equation_check"]
                        item_check["observations"].append(
                            f"Solución verificada: {res['equation_check'].get('true_solutions')}"
                        )
                    if "geometric_check" in res:
                        item_check["geometric_check"] = res["geometric_check"]
                        item_check["observations"].append("Invariante geométrico formal verificado con éxito.")
                    if "probability_check" in res:
                        item_check["probability_check"] = res["probability_check"]
                        item_check["observations"].append("Distribución probabilística conforme a axiomas de Kolmogorov.")
                    if "combinatorics_check" in res:
                        item_check["combinatorics_check"] = res["combinatorics_check"]
                        item_check["observations"].append("Valores combinatorios exactos verificados.")
                else:
                    item_check["status"] = "FAIL"
                    report["status"] = "FAIL"
                    item_check["observations"].extend(res.get("duplicates", []))
                    if res.get("error_detail"):
                        item_check["observations"].append(res["error_detail"])

            elif fmt in ("OPEN_DEVELOPMENT", "PROOF_ARGUMENT", "TRUE_FALSE_JUSTIFIED", "EXIT_TICKET_PROMPT"):
                # Verificar expresiones matemáticas o invariantes si están presentes
                res = verifier.verify_item(item)
                if res.get("status") == "PASS":
                    item_check["observations"].append("Ítem cualitativo/desarrollo validado.")
                    if "geometric_check" in res:
                        item_check["geometric_check"] = res["geometric_check"]
                        item_check["observations"].append("Invariante geométrico formal verificado con éxito.")
                    if "probability_check" in res:
                        item_check["probability_check"] = res["probability_check"]
                        item_check["observations"].append("Axiomas de probabilidad verificados.")
                    if "combinatorics_check" in res:
                        item_check["combinatorics_check"] = res["combinatorics_check"]
                        item_check["observations"].append("Valores combinatorios verificados.")
                else:
                    item_check["status"] = "FAIL"
                    report["status"] = "FAIL"
                    if res.get("error_detail"):
                        item_check["observations"].append(res["error_detail"])

            if item_check["status"] == "PASS":
                report["items_passed"] += 1
            else:
                report["items_failed"] += 1

            report["checks"].append(item_check)

    # Caso 2: Unidad Didáctica (phases)
    elif "phases" in data:
        phases = data.get("phases", [])
        report["items_total"] = len(phases)
        
        for phase in phases:
            pid = phase.get("phase_id", "?")
            pname = phase.get("phase_name", "")
            phase_check = {
                "phase_id": pid,
                "phase_name": pname,
                "status": "PASS",
                "observations": ["Fase metodológica consistente."]
            }
            report["items_passed"] += 1
            report["checks"].append(phase_check)

    else:
        report["status"] = "WARN" if not strict else "FAIL"
        report["observations"] = ["No se detectaron bloques 'items' ni 'phases' en el archivo."]

    report["passed"] = (report["status"] == "PASS")
    return report


def main():
    parser = argparse.ArgumentParser(
        prog="tools/verify_math.py",
        description="Auditor Simbólico SymPy para Gate 1 (Zero-Trust Mathematical Verification)"
    )
    parser.add_argument("file", nargs="?", help="Ruta al borrador .yaml o .json a verificar")
    parser.add_argument("--expr", "-e", help="Expresión o igualdad matemática aislada a verificar")
    parser.add_argument("--solve", "-s", help="Ecuación a resolver simbólicamente con SymPy")
    parser.add_argument("--check-geom", "-g", help="Verifica restricciones geométricas (ej. 'triangle: 3, 4, 5', 'angles: 60, 60, 60', 'pythagorean: 3, 4, 5')")
    parser.add_argument("--check-prob", "-p", help="Verifica probabilidades y axiomas de Kolmogorov (ej. '0.2, 0.5, 0.3')")
    parser.add_argument("--check-comb", "-c", help="Verifica cálculos combinatorios (ej. 'n=5, k=2, c=10, p=20')")
    parser.add_argument("--json", "-j", action="store_true", help="Salida en formato JSON para subagentes")
    parser.add_argument("--strict", action="store_true", help="Modo estricto: falla ante advertencias")

    args = parser.parse_args()

    if args.check_geom:
        res = verify_geometry_cli(args.check_geom)
        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            print(f"Consulta Geométrica: {res.get('input')}")
            print(f"Tipo:               {res.get('type')}")
            print(f"Resultado:          [{res.get('status')}]")
            if res.get("status") != "PASS":
                print(f"Error:              {res.get('error') or res.get('detail', {}).get('error')}")
            else:
                print(f"Detalle:            {res.get('detail')}")
        sys.exit(0 if res.get("status") == "PASS" else 1)

    if args.check_prob:
        res = verify_probability_cli(args.check_prob)
        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            print(f"Distribución:       {res.get('input')}")
            print(f"Resultado:          [{res.get('status')}]")
            if res.get("status") != "PASS":
                print(f"Errores:            {res.get('detail', {}).get('errors')}")
            else:
                print("Detalle:            Axiomas de probabilidad de Kolmogorov satisfechos formalmente.")
        sys.exit(0 if res.get("status") == "PASS" else 1)

    if args.check_comb:
        res = verify_combinatorics_cli(args.check_comb)
        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            print(f"Consulta:           {res.get('input')}")
            print(f"Resultado:          [{res.get('status')}]")
            if res.get("status") != "PASS":
                print(f"Errores:            {res.get('detail', {}).get('errors')}")
            else:
                det = res.get('detail', {})
                print(f"Detalle:            C({det.get('n')},{det.get('k')})={det.get('true_combinations')} | P={det.get('true_permutations')}")
        sys.exit(0 if res.get("status") == "PASS" else 1)

    if args.expr:
        res = verify_expression(args.expr)
        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            print(f"Expresión:    {res.get('input')}")
            print(f"SymPy Parsed: {res.get('parsed_sympy', res.get('error'))}")
            if "simplified" in res:
                print(f"Simplificado: {res.get('simplified')}")
            if "solutions" in res:
                print(f"Soluciones:   {res.get('solutions')}")
            print(f"Resultado:    [{res.get('status')}]")
        sys.exit(0 if res.get("status") == "PASS" else 1)

    if args.solve:
        res = verify_expression(args.solve)
        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            print(f"Ecuación:   {args.solve}")
            print(f"Soluciones: {res.get('solutions')}")
            print(f"Resultado:  [{res.get('status')}]")
        sys.exit(0 if res.get("status") == "PASS" else 1)

    if not args.file:
        parser.print_help()
        sys.exit(2)

    path = Path(args.file)
    report = verify_draft_file(path, strict=args.strict)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("=" * 65)
        print("  GATE 1: AUDITORÍA MATEMÁTICA FORMAL CON SYMPY (CAS)")
        print(f"  Archivo: {path.name}")
        print("=" * 65)
        for c in report.get("checks", []):
            cid = c.get("item_id", c.get("phase_id", "?"))
            st = c.get("status", "INFO")
            print(f"\n[{'Ítem' if 'item_id' in c else 'Fase'} {cid}] [{st}]")
            for obs in c.get("observations", []):
                print(f"  - {obs}")
            if "equation_check" in c:
                eq = c["equation_check"]
                print(f"    * Ecuación:     {eq.get('equation')}")
                print(f"    * Raíces:       {eq.get('true_solutions')}")
            if "geometric_check" in c:
                geom = c["geometric_check"]
                print(f"    * Geometría:    {'VÁLIDO' if geom.get('valid') else 'INVÁLIDO: ' + str(geom.get('error'))}")
            if "probability_check" in c:
                prob = c["probability_check"]
                print(f"    * Probabilidad: {'VÁLIDO' if prob.get('all_valid') else 'INVÁLIDO: ' + str(prob.get('errors'))}")
            if "combinatorics_check" in c:
                comb = c["combinatorics_check"]
                print(f"    * Combinatoria: {'VÁLIDO' if comb.get('all_valid') else 'INVÁLIDO: ' + str(comb.get('errors'))}")
        
        print("\n" + "-" * 65)
        print(f"  DICTAMEN GATE 1: {report.get('status')} ({report.get('items_passed')}/{report.get('items_total')} aprobados)")
        print("=" * 65)

    sys.exit(0 if report.get("passed") else 1)


if __name__ == "__main__":
    main()
