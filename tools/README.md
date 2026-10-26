# Deterministic CLI Tools (`tools/`)

This directory contains deterministic command-line tools designed for direct invocation by **AI Agent Harnesses** (Claude Code, OpenCode, Antigravity, Cursor, Roo-Code) or by developers and educators from their terminal.

By decoupling mathematical validation and document typesetting into pure CLI tools, subagents can perform millisecond-level verification via terminal commands (`bash` or `powershell`), eliminating token waste and guaranteeing absolute mathematical rigor.

---

## 1. Available Tools

| Script | Purpose / Gate | Formats | Example Command |
| :--- | :--- | :--- | :--- |
| [`verify_math.py`](verify_math.py) | **Gate 1:** Formal mathematical CAS audit with SymPy. Detects duplicate distractors, wrong roots, and algebraic inconsistencies. | `.yaml`, `.json`, `--expr` | `python tools/verify_math.py draft.yaml --json` |
| [`validate.py`](validate.py) | JSON Schema Draft 2020-12 contract validator for assessments and didactic units. | `.yaml`, `.json`, `--all` | `python tools/validate.py draft.yaml` |
| [`render.py`](render.py) | **Gate 2:** Multi-format renderer and automated PDF compiler. | Typst, LaTeX, Moodle XML | `python tools/render.py draft.yaml --format typst --compile` |
| [`pedagogical_judge.py`](pedagogical_judge.py) | Semantic didactic evaluator implementing LLM-as-a-Judge against 4D pedagogical rubrics. | `.yaml`, `.json` | `python tools/pedagogical_judge.py draft.yaml --framework brousseau-tsd --json` |

---

## 2. Usage Guide for Agents and Developers

### A. `tools/verify_math.py` (SymPy CAS Auditor)

Verifies that equations have exact solutions, invariants hold, and no duplicate or algebraically equivalent options exist (e.g., detecting that $\frac{2}{4}$ is identical to $0.5$).

```bash
# Audit a complete assessment draft:
python tools/verify_math.py drafts/assessment.yaml

# Structured JSON output for harness subagents:
python tools/verify_math.py drafts/assessment.yaml --json

# Verify an isolated mathematical equality or identity:
python tools/verify_math.py --expr "x^2 - 5*x + 6 = 0"

# Symbolically solve an equation:
python tools/verify_math.py --solve "2*x + 4 = 10"

# Audit geometric invariants (triangle inequality, angle sums, Pythagorean theorem):
python tools/verify_math.py --check-geom "triangle: 3, 4, 5"
python tools/verify_math.py --check-geom "angles: 60, 60, 60"
python tools/verify_math.py --check-geom "pythagorean: 5, 12, 13"

# Audit Kolmogorov probability axioms:
python tools/verify_math.py --check-prob "0.2, 0.5, 0.3"

# Audit combinatorics calculations:
python tools/verify_math.py --check-comb "n=5, k=2, c=10, p=20"
```

**Exit Codes:**
* `0`: All mathematical checks passed (`PASS`).
* `1`: Verification failure (e.g., duplicate distractor, incorrect root, invariant violated).
* `2`: Syntax error or file not found.

---

### B. `tools/validate.py` (Schema Validator)

Ensures that agent-generated drafts strictly respect the data contracts defined in `schemas/`.

```bash
# Validate a draft against its schema (auto-detects assessment vs didactic-unit):
python tools/validate.py drafts/my_unit.yaml

# Explicitly validate against the didactic-unit schema:
python tools/validate.py drafts/my_unit.yaml --schema didactic-unit

# Audit all schemas, curriculums, and frameworks in the repository:
python tools/validate.py --all

# JSON output for agent processing:
python tools/validate.py drafts/my_unit.yaml --json
```

---

### C. `tools/render.py` (Multi-Format Renderer & Compiler)

Transforms an approved neutral semantic draft into a typeset document and compiles it to PDF when requested.

```bash
# Render to Typst (.typ) and compile instantly to PDF:
python tools/render.py drafts/assessment.yaml --format typst --compile

# Render to LaTeX (.tex):
python tools/render.py drafts/assessment.yaml --format latex -o output/assessment.tex

# Export to Moodle XML for batch LMS import (Moodle, Canvas, Blackboard):
python tools/render.py drafts/assessment.yaml --format moodle -o question_bank.xml

# JSON output with compilation status and artifact paths:
python tools/render.py drafts/assessment.yaml --format typst --compile --json
```

---


### D. `tools/audit_pdf_layout.py` (Visual PDF Layout Auditor - Gate 2)

Inspects compiled binary PDFs via `pypdf` to prevent the "exit-code 0 fallacy":
- Detects orphan overflows (< 20% character density on the final page).
- Detects evaluation reactivos/items split across page breaks (e.g. options A/B on page 1 and C/D on page 2).
- Detects orphan section headers severed at the page bottom.
- Detects unparsed LaTeX syntax bleed in Typst (`\text{}`, `\circ`, `\frac{}`).
- Enforces strict physical page budget (default: 2 pages / 1 physical sheet printed double-sided).

```bash
# Audit a compiled PDF:
python tools/audit_pdf_layout.py output/assessment.pdf

# Audit with custom physical page budget:
python tools/audit_pdf_layout.py output/worksheet.pdf --budget 2

# Structured JSON output for agent harnesses:
python tools/audit_pdf_layout.py output/assessment.pdf --json
```

**Exit Codes:**
* `0`: PASS. The PDF satisfies all physical layout and typography constraints.
* `1`: FAIL. Layout violation detected (orphan overflow, split reactivo, LaTeX corruption, budget exceeded).
* `2`: ERROR. File not found or corrupted PDF.

---

## 3. Harness Integration Workflow

In agent harness environments such as Claude Code or Antigravity, the `evaluator` subagent executes:
1. `python tools/validate.py <draft>`
2. `python tools/verify_math.py <draft> --json`

If both tools exit with code `0`, the `universal-format-engine` subagent executes:
3. `python tools/render.py <draft> --format typst --compile --json`
4. `python tools/audit_pdf_layout.py <rendered_pdf> --json`
