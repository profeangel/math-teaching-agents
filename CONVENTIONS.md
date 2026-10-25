# CONVENTIONS.md - math-teaching-agents

This file serves as a reference point for Aider and terminal pair-programming tools.

Master architectural rules, the 16-agent catalog, and formal verification protocols are centralized in:
@AGENTS.md

## Key Development Guidelines
1. Zero symbolic hallucination: verify mathematics with `python tools/verify_math.py`.
2. Validate data contracts before typesetting: `python tools/validate.py`.
3. Compile with Typst (`python tools/render.py --format typst --compile`) for instant classroom-ready PDFs.
4. All code modifications must keep 100% of the `pytest tests/` test suite green (76/76 passing).
