# Implementer log: coach-explain-2026-11-17

Build round: 1 of 3 (decision-008). Date: 2026-11-18.
Inputs: spec.md (revision 1, H1-approved), red-proof.md (G1 passed), log.md (H1 answers),
the three test files in `backend/tests/`.

Regression status: **pending**. No test runner is available to the implementer. The tester's
green re-run is the check, and it can only go green for `test_coach_api.py` after the main
session adds the two `main.py` lines (H1 Q1 answer (b)).

## Files created (and nothing else)

- `backend/app/services/position_analysis.py`
- `backend/app/services/coach.py`
- `backend/app/api/coach.py`
- this log

No existing file was modified. No test file was created or edited. `git status --short` at
start: `M docs/iteration-log-test-author.md`, `?? backend/tests/test_coach.py`,
`?? backend/tests/test_coach_api.py`, `?? backend/tests/test_position_analysis.py`,
`?? docs/orchestrator-runs/coach-explain-2026-11-17/` (all pre-existing, not mine).

## Wiring follow-up (required, owned by the main session per H1 Q1)

In `backend/app/main.py`, exactly two lines:

```python
from app.api.coach import router as coach_router      # next to the other router imports
app.include_router(coach_router)                       # after app.include_router(games_router)
```

Not done by me and not worked around (no `__init__.py` side effects).

## Red test -> code map

### `backend/tests/test_position_analysis.py` (red: ModuleNotFoundError)

| Test | Code meant to make it pass |
|---|---|
| `test_analyse_position_without_stockfish_path_raises_engine_unavailable` | `position_analysis.py:40-42` (RuntimeError from `engine.open_engine` -> fixed reason "STOCKFISH_PATH is not set"; `open_engine` raises before `popen_uci`) |
| `test_analyse_position_wraps_os_error_as_engine_unavailable` | `position_analysis.py:35-37` (OSError -> fixed reason "could not start the engine process", `raise ... from exc` so `__cause__ is missing`; path never copied, `str(exc)` not used) |
| `test_analyse_position_returns_lines_and_quits_engine` | `position_analysis.py:53-63` (calls `engine.analyse(uci_engine, chess.Board(fen), multipv=1)`, `finally` quits once) |
| `test_analyse_position_quits_engine_when_analysis_fails[engine_error, engine_terminated_error]` | `position_analysis.py:58-59` (EngineError, incl. EngineTerminatedError subclass) and `:62-63` (quit in `finally`) |
| `test_get_position_analyser_returns_analyse_position` | `position_analysis.py:66-68` |
| `test_engine_unavailable_error_is_a_runtime_error` | `position_analysis.py:22-23` |

Note: `_quit_engine` (`:45-50`) swallows and logs (WARNING, exception class name only) an
`EngineError`/`OSError` from `quit()`, so a failing quit never replaces the real result or
error. The fake engine's `quit` never raises, so the count is still exactly 1.

### `backend/tests/test_coach.py` (red: ModuleNotFoundError)

| Test(s) | Code |
|---|---|
| `test_verdict_names_bucket_and_centipawns_lost[*]` | `coach.py:24`, `:148` (`f"{LABEL} — {delta_cp} CP lost."`, U+2014) |
| `test_praise_and_concern_follow_bucket_without_alerts[*]` | `coach.py:25-36`, `:145-146` |
| `test_opponent_pin_alert_sets_praise[*]`, `test_own_pin_alert_sets_concern[*]`, `test_both_pin_alerts_set_praise_and_concern[*]` | `coach.py:37-38`, `:145-146` (praise and concern chosen independently) |
| `test_tip_for_good_move_is_general_advice` | `coach.py:132-135` |
| `test_tip_for_non_good_move_names_best_move_from_best_line[*]` | `coach.py:136-138` |
| `test_tip_without_best_line_falls_back_to_general_check[*]` | `coach.py:139` |
| `test_explanation_respects_plan_length_rules[*]` (64 cases) | all template strings at `coach.py:24-40`: praise/concern have no `.!?` and <= 5 words; verdict/tip have exactly one `.` at the end (em dash is not a terminator); all single-line |
| `test_select_move_returns_move_at_ply_index[*]` | `coach.py:74-76` |
| `test_select_move_out_of_range_raises_move_not_found[*]` | `coach.py:79-81` ("no move with id ...; expected a move_id from 0 to {n-1}") |
| `test_select_move_negative_id_raises_instead_of_wrapping[*]` | `coach.py:75` (explicit `0 <= move_id` guard; never indexes with a negative) |
| `test_select_move_on_empty_game_raises_move_not_found` | `coach.py:77-78` ("expected a game with at least one recorded move") |
| `test_move_not_found_error_is_a_lookup_error` | `coach.py:43` |
| `test_context_computes_delta_and_bucket_from_both_positions` | `coach.py:114-129` (50 - (-100) = 150 -> mistake; best_line "g1f3 b8c6") |
| `test_context_calls_analyser_with_fen_before_then_fen_after` | `coach.py:116` then `:119` |
| `test_context_reports_opponent_pin_alert`, `test_context_reports_own_pin_alert`, `test_context_without_pins_has_no_alerts` | `coach.py:102-111` (mover = side to move in `fen_before`; own first, then opponent; each at most once) |
| `test_checkmating_move_scores_result_as_mate_without_second_engine_call` | `coach.py:95-96` (`-MATE_SCORE`, no analyser call; 9999 - 10000 clamps to 0 -> good) |
| `test_stalemating_move_scores_result_as_zero_without_second_engine_call` | `coach.py:97-98` (`is_game_over(claim_draw=False)` -> 0, no analyser call) |
| `test_context_carries_move_fields_and_versions` | `coach.py:121-129`, defaults at `:58-59` |
| `test_empty_analysis_raises_engine_unavailable[before, after]` | `coach.py:84-89` ("engine returned no analysis for FEN ...; expected at least one line") |

