# Assessment and Psychometrics Reference Guide

1. **Data Contract Schema**:
   - `schemas/assessment-spec.json` (Validated against JSON Schema Draft 2020-12)

2. **Cognitive Distractor Models**:
   - Every distractor must map to a documented error model:
     - `linearity_illusion`: Applying direct proportionality to non-linear phenomena.
     - `sign_inversion`: Confusion in horizontal translations f(x - h) vs f(x + h).
     - `cross_term_omission`: (a + b)^2 = a^2 + b^2 (exponent distribution fallacy).
     - `denominator_sum`: Direct addition a/b + c/d = (a+c)/(b+d).

3. **Formal Verification**:
   - CAS execution: `python tools/verify_math.py drafts/<file>.yaml --json`
