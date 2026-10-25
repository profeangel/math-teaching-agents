---
name: math-didactic-unit
description: >-
  Design of learning sequences, problem situations, and didactic units in mathematics grounded in plural, declarative theoretical frameworks (TDS, TRRS, APOS, EOS, RME, ATD, etc.).
  Use when designing, planning, or refining lesson plans, guided inquiry sheets, didactic situations, or mathematical concept progressions under any pedagogical paradigm.
  DO NOT USE / NO USAR for solely designing multiple-choice tests or exams with scoring keys, or for general programming queries.
---

# Skill Protocol: math-didactic-unit

This skill implements an approach based on **Epistemological Pluralism and Networking of Theories (*Radford / Bikner-Ahsbahs*)**.
The system is **NOT** dogmatically tied to a single educational philosophy: the educator specifies the desired framework, and the system dynamically configures its cognitive constructs, instructional phases, and audit criteria.

---

## 1. Selection & Dynamic Substitution of Didactic Frameworks

The teacher can explicitly designate active theoretical frameworks:

| Theoretical Framework | Official Manifest | Instructional Phases Adopted | Critical Audit Focus |
| :--- | :--- | :--- | :--- |
| **Theory of Didactical Situations (TDS / TSD)** | `frameworks/brousseau-tsd.yaml` | 4 A-didactic phases: Action, Formulation, Validation, Institutionalization | Devolution and strict vigilance against Topaze & Jourdain didactic effects. |
| **Onto-Semiotic Approach (OSA / EOS)** | `frameworks/godino-eos.yaml` | Onto-semiotic configuration (Situations, Language, Concepts, Propositions, Procedures, Arguments) | Didactic Suitability (epistemic, cognitive, interactional) and resolution of semiotic conflicts. |
| **APOS Theory (Dubinsky)** | `frameworks/dubinsky-apoe.yaml` | ACE Cycle: Exploration Activities (A), Classroom Discussion (C), Exercises (E) | Genetic Decomposition: transitions from Action to Process and Encapsulation into Object. |
| **Registers of Representation (TRRS)** | `frameworks/duval-trrs.yaml` | Multi-register articulation: Graphical, Tabular, Verbal, Symbolic | Active conversion between semiotic registers (preventing purely mechanical mono-register treatment). |
| **Realistic Mathematics Education (RME)** | Dynamic / `frameworks/rme.yaml` | Horizontal Mathematization $\to$ Vertical Mathematization | Authentic phenomenological contexts and mediating progressive schematizations. |

---

## 2. "Just-in-Time" Synthesis Protocol for New Frameworks

If the educator requests a theoretical model without a pre-existing manifest in `frameworks/` (e.g., *D'Ambrosio's Ethnomathematics, Chevallard's Anthropological Theory of the Didactic - ATD, or Cantoral's Socioepistemology*):

1. **Research & Grounding**: The agent inspects foundational literature.
2. **Declarative Manifest Generation**: Synthesizes a new `frameworks/<framework-id>.yaml` adhering to the standard schema:
   - `kflm_cognitive_model`: learning premise and epistemological barriers according to the theory.
   - `kmt_instructional_design`: instructional design phases and heuristics.
   - `audit_checklist_gate_1`: quality control criteria for Gate 1.
3. **Active Substitution**: The agent adopts the phases and terminology in `schemas/didactic-unit.json` (`phases[*].phase_name`), replacing prior defaults.

---

## 3. Progressive Disclosure (On-Demand Loading)

Avoid overloading the initial context:
* Inspect only the specific `frameworks/<selected-framework>.yaml` requested.
* Inspect only the relevant national or international curriculum adapter in `curriculums/<curriculum>.yaml`.

---

## 4. Contract Validation and Compilation

1. **Draft Validation**:
   Check that the document complies with the schema:
   ```bash
   python tools/validate.py drafts/my_unit.yaml --json
   ```
2. **Semantic Audit**:
   Execute the pedagogical evaluator against the active framework's audit criteria:
   ```bash
   python tools/pedagogical_judge.py drafts/my_unit.yaml --framework brousseau-tsd --json
   ```
3. **Typesetting & Rendering**:
   Compile to clean Typst or LaTeX layout:
   ```bash
   python tools/render.py drafts/my_unit.yaml --format typst --compile --json
   ```
