"""
Validador de esquemas JSON, marcos didácticos YAML y adaptadores curriculares.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
import yaml
import jsonschema
from jsonschema import Draft202012Validator


class SchemaValidator:
    """Valida la integridad de contratos y archivos declarativos del ecosistema."""

    def __init__(self, root_dir: Path):
        self.root_dir = Path(root_dir)
        self.schemas_dir = self.root_dir / "schemas"
        self.curriculums_dir = self.root_dir / "curriculums"
        self.frameworks_dir = self.root_dir / "frameworks"

    def validate_all_json_schemas(self) -> List[Tuple[str, bool, str]]:
        """Valida que todos los schemas JSON sean metarreglas válidas Draft 2020-12."""
        results = []
        if not self.schemas_dir.exists():
            return [("schemas/", False, "Directorio no encontrado")]

        for schema_file in self.schemas_dir.glob("*.json"):
            try:
                with open(schema_file, "r", encoding="utf-8") as f:
                    schema_data = json.load(f)
                Draft202012Validator.check_schema(schema_data)
                results.append((schema_file.name, True, "Schema JSON válido (Draft 2020-12)"))
            except Exception as e:
                results.append((schema_file.name, False, str(e)))
        return results

    def validate_curriculums(self) -> List[Tuple[str, bool, str]]:
        """Valida que los adaptadores curriculares contengan los bloques canónicos requeridos."""
        results = []
        required_keys = ["id", "country_or_entity", "language", "thesaurus_mappings"]
        for curr_file in self.curriculums_dir.glob("*.yaml"):
            try:
                with open(curr_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                missing = [k for k in required_keys if k not in data]
                if missing:
                    results.append((curr_file.name, False, f"Faltan claves obligatorias: {missing}"))
                else:
                    results.append((curr_file.name, True, f"Perfil válido ({data.get('country_or_entity')})"))
            except Exception as e:
                results.append((curr_file.name, False, str(e)))
        return results

    def validate_frameworks(self) -> List[Tuple[str, bool, str]]:
        """Valida que los marcos didácticos tengan los bloques de investigación requeridos."""
        results = []
        required_keys = [
            "id", "nombre", "autor_principal",
            "kflm_cognitive_model", "kmt_instructional_design",
            "audit_checklist_gate_1"
        ]
        for fw_file in self.frameworks_dir.glob("*.yaml"):
            try:
                with open(fw_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                missing = [k for k in required_keys if k not in data]
                if missing:
                    results.append((fw_file.name, False, f"Faltan claves obligatorias: {missing}"))
                else:
                    results.append((fw_file.name, True, f"Marco válido ({data.get('nombre')})"))
            except Exception as e:
                results.append((fw_file.name, False, str(e)))
        return results

    def validate_instance(self, instance_data: dict, schema_name: str = "assessment-spec.json") -> Tuple[bool, List[str]]:
        """Valida un documento (ej. borrador de evaluación) contra el schema oficial."""
        schema_path = self.schemas_dir / schema_name
        if not schema_path.exists():
            return False, [f"No se encontró el schema: {schema_name}"]

        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        validator = Draft202012Validator(schema)
        errors = [err.message for err in validator.iter_errors(instance_data)]
        return len(errors) == 0, errors
