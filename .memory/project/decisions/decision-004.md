# Decision 004 - Game API contract and error-handling rule

**Date:** 2026-11-05
**Review by:** 2027-02-03
**Status:** Active. Chosen by the agent while implementing [decision-003](decision-003.md); not yet reviewed by the user.

**Decision:** The Phase 1 routes, status codes and error rule are fixed as follows. Change them here and in the tests together.

| Operation | Route | Success | Errors |
|---|---|---|---|
| Create game | `POST /api/games` | 201 `GameOut` | none |
| Get game | `GET /api/games/{game_id}` | 200 `GameOut` | 404 |
| Post move | `POST /api/games/{game_id}/moves` body `{fen, move}` | 201 `MoveOut` | 404 unknown game; 400 bad FEN, non-UCI or illegal move; 409 FEN is not the game's current position ([decision-006](decision-006.md)); 422 missing or mistyped body field (FastAPI default) |
| Take back move | `POST /api/games/{game_id}/takeback` (added 2026-11-06) | 200 `GameOut` after removing the last move | 404 unknown game; 409 no moves to take back |
| Delete game | `DELETE /api/games/{game_id}` | 204, no body | 404 |

- `GameOut` = `{game_id, fen, history: [MoveOut]}`. `fen` is the last move's `fen_after`, or the start position.
- `MoveOut` = `{move_id, move, san, fen_before, fen_after}`.
- **Moves are UCI only** (`e2e4`, promotions like `e7e8q`). SAN input such as `Nf3` gets a 400. This matches the plan's `"move": "e2e4"` payload and the position fixtures. Moves are parsed with `board.parse_uci`, which rewrites king-takes-rook castling (`e1h1`) to standard `e1g1`, so the stored `move` has one spelling per move (added 2026-11-05). `parse_uci` returns the null move `0000` instead of raising, so `apply_move` checks for it explicitly and returns a 400.
- **`move_id` is the 0-based ply index** into the game's history. Phase 5's `POST /api/coach/explain {game_id, move_id}` should look moves up by this index.
- **`game_id` is `uuid4().hex`** (32 lowercase hex chars, no dashes).
- `fen_before` and `fen_after` are python-chess canonical `board.fen()`. Because the en-passant square is written only when a capture is legal, the client's FEN text may differ from `fen_before`. Phase 2's evaluation-cache key should use the canonical form.
- **Error-handling rule:** services (`app/services/moves.py`, `app/services/game_store.py`) never import FastAPI. They raise domain errors: `MoveError(ValueError)` → 400, `GameNotFoundError(KeyError)` → 404, `NoMovesError(LookupError)` → 409 and `PositionMismatchError(ValueError)` → 409. A `KeyError`'s `str()` adds quotes, so the router builds messages from `exc.args[0]`.
- **Message convention (2026-11-06):** a domain error message says only the problem and what was expected (e.g. `illegal move 'e2e5' for FEN …; expected …`). The router adds the operation, so every `detail` reads `"<operation> failed: <problem>; expected <…>"` (`post move failed:`, `get game failed:`, `take back move failed:`, `delete game failed:`). New services should follow this, not put their own operation prefix in the message.
- **Every error `detail` is a string, including 422.** An exception handler in `app/main.py` (`validation_error_handler`) rewrites FastAPI's list-of-objects 422 into `"<METHOD> <path> failed: invalid request (body.move: Field required; …); expected a request matching the API schema at /docs"`. It names the fields but **never echoes submitted values** (coding standards: no request bodies in output). Known gap: the generated OpenAPI spec (`/docs`) still describes the 422 with FastAPI's default list schema (`HTTPValidationError`). Fixing that needs a custom `openapi()` or per-route `responses=`; not done.
- Unknown body fields are silently ignored (Pydantic default). A `game_id` in the body is ignored; the id only comes from the URL. `POST /api/games/` (with a trailing slash) gets a 307 redirect to `/api/games`, so clients should use the exact path. Only the router (`app/api/games.py`) turns those into `HTTPException`. Every message names the operation, the bad input and what was expected (coding standards). Tests check only the status code and a key phrase (`"illegal move"`, `"invalid FEN"`, `"not UCI"`, `"does not match"`, `"no moves to take back"`, `"get game"`/`"post move"`/`"take back move"`/`"delete game"`). A FEN that parses but describes an impossible position (`board.is_valid()` is false, e.g. no kings) counts as an invalid FEN.

**Rationale:** Decision-003 left the route paths and response shapes open, and the frontend and the Phase 5 "Why?" endpoint both depend on them. The testing standards already use `test_illegal_move_returns_400` as their example, so 400 is the expected code for a bad move. Moves use 201 because each one adds a history record with its own id. Keeping HTTP out of the services lets Phase 2 and 4 reuse `apply_move` without FastAPI.

**Alternatives rejected:**
- 422 for illegal moves. It would mix chess errors with FastAPI's schema-validation errors.
- 200 for moves. Would also have worked.
- Accepting SAN as well as UCI. It makes parsing ambiguous, and nothing downstream uses SAN as input.
- Integer game ids. They are guessable and collide after a restart.
