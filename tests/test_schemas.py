"""
Tests unitarios para la validación de schemas JSON y archivos declarativos YAML.
"""

from pathlib import Path
from math_teaching_agents.validators.schema_validator import SchemaValidator


def test_json_schemas_validity():
    root = Path(__file__).resolve().parents[1]
    validator = SchemaValidator(root)
    results = validator.validate_all_json_schemas()

    assert len(results) >= 2, "Debe haber al menos 2 esquemas JSON en schemas/"
    for name, ok, msg in results:
        assert ok, f"Error en schema {name}: {msg}"


def test_curriculums_validity():
    root = Path(__file__).resolve().parents[1]
    validator = SchemaValidator(root)
    results = validator.validate_curriculums()

    assert len(results) >= 5, "Debe haber al menos 5 currículos en curriculums/"
    names = [r[0] for r in results]
    assert "mexico-nem.yaml" in names
    assert "colombia-men.yaml" in names
    assert "chile-mineduc.yaml" in names
    for name, ok, msg in results:
        assert ok, f"Error en currículo {name}: {msg}"


def test_frameworks_validity():
    root = Path(__file__).resolve().parents[1]
    validator = SchemaValidator(root)
    results = validator.validate_frameworks()

    assert len(results) >= 4, "Debe haber al menos 4 marcos didácticos en frameworks/"
    names = [r[0] for r in results]
    assert "godino-eos.yaml" in names
    assert "duval-trrs.yaml" in names
    for name, ok, msg in results:
        assert ok, f"Error en marco teórico {name}: {msg}"
