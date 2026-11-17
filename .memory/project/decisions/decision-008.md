# Decision 008 - Reviewer rejects and verifier failures share one 3-round budget

**Date:** 2026-11-17
**Review by:** 2027-02-15
**Status:** Active. User-confirmed 2026-11-17 ("share the limit").

**Decision:** In a TDD orchestration run, a round is one implementer
(endpoint-builder) build, and the first build is round 1. A still-red green
run (tests unchanged), a reviewer reject and a verifier FAIL each start the
next round, and all count against the same limit of 3 rounds per run. If
round 3 is still red, rejected by the reviewer or fails verification, the
orchestrator escalates to the human with the accumulated findings and stops.
Every build goes through the green re-run, G2 and review again before the
verifier runs. (Still-red routing and the G2 re-run after every build were
added 2026-11-17 when the user asked to fix the G2 note in the
orchestration diagram; they follow from "a round is one implementer
build".)

**Why:** Before this, the orchestrator capped review rounds at 3, but the
verifier skill's "max 3 rounds" didn't say whether it was a separate budget.
Separate budgets would allow up to 6 rebuilds before a human saw the run.

**Where it is written:** `.claude/agents/orchestrator.md` (stages 7, 9-10,
Loops back to), `.claude/agents/endpoint-builder.md`,
`.claude/agents/reviewer.md`, `.claude/skills/verifier/SKILL.md`,
`docs/orchestration-diagram.md`, `docs/routing-and-tool-grant-map.md`.

**Alternatives rejected:** Separate 3-round budgets for review and
verification.