### `backend/tests/test_coach_api.py` (red: 404 Not Found, router unwired)

All 16 depend on the main.py wiring above; without it they stay 404. With it:

| Test(s) | Code |
|---|---|
| `test_explain_returns_200_with_exactly_four_string_keys`, `test_explain_mistake_returns_templated_card`, `test_explain_reports_pin_on_opponent_in_praise`, `test_explain_reports_own_pinned_piece_in_concern`, `test_explain_uses_move_id_as_zero_based_ply_index`, `test_explain_does_not_change_game_history` | `api/coach.py:44-75` (read-only: `store.get` + `game.history` tuple; no store writes) |
| `test_explain_unknown_game_returns_404`, `test_explain_unknown_game_does_not_call_engine` | `api/coach.py:51-55` (before any analyser call) |
| `test_explain_move_id_out_of_range_returns_404[*]`, `test_explain_out_of_range_move_does_not_call_engine` | `api/coach.py:56-60` |
| `test_explain_negative_move_id_returns_422_with_string_detail` | `api/coach.py:27` (`Field(ge=0)`), string detail from the existing handler in `main.py` (loc `body.move_id`) |
| `test_explain_missing_field_returns_422_with_string_detail[*]` | `api/coach.py:23-27` + existing `main.py` handler |
| `test_explain_engine_unavailable_returns_503` | `api/coach.py:61-65` (detail = `"explain move failed: " + exc.args[0]`) |
| `test_explain_after_takeback_explains_the_replacement_move` | `coach.py:72-76` reads the current history, so the replacement move is explained |

Override compatibility: the tests install `app.dependency_overrides[get_position_analyser] =
lambda: fake`; `AnalyserDep` depends on `get_position_analyser` (`api/coach.py:18`), and the
handler awaits whatever callable the dependency returns.

## HTTP contract as built

Route: `POST /api/coach/explain` (router prefix `/api/coach`, tag `coach`). Plan line 57;
spec 2.4/2.5.

- Request `ExplainRequest {game_id: str, move_id: int >= 0}`. Plan line 57.
- Response 200 `ExplainOut {verdict, praise, concern, tip}`, all strings, no other keys. Plan
  lines 72-81; spec 2.3, 5.3 (`exactly_four_string_keys`, `mistake_returns_templated_card`).
- 422: missing/mistyped field or `move_id < 0`; string detail with "invalid request" and the
  field name, from the existing `main.py` handler. decision-004; spec 2.5 row 2.
- 404 `"explain move failed: no game with id '...'; expected an id returned by POST /api/games"`.
  decision-004; spec 2.5 row 3.
- 404 `"explain move failed: no move with id N in game '...'; expected a move_id from 0 to M"`
  (or "...expected a game with at least one recorded move"). spec 2.5 row 4 and its rationale.
- 503 `"explain move failed: engine unavailable (...); expected a working Stockfish binary at
  STOCKFISH_PATH"` or `"explain move failed: engine returned no analysis for FEN ...; expected
  at least one line"`. H1 Q2; spec 2.5 row 5.
- Check order: 422 -> 404 game -> 404 move -> 503 -> 200. The analyser is never called
  before both lookups succeed.
- Logging: INFO `game %s: explained move %d (bucket %s, source fallback)` on success; INFO
  rejection lines with game id and move_id. The request body is never logged.
- No LLM call anywhere; plan line 83 fallback is the only path (spec 1, 8).

## Mocked components and seams

- Stockfish (API tests): `get_position_analyser` dependency (`position_analysis.py:66-68`),
  consumed via `AnalyserDep` (`api/coach.py:18`).
- Stockfish (service tests): `build_move_context(move, analyser)` takes the analyser as an
  argument (`coach.py:114`).
- Stockfish (unit tests of the boundary): `analyse_position` calls `engine.open_engine()`,
  which looks up `chess.engine.popen_uci` at call time, so monkeypatching it and
  `STOCKFISH_PATH` works; no binary is needed.
- LLM: none exists. No `openai` import, no provider env vars, no cache.

## Reviewer checks (spec 5.4), self-checked by reading

- `services/coach.py` and `services/position_analysis.py` import no `fastapi` and no `app.api`.
- `coach.py` imports only `MATE_SCORE` from `engine.py`; it reaches the engine only through
  the injected analyser. It imports `EngineUnavailableError`/`PositionAnalyser` from
  `position_analysis` (a service module, no FastAPI).
- No module reads env vars; `STOCKFISH_PATH` is read only inside `engine.open_engine`.
  Error messages never include its value (fixed reason strings, never `str(exc)`).
- Docstrings on every function and class, type hints on every signature, `_` private helpers,
  module loggers, no `print`.
- Ruff is not run (decision-009); knowledge standards still mention ruff.

## Deferred / follow-ups

- **main.py wiring** (above): main session, per H1 Q1 (b). Blocks all of `test_coach_api.py`.
- Out of scope per spec 8: LLM path, cache, `fen_before`/409 takeback guard (H1 Q3), other
  tactical motifs, per-move analysis payload, frontend.
- Each "Why?" opens Stockfish and runs up to two analyses (no evaluation cache); engine
  analysis is serialized by `engine._analysis_lock`. Noted, not changed.
- No shared-code change needed beyond the main.py lines.

## Loop findings addressed

None: this is round 1.

## Candidate commands for the tester

`uv run pytest` in `backend/` (full suite; baseline 123 + the 100 new tests).
