"""
test_skills_and_metastandard.py
Pruebas para certificar la conformidad con el Meta-Estándar Universal
y las Skills Canónicas en .agents/skills/.
"""

from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent

def test_metastandard_files_exist():
    assert (ROOT / "AGENTS.md").exists()
    assert (ROOT / "CLAUDE.md").exists()
    assert (ROOT / "CONVENTIONS.md").exists()
    assert (ROOT / ".cursor" / "rules" / "core.mdc").exists()
    assert (ROOT / ".cursor" / "rules" / "math-teaching.mdc").exists()

def test_skills_canonical_structure():
    skills_dir = ROOT / ".agents" / "skills"
    assert skills_dir.exists()
    
    expected_skills = ["math-didactic-unit", "math-assessment", "math-dynamic-visualizer"]
    for skill_name in expected_skills:
        skill_file = skills_dir / skill_name / "SKILL.md"
        assert skill_file.exists(), f"Falta SKILL.md en {skill_name}"
        
        content = skill_file.read_text(encoding="utf-8")
        assert content.startswith("---")
        parts = content.split("---")
        assert len(parts) >= 3
        
        frontmatter = yaml.safe_load(parts[1])
        assert "name" in frontmatter
        assert "description" in frontmatter
        assert "NO USAR" in frontmatter["description"], f"Falta disparador negativo en {skill_name}"
        assert (skills_dir / skill_name / "references").is_dir(), f"Falta references/ en {skill_name}"
        assert (skills_dir / skill_name / "examples").is_dir(), f"Falta examples/ en {skill_name}"

def test_all_frameworks_present():
    fw_dir = ROOT / "frameworks"
    assert (fw_dir / "brousseau-tsd.yaml").exists()
    assert (fw_dir / "dubinsky-apoe.yaml").exists()
    assert (fw_dir / "duval-trrs.yaml").exists()
    assert (fw_dir / "godino-eos.yaml").exists()
    assert (fw_dir / "isoda-olfos-resolucion-problemas.yaml").exists()

def test_all_curriculums_present():
    curr_dir = ROOT / "curriculums"
    assert (curr_dir / "chile-mineduc.yaml").exists()
    assert (curr_dir / "spain-lomloe.yaml").exists()
    assert (curr_dir / "mexico-nem.yaml").exists()
    assert (curr_dir / "colombia-men.yaml").exists()
    assert (curr_dir / "international-standard.yaml").exists()
