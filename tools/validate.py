#!/usr/bin/env python3
"""
CLI Tool: Validador de Contratos y Schemas Didácticos (Draft 2020-12).
Herramienta determinista para Harnesses de Agentes (Claude Code, OpenCode, Antigravity)
que valida la estructura formal de borradores (evaluaciones y unidades didácticas)
o verifica la integridad de esquemas, currículos y marcos teóricos del ecosistema.

Uso:
  python tools/validate.py path/to/draft.yaml
  python tools/validate.py path/to/draft.yaml --schema didactic-unit
  python tools/validate.py path/to/draft.yaml --json
  python tools/validate.py --all
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
from math_teaching_agents.validators.schema_validator import SchemaValidator


def detect_schema_name(data: dict, explicit_schema: str = None) -> str:
    """Infiere el esquema JSON adecuado según la estructura del documento."""
    if explicit_schema:
        if explicit_schema.endswith(".json"):
            return explicit_schema
        if explicit_schema in ("assessment", "evaluacion", "assessment-spec"):
            return "assessment-spec.json"
        if explicit_schema in ("didactic-unit", "unit", "unidad", "didactic_unit"):
            return "didactic-unit.json"
        return explicit_schema

    # Detección heurística por claves canónicas
    if "phases" in data or "didactic_phases" in data:
        return "didactic-unit.json"
    return "assessment-spec.json"


def validate_single_file(file_path: Path, explicit_schema: str = None) -> dict:
    """Valida un archivo borrador YAML o JSON contra el esquema JSON correspondiente."""
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

    schema_name = detect_schema_name(data, explicit_schema)
    validator = SchemaValidator(ROOT_DIR)
    ok, errors = validator.validate_instance(data, schema_name=schema_name)

    return {
        "tool": "validate.py",
        "file": str(file_path),
        "schema_used": schema_name,
        "status": "PASS" if ok else "FAIL",
        "passed": ok,
        "errors_count": len(errors),
        "errors": errors
    }


def validate_system_contracts() -> dict:
    """Ejecuta la auditoría completa de todos los schemas, curriculums y frameworks."""
    validator = SchemaValidator(ROOT_DIR)
    
    json_results = validator.validate_all_json_schemas()
    curr_results = validator.validate_curriculums()
    fw_results = validator.validate_frameworks()

    all_passed = (
        all(ok for _, ok, _ in json_results) and
        all(ok for _, ok, _ in curr_results) and
        all(ok for _, ok, _ in fw_results)
    )

    return {
        "tool": "validate.py",
        "scope": "system_contracts",
        "status": "PASS" if all_passed else "FAIL",
        "passed": all_passed,
        "schemas": [{"name": n, "valid": ok, "detail": msg} for n, ok, msg in json_results],
        "curriculums": [{"name": n, "valid": ok, "detail": msg} for n, ok, msg in curr_results],
        "frameworks": [{"name": n, "valid": ok, "detail": msg} for n, ok, msg in fw_results]
    }


def main():
    parser = argparse.ArgumentParser(
        prog="tools/validate.py",
        description="Validador de Contratos y Esquemas Didácticos JSON/YAML"
    )
    parser.add_argument("file", nargs="?", help="Ruta al borrador .yaml o .json a validar contra el esquema")
    parser.add_argument("--schema", "-s", help="Esquema a emplear: assessment, didactic-unit o ruta al schema")
    parser.add_argument("--all", "-a", action="store_true", help="Audita todos los schemas, currículos y marcos del repo")
    parser.add_argument("--json", "-j", action="store_true", help="Salida en formato JSON para subagentes")

    args = parser.parse_args()

    # Si se pide --all o no se provee archivo, valida los contratos del sistema
    if args.all or not args.file:
        res = validate_system_contracts()
        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            print("=" * 65)
            print("  AUDITORÍA DE CONTRATOS DIDÁCTICOS Y SCHEMAS DEL SISTEMA")
            print("=" * 65)

            print("\n[1] Esquemas JSON (Draft 2020-12):")
            for item in res["schemas"]:
                tag = "OK" if item["valid"] else "FAIL"
                print(f"  [{tag:<4}] {item['name']:<26} -> {item['detail']}")

            print("\n[2] Adaptadores Curriculares:")
            for item in res["curriculums"]:
                tag = "OK" if item["valid"] else "FAIL"
                print(f"  [{tag:<4}] {item['name']:<26} -> {item['detail']}")

            print("\n[3] Marcos Didácticos:")
            for item in res["frameworks"]:
                tag = "OK" if item["valid"] else "FAIL"
                print(f"  [{tag:<4}] {item['name']:<26} -> {item['detail']}")

            print("\n" + "-" * 65)
            print(f"  DICTAMEN GENERAL: {res['status']}")
            print("=" * 65)
        sys.exit(0 if res["passed"] else 1)

    # Validar un archivo específico
    target_path = Path(args.file)
    res = validate_single_file(target_path, explicit_schema=args.schema)

    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print("=" * 65)
        print("  VALIDACIÓN DE ESQUEMA DIDÁCTICO (Draft 2020-12)")
        print(f"  Archivo:  {target_path.name}")
        print(f"  Esquema:  {res.get('schema_used')}")
        print("=" * 65)

        if res.get("passed"):
            print("  [OK] El documento cumple estrictamente con el contrato del esquema.")
        else:
            print(f"  [FAIL] Se detectaron {res.get('errors_count')} errores de validación:")
            for err in res.get("errors", []):
                print(f"    - {err}")

        print("\n" + "-" * 65)
        print(f"  DICTAMEN: {res.get('status')}")
        print("=" * 65)

    sys.exit(0 if res.get("passed") else 1)


if __name__ == "__main__":
    main()
