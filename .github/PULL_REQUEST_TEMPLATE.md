## Description of Change
<!-- Describe the problem this Pull Request solves or the feature it introduces. -->

## Type of Contribution
- [ ] New Curriculum Adapter (`curriculums/*.yaml`)
- [ ] New Theoretical Framework (`frameworks/*.yaml`)
- [ ] New Typography Template or Output Format (`templates/`)
- [ ] Improvement to Agent Prompts / Specifications (`agents/`)
- [ ] Code / CLI / Test Suite Enhancement (`src/` or `tests/`)
- [ ] Documentation / Errata Correction

## Didactic Policy Checklist
- [ ] Preservation of Gate 1: No generation agents are coupled directly to visual presentation formatting.
- [ ] Cognitive Distractor Traceability (if applicable): Every distractor is grounded in documented student misconceptions.
- [ ] Observable Rubric Criteria: Rubrics employ empirical observable descriptors (*Förster / Brookhart*).

## Technical Verification
- [ ] Executed `math-agent validate` (or `python -m math_teaching_agents.cli validate`) successfully.
- [ ] All `pytest` tests passed (100% green).
