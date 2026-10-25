---
name: math-assessment
description: >-
  Construction of authentic mathematics assessment instruments, psychometric items with cognitive distractors, and question banks exportable to Moodle XML.
  Use when designing, calibrating, or validating quizzes, exams, rubrics, or multiple-choice questions in secondary and higher mathematics education.
  DO NOT USE / NO USAR for annual lesson plans without assessment components, or for isolated computations without pedagogical purpose.
---

# Skill Protocol: math-assessment

This skill governs the creation of assessment instruments with construct validity, diagnostic distractors, and unbreakable formal verification.

---

## 1. Golden Rules of Assessment Design

1. **Zero Arbitrary Distractors**:
   - Every incorrect option (distractor) must model a **genuine epistemological obstacle or documented cognitive error** from research literature (e.g., De Bock's illusion of linearity, sign reversals, exponent distributivity fallacies, direct fraction denominator addition).
   - Random numbers or arbitrary sign flips are strictly prohibited.
2. **Mandatory Symbolic Verification (Gate 1)**:
   - All solutions and keys must be validated with SymPy CAS before producing the rubric:
     ```bash
     python tools/verify_math.py drafts/my_assessment.yaml --json
     ```
   - The verifier automatically checks that no duplicate distractors exist and that no distractor algebraically matches the correct key.

---

## 2. Cognitive Demand Taxonomy (Anderson-Krathwohl / Bloom)

Instruments must maintain a balanced distribution across cognitive levels:
- **Level 1 (Knowledge / Recall)**: Definitions and elementary properties ($\le 20\%$).
- **Level 2 (Procedural Application)**: Standard algorithmic execution and equations ($\approx 40\%$).
- **Level 3 (Analysis & Modeling)**: Non-routine real-world contexts, justification of falsity, and optimization ($\ge 40\%$).

---

## 3. Multi-Format Output

1. **Print-Ready PDF (Typst)**:
   ```bash
   python tools/render.py drafts/my_assessment.yaml --format typst --compile --json
   ```
2. **LMS Question Bank (Moodle XML)**:
   ```bash
   python tools/render.py drafts/my_assessment.yaml --format moodle --output question_bank.xml --json
   ```
   *Note*: The exporter injects automated diagnostic feedback for each distractor into Moodle XML.

---

## 4. Verification Gate & Human Checkpoint (HITL)

1. Validate schema compliance with `python tools/validate.py`.
2. When interactive review is enabled (`--interactive-review`), submit draft to `src/math_teaching_agents/human_review.py`.
3. Any modifications made by the teacher undergo automated Gate 1 re-audit before final typesetting.
