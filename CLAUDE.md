# CLAUDE.md - math-teaching-agents (v0.8.0)

Operating guidelines for Claude Code, terminal AI assistants, and autonomous coding agents.
The repository implements a neural-symbolic multi-agent suite for didactic design and mathematical assessment.

Master architecture and role specifications are centralized in:
@AGENTS.md

---

## 1. Immediate Validation Commands ("Checks to Run")

Before completing any code modification or instructional artifact:

```bash
# 1. Run Complete Unit Test Suite (76 green tests):
pytest tests/

# 2. Audit Schemas, Curriculums, and Theoretical Frameworks:
python tools/validate.py --all

# 3. Validate a Specific Draft (YAML/JSON) Against the Official Contract:
python tools/validate.py drafts/my_assessment.yaml --json

# 4. Symbolic CAS Verification with SymPy (Gate 1):
python tools/verify_math.py drafts/my_assessment.yaml --json
python tools/verify_math.py --solve "x**2 - 5*x + 6 = 0" --json

# 5. Instant PDF Compilation via Typst (Gate 2):
python tools/render.py drafts/my_assessment.yaml --format typst --compile --json
```

---

## 2. Strict Behavioral Invariants

1. **Zero Symbolic Hallucination**: Never calculate roots, expansions, or algebraic solutions from memory. Always invoke `tools/verify_math.py` or SymPy CAS.
2. **Typst Priority for Classroom Materials**: Use Typst (`.typ`) by default for instant PDF generation (compiles in ~100 ms without TeX Live / MiKTeX dependencies).
3. **Respect Brousseau's Didactic Phases**: Never spoon-feed formulas or procedures beforehand (strict vigilance against the Topaze Effect).
4. **Duval Multi-Register Articulation**: Every problem situation or assessment item must articulate at least two semiotic registers (graphical/geometric, tabular, verbal/contextual, algebraic/symbolic).
5. **Read-Only Adversarial Auditor**: The evaluator role (`math-auditor` / `zero-trust-evaluator`) must not modify files directly; it issues a structured `<audit_report>` for the creator to remediate (maximum 2 cycles before escalating to Human-in-the-Loop).
6. **Immutable Versioning**: Any modification or evolution must follow the SemVer policy declared in `VERSIONS.md`.
