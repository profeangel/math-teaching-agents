# Official Version Registry and Immutable Versioning Policy

This repository implements a **strict policy of immutability and version traceability**:

> [!IMPORTANT]
> **Golden Rule of Versioning (Absolute Immutability)**:
> 1. **No Overwrites or Deletions**: No prior release version is ever deleted or modified in place.
> 2. **Derivation by Copy**: Any architectural change, feature addition, or refactoring is treated as a **new semantic version (`x.y.z`)**. To modify, **the prior version is preserved in its frozen directory (`math-teaching-agents-v<x.y.z>/`) and only the active working branch is updated**.
> 3. **SemVer Criteria (`MAJOR.MINOR.PATCH`)**:
>    - **PATCH (`x.y.Z`)**: Bug fixes, prompt errata, or minor linter improvements without changing JSON schemas or data contracts.
>    - **MINOR (`x.Y.0`)**: New didactic functionalities, new subagents, new mathematical verifiers, semantic evaluators, or national curriculum adapters without breaking backward compatibility.
>    - **MAJOR (`X.0.0`)**: Structural changes in core schemas (`assessment-spec.json`, `didactic-unit.json`) or FSM orchestration protocols.

---

## Version Catalog

| Version | Directory | State | Tests | Milestone / Highlights |
| :--- | :--- | :---: | :---: | :--- |
| **`v0.8.1`** | [`math-teaching-agents/`](.) | **Active (Current)** | 80/80 (100% green) | **Pedagogical Reality & Visual Layout Auditor**: Visual PDF layout auditor (`tools/audit_pdf_layout.py`) in Gate 2, Problem-Solving 5-moment framework (Isoda & Olfos 2009), Out-of-the-Box classroom materials intake, procedural fluency balance, and Lazy On-Demand Answer Key. |
| **`v0.8.0`** | [`../math-teaching-agents-v0.8.0-en/`](../math-teaching-agents-v0.8.0-en/) | Frozen | 76/76 (100% green) | **The Synthesis Release**: Full fusion of didactic richness and executable Python engine. Integrates Universal Meta-Standard (`AGENTS.md`, `CLAUDE.md`, `.cursor/rules/`), 3 Canonical Skills (`math-didactic-unit`, `math-assessment`, `math-dynamic-visualizer`), `LLM-as-a-Judge` semantic evaluator (`pedagogical_judge.py`), and 76 passing tests. |
| **`v0.7.0`** | [`../math-teaching-agents-v0.7.0/`](../math-teaching-agents-v0.7.0/) | Frozen | 68/68 (100% green) | **Engine & Invariants Release**: Executable Python engine, SymPy CAS, geometric & probabilistic invariants, Two-Stage Gatekeeper, Human-in-the-Loop, and 68 tests. |
| **`v0.1.0`** | [`../math-teaching-agents-v0.1.0/`](../math-teaching-agents-v0.1.0/) | Frozen | Foundational | **Genesis Release**: Original declarative multi-agent architecture with 14 teaching roles, didactic frameworks (APOS, EOS, TDS, Duval), and core specifications. |
