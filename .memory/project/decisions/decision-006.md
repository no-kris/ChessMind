# Decision 006 - Game history has no gaps; takebacks use their own endpoint

**Date:** 2026-11-05 (first recorded); revised 2026-11-06
**Review by:** 2027-02-04
**Status:** Active. Confirmed by the user on 2026-11-06. This reverses the agent's original 2026-11-05 choice.

**Decision:** A game's history is always one continuous game: each move's `fen_before` equals the previous move's `fen_after` (or the start position for move 0).
- `POST /api/games/{game_id}/moves` still computes the result from the request's `FEN + move`, as decision-003 requires. It **records the move only if the request FEN, in canonical form, equals the game's current position** (`game.fen`). Otherwise it returns **409** "does not match". Checks run in a fixed order: 404 unknown game, then 400 bad FEN or move, then 409 mismatch.
- The comparison is between canonical FENs (`apply_move`'s `fen_before` vs the stored `fen_after`), never between raw strings. A FEN carrying an uncapturable en-passant square still matches. Move counters do count, so a FEN with a wrong halfmove or fullmove number is a mismatch.
- **Takebacks:** `POST /api/games/{game_id}/takeback` removes the last move (one ply) and returns 200 `GameOut` at the previous position. With no moves it returns 409 "no moves to take back"; an unknown game gives 404. It is backed by `GameStore.pop_move`, which raises `NoMovesError`.
- **The check lives in the store** (`GameStore.append_move`, since 2026-11-06). It raises `PositionMismatchError(ValueError)`, which the router maps to 409. Because the check and the append are one synchronous call, the rule holds for every caller, and a handler may `await` before calling it, e.g. for a Phase 2 engine call. `Game.history` is a read-only tuple and the list itself is private as `Game._history`, so nothing outside `GameStore` can append around the check. Tests lock this in: `test_history_cannot_be_changed_from_outside_the_store` and `test_two_requests_racing_from_the_same_position_record_only_one_move`. `apply_move` stays a pure function so Phases 2–4 can reuse it without a game.

**Consequences for later phases:**
- Replaying history from the start is valid; any feature that walks the moves in order can rely on it. (PGN export was the motivating example but was dropped from scope on 2026-11-06; see [decision-003](decision-003.md).)
- Phase 2's "position before a move = previous move's result" cache shortcut always holds.
- **`move_id` values are reused after a takeback.** Take back move 3, play a different move, and the new move is also `move_id` 3. A "Why?" request (Phase 5) sent with a `move_id` from before the takeback would explain the new move. Either the client clears per-move UI on takeback, or Phase 5 should also accept the expected `fen_before` and return 409 when it differs.
- **A game can only start from the standard start position.** Starting from a custom FEN (puzzles, analysis) would need an optional `fen` on `POST /api/games`. Not built.
- Takeback is one ply. Undoing "my move and the engine's reply" means calling it twice. A `count` parameter was left out on purpose until a caller needs it.

**Rationale:** The user chose a gapless history over the agent's original "trust the client FEN" design after a demo showed that a takeback produced a history reading "1. e4 2. d4". That kind of history breaks replay and PGN, hides a client whose board is out of sync, and weakens the Phase 2 cache assumption.

**Alternatives rejected:**
- Trust the client's FEN and allow gaps. This was the original 2026-11-05 version of this decision. Takebacks needed no endpoint, but the history became a request log rather than a game.
- Accept a mismatched move with a `continuous: false` flag. It keeps the gaps and only labels them.
- Keeping the check in the router (the first 2026-11-06 version). A step-2 code review showed two holes. Any code holding a `Game` could append straight to its mutable `history` list. And one `await` between the router's check and its append let two requests both pass, which was reproduced. The user chose to move the check into the store.
