# Contribution Guidelines (`CONTRIBUTING.md`)

Thank you for your interest in contributing to this multi-agent mathematics education ecosystem!

This project is built on a decoupled, modular architecture so mathematics educators, didactic researchers, and software engineers can extend the system without breaking its core verification invariants.

---

## 1. Adding a New Theoretical Framework (`frameworks/*.yaml`)

You do not need to write Python code or build new agents to incorporate a didactic framework. Simply add a YAML file under `frameworks/`:

1. Create `frameworks/my-framework.yaml`.
2. Define the four mandatory blocks:
   - `kflm_cognitive_model`: Mental model of the student and theoretical explanation of cognitive obstacles or misconceptions.
   - `kmt_instructional_design`: Teaching phases and design heuristics for learning situations.
   - `audit_checklist_gate_1`: Critical verification checkpoints that the semantic auditor (Gate 1) must enforce.
   - `networking`: Compatible and incompatible didactic frameworks (*Radford / Bikner-Ahsbahs*).
3. Submit a Pull Request documenting the academic literature citations supporting the theoretical profile.

---

## 2. Adding a National or Regional Curriculum Adapter (`curriculums/*.yaml`)

To adapt the system to the terminology and standards of a new country or state:

1. Create `curriculums/country-system.yaml`.
2. Map official terminology under `thesaurus_mappings`:
   - Grade level equivalences (e.g., Primary, Middle School, High School, Secondary, Sixth Form).
   - Official mathematical strands and domain names.
   - Curricular standards terminology (e.g., "Learning Objectives", "Essential Knowledge", "Competencies").
   - Grading scales and benchmark examinations.
3. Include the official decree, statutory guidance, or syllabus version reference.

---

## 3. Adding New Typesetting Templates (`templates/`)

* LaTeX templates must compile without fatal errors under modern engines such as **XeLaTeX** or **Tectonic**.
* Word templates must use the Jinja2 variables documented in `templates/word/README.md`.
* Avoid proprietary package dependencies or fonts with restrictive commercial licenses.
* Typst templates are preferred for rapid, reproducible PDF compilation.

---

## 4. Zero-Trust Quality Policy
Any proposed changes to agent prompts or specifications in `agents/` must guarantee:
- **Preservation of Gate 1 (Fail-Fast):** Generation agents must never couple directly to visual presentation formatting.
- **Mathematical & Didactic Rigor:** Every generated distractor must be grounded in documented student misconceptions.
- **Full Test Passing:** Run `pytest tests/` and verify that all 76 tests pass before opening a PR.
