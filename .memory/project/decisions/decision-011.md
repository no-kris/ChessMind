# Decision 011 - Phase 5 "Why?" endpoint: templated fallback only

**Date:** 2026-11-18
**Review by:** 2027-02-16
**Status:** Active. Answers confirmed by the user on 2026-11-17 at the spec gate (H1). Built and green, not yet committed.

**Decision:** `POST /api/coach/explain` with `{game_id, move_id}` returns `{verdict, praise, concern, tip}` built only from templates (bucket + tactical alerts). No LLM, no `openai` import, no provider env vars, no explanation cache in this slice. Spec: `docs/orchestrator-runs/coach-explain-2026-11-17/spec.md`.
- Status codes (decision-004 style, every `detail` starts "explain move failed: "): 422 bad body or `move_id < 0` (so -1 never wraps to the last move); 404 unknown game; 404 `move_id` past the end of history; **503 engine unavailable** (user chose this over a generic 200 card). Check order: 422 → 404 game → 404 move → engine.
- The move's evaluation is not stored, so the endpoint runs the engine on demand (before and after positions) via `services/position_analysis.py`. Tests replace it through the `get_position_analyser` dependency override and never need Stockfish.
- Alert names are `own_piece_pinned` / `opponent_piece_pinned` (not the plan's bare `pin`), so templates know whose piece is pinned.
- A game-ending move skips the engine on the final position: checkmate = `-MATE_SCORE`, other finished game = 0.
- Template wording is spec section 2.3 and is locked in by tests.
- **`move_id` reuse after takeback (decision-006) is accepted for now:** the endpoint explains whatever move is at that index. `test_explain_after_takeback_explains_the_replacement_move` locks this in. No `fen_before` field and no 409 path. Revisit when the LLM slice or Phase 6 UI lands.
- `main.py` wiring was added by the main session on the user's instruction, because the implementer's write scope only covers new files under `backend/app/api/**` and `backend/app/services/**`.

**Known gaps (from review):** the stalemate test cannot tell "0" from `-MATE_SCORE` (spec 5.1 before-score of 0); any engine-startup RuntimeError is reported as "STOCKFISH_PATH is not set"; a few non-criteria branches are untested; never exercised against a real Stockfish.

**Still to come in Phase 5:** the real LLM call, JSON mode, and the explanation cache, with this template as the fallback.
