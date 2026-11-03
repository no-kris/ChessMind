# Decision 001 - Implement drift report fixes

**Date:** 2026-11-03
**Review by:** 2027-02-01
**Status:** Active

**Decision:** Implement the fixes for findings D1–D12 in `docs/drift-report.md` so the position-builder agent, `docs/prd-positions.md` and `docs/rubric-positions.md` agree with each other and with the tests.

**Rationale:** The drift report found 12 places where the agent, PRD, rubric and test disagree, including a high-severity contradiction (D1) where an honest run that reports unverified scenarios can never pass the pytest gate. The agent also still requires real Lichess games and WebFetch access (D2), even though that requirement was dropped, so it wastes network calls and attempts on a rule nobody enforces. Fixing the docs and agent against the PRD, rubric and test as the authoritative sources removes these conflicts with mostly documentation changes.

**Alternatives rejected:** Leaving the drift unfixed was ruled out because the agent would keep following stale rules and the D1 gate would keep failing honest runs.