# Decision 002 - Keep test files in a separate tests directory

**Date:** 2026-11-03
**Review by:** 2027-02-01
**Status:** Active

**Decision:** Put test files in a dedicated `tests/` directory, not next to the source files they test. In the backend this is `backend/tests/` (fixtures in `backend/tests/fixtures/`). New tests go there, not alongside modules in `backend/app/`.

**Rationale:** Not recorded. The user stated the decision without giving a reason.

**Alternatives rejected:** Placing test files alongside the source files (for example `backend/app/services/test_engine.py` or `Component.test.tsx` next to the component).

**Notes:** At the time of recording, the backend already follows this layout and the frontend has no tests yet. Where frontend tests should live (e.g. `frontend/tests/`) has not been decided.
