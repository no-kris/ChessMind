# Decision 003 - Next implementation slice: in-memory game store and move endpoint

**Date:** 2026-11-04
**Review by:** 2027-02-02
**Status:** Active

**Decision:** The next implementation work is Phase 1 of `ai_chess_coach_project_plan.md` (lines 25-31): an in-memory game store plus the game and move endpoints.

**Scope (in):**
- In-memory session game store keyed by game id. No database, nothing persisted.
- Endpoints: create game, get game, post move, delete game.
- The move endpoint is computed from the request's `FEN + move` (stateless). It does not derive the result from stored state.
- The store keeps move history only so the later "Why?" lookup (`POST /api/coach/explain {game_id, move_id}`, Phase 5) can find a move.

**Scope (out):**
- No Stockfish/engine call in this slice. Engine analysis, delta classification and the evaluation cache come in later phases.
- No LLM, no "Why?" endpoint, no frontend work.
- Exact route paths and response shapes are not fixed by this decision.

**Verification (tests to write; none exist yet as of 2026-11-04):**
Tests go in `backend/tests/` per [decision-002](decision-002.md). They need no `@pytest.mark.engine` or `@pytest.mark.llm` marker, because this slice makes no engine or LLM calls.
- Create game returns a new game id; get game returns that game.
- Get, move or delete on an unknown game id returns a not-found error.
- Post legal move returns the resulting position computed from the sent `FEN + move`, and appends the move to the game's history.
- Post illegal move or invalid FEN is rejected with an error naming the bad input, and history is unchanged.
- Delete game removes it; a later get returns not-found.
- The move path does not call the engine (e.g. patch the engine wrapper to raise and confirm the move still succeeds).
- Gate: `ruff check` and `pytest` pass in `backend/` (coding standards, "Before committing").

**Rationale:** Not recorded. The user stated the decision without giving a reason. It matches the project plan's next unchecked Phase 1 items.

**Alternatives rejected:** None recorded.
