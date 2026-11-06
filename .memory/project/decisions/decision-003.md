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

**Progress (2026-11-05):** Implemented, not yet committed. The choices made during implementation are in [decision-004](decision-004.md) (routes, status codes, error rule), [decision-005](decision-005.md) (single-process store constraints) and [decision-006](decision-006.md) (client FEN is trusted; needs user confirmation).
- New files: `backend/app/services/moves.py` (pure `apply_move`), `backend/app/services/game_store.py`, `backend/app/api/games.py` (router, included in `main.py`), `backend/tests/conftest.py`, `backend/tests/test_moves.py`, `backend/tests/test_game_store.py`, `backend/tests/test_games_api.py`.
- Every verification item above has a test. `pytest`: 53 passed (28 before).
- **Gate caveat:** `ruff check` reports 9 `EXE002` errors (executable without shebang) in files that existed before this work. Git stores them as `100644`, but on the WSL mount they appear executable, and `core.fileMode=false` hides this from git. None of the errors come from this slice's code. The user needs to decide on a fix (chmod -x, or ignore EXE002 in `pyproject.toml`) before the gate can pass.
- Also, all 32 "modified" files in `git status` at the start of the session differed only in line endings (CRLF), not content.
- **2026-11-06:** Castling is now stored in standard UCI (`e1h1` → `e1g1`). The user confirmed a gapless history: a FEN mismatch returns 409, and `POST /api/games/{id}/takeback` was added ([decision-006](decision-006.md) revised). `pytest`: 67 passed. `ruff check`: only the 9 pre-existing EXE002 errors.
- **2026-11-06 (later):** After the step-2 review, the no-gaps check moved into `GameStore.append_move`, and `Game.history` became a read-only tuple. `pytest`: 70 passed. A mutation check (disabling the store check) made 4 tests fail.
- **2026-11-06 (router review):** Fixed three things. App logs had been silently dropped, now fixed in [decision-007](decision-007.md). 422s now use a string `detail`, and 400s now carry the `post move failed:` prefix ([decision-004](decision-004.md)). Errors for impossible positions now list status flag names. `pytest`: 76 passed. Confirmed against a real uvicorn server, not just TestClient.
- **Committed 2026-11-06** on branch `feat/phase1-game-store` (not merged, not pushed), at the user's request. `ai_chess_coach_project_plan.md` Phase 1 was updated in the same commit: items ticked, takeback and logging added, and PGN export split out as the one open Phase 1 item. The 32 files whose only change was line endings (CRLF) were left out of the commit.
- Still open: merge to `main`; PGN export; decisions 004–005 were never explicitly reviewed by the user (who asked to commit them as they are). Plan items "Implement FEN/PGN utilities" and PGN export are not done; only FEN handling exists.

**Rationale:** Not recorded. The user stated the decision without giving a reason. It matches the project plan's next unchecked Phase 1 items.

**Alternatives rejected:** None recorded.
