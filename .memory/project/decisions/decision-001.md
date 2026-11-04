# Decision 001 - Implement drift report fixes

**Date:** 2026-11-03
**Review by:** 2027-02-01
**Status:** Active

**Decision:** Implement the fixes for findings D1–D12 in `docs/drift-report.md` so the position-builder agent, `docs/prd-positions.md` and `docs/rubric-positions.md` agree with each other and with the tests.

**Rationale:** The drift report found 12 places where the agent, PRD, rubric and test disagree, including a high-severity contradiction (D1) where an honest run that reports unverified scenarios can never pass the pytest gate. The agent also still requires real Lichess games and WebFetch access (D2), even though that requirement was dropped, so it wastes network calls and attempts on a rule nobody enforces. Fixing the docs and agent against the PRD, rubric and test as the authoritative sources removes these conflicts with mostly documentation changes.

**Alternatives rejected:** Leaving the drift unfixed was ruled out because the agent would keep following stale rules and the D1 gate would keep failing honest runs.

**Progress (2026-11-04):** Fixes applied, not yet committed. Choices made by the user:
- D1: a run with an unverified scenario is an honest fail. Only the PRD and rubric changed; the test is unchanged. Making the test xfail missing scenarios was rejected.
- D2: modified rather than applied as written. Lichess is an optional fallback when no realistic constructed position fits. It is no longer required, and constructed positions are allowed. The agent keeps `WebFetch`, and the `lichess.org` allow in `settings.json` stays.
- D9: attempt counts are required for every scenario; going over 3 attempts scores Level 1 on Report Completeness.
- D4 and D12 no longer apply: the 2026-11-02 revert of the agent to v0.2.0 (commit 2b23729) removed the lines they cited. The agent is now v0.4.0.
- Still open: re-run the drift-investigator to confirm, and decide whether to commit `docs/drift-report.md` and the handoff.