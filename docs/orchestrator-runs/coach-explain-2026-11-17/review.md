# Review: coach-explain-2026-11-17, build round 1 of 3

Reviewer stage. Date: 2026-11-18.
Inputs read: spec.md (rev 1, H1-approved), log.md, green-report-round-1.md,
implementer-log.md, the three test files, the three new production files, and
for context `engine.py`, `classify.py`, `game_store.py`, `tactics.py` (pinned_color),
`main.py`, `conftest.py`, `.memory/knowledge/coding-standards.md` and
`testing-standards.md`. Memory scope (`.memory/SCOPE.md` = ChessMind) matches this repo.

## Verdict

**pass**

The production code matches spec.md in every checked point, and each acceptance
criterion in section 5 has a test with real assertions. One test is weak because
of the input value the spec itself prescribes (O1 below). It is recorded as a
non-blocking observation for the human or tester. It is not a reason to reject:
the test follows spec 5.1 literally, the code under it is correct, and the
implementer cannot change test files.

## (a) Code vs. spec

| Spec item | Verified how | Result |
|---|---|---|
| 2.1 `PositionAnalyser`, `EngineUnavailableError(RuntimeError)`, `analyse_position`, `get_position_analyser` | read `backend/app/services/position_analysis.py:13`, `:22`, `:53`, `:66` | ok |
| 2.1 uses `engine.open_engine()` and `engine.analyse(..., chess.Board(fen), multipv=1)`, default depth | `position_analysis.py:35`, `:57` (no depth passed, so it uses engine.py's default of 15) | ok |
| 2.1 `quit()` in `finally` once the engine is open | `position_analysis.py:54-63`. The open happens before the `try`, so quit runs only when an engine exists | ok |
| 2.1 wrap RuntimeError / OSError / EngineError (incl. EngineTerminatedError) with `raise ... from exc`, message `engine unavailable ({reason}); expected a working Stockfish binary at STOCKFISH_PATH`, never the env value | `position_analysis.py:19`, `:26-28`, `:33-42`, `:58-61`. All reasons are fixed text and `str(exc)` is never interpolated. Except-clause order OSError → EngineError → RuntimeError is correct (EngineError subclasses RuntimeError) | ok |
| 2.1 `engine.py` not edited | not in `git status --short` | ok |
| 2.2 constants, `MoveNotFoundError(LookupError)`, frozen `MoveContext` / `Explanation` with exact fields and defaults | `backend/app/services/coach.py:19-22`, `:42-68` | ok |
| 2.2 `select_move`: no negative wrap, exact message text, empty-history variant | `coach.py:71-80`. The `0 <= move_id < len` guard means a negative id never indexes | ok |
| 2.2 `build_move_context` steps 1-5: before analysis first; empty → EngineUnavailableError with the "no analysis" message; checkmate → `-MATE_SCORE` with no call; other game-over (`claim_draw=False`) → 0 with no call; `eval_loss` / `bucket`; pin alerts own-then-opponent, deduplicated, mover = side to move in `fen_before`; analyser errors propagate unchanged | `coach.py:83-125`. `tactics.Pin.pinned_color` uses `chess.COLOR_NAMES` (`tactics.py:85`), the same vocabulary as `coach.py:104` | ok |
| 2.2 no engine import beyond `MATE_SCORE` | `coach.py:12`. It also imports `EngineUnavailableError` and `PositionAnalyser` from `position_analysis`, which the 2.2 interface requires | ok |
| 2.3 exact template strings, U+2014 separator, UCI tip | `coach.py:24-40`, `:128-148`, compared string by string with the 2.3 table. The em dash in `coach.py:146`, the test file and the spec render the same; I could only check this visually because I have no byte tool | ok |
| 2.3 / plan line 81 shape rules | Checked every literal by hand: praise/concern have no `.!?` and are 3-5 words; verdict and tip each end with one `.`, and the only other punctuation is commas and the em dash; all are single-line | ok |
| 2.4 router prefix/tag, `ExplainRequest` with `Field(ge=0)`, `ExplainOut`, local `StoreDep` / `AnalyserDep`, `async def` | `backend/app/api/coach.py:15-36`, `:43-44` | ok |
| 2.5 status mapping 404 / 404 / 503 / 200, detail `explain move failed: ` + `exc.args[0]` (avoids KeyError quoting) | `api/coach.py:39-40`, `:50-64` | ok |
| 2.5 check order 422 → 404 game → 404 move → 503 → 200, and the engine is never started for an unknown game or move | `api/coach.py:50-64`, sequential `store.get` → `select_move` → `build_move_context` | ok |
| 2.5 logging: INFO success line verbatim, INFO rejections with game id and move_id, no body | `api/coach.py:53`, `:58`, `:63`, `:66-68` | ok |
| 3 services never import FastAPI; only the router maps to HTTP | Neither `coach.py` nor `position_analysis.py` imports `fastapi` or `app.api` | ok |
| 5.4 no `openai` import | `codebase_search "openai"` under `backend/`: hits only in pyproject.toml, uv.lock, a main.py description string and stale pytest cache ids. No import | ok |
| 5.4 no env var other than STOCKFISH_PATH, and only via `open_engine` | `codebase_search "environ"` / `"getenv"` under `backend/app/`: only `engine.py:15` and the existing `main.py` LOG_LEVEL / CORS_ORIGINS. No new file imports `os` | ok |
| No cache (spec 8) | No module-level result dict, no `functools` cache, no store writes in any new file | ok |
| Out of scope not built (no LLM, no `source` field, no context in response, no `fen_before` / 409) | `ExplainOut` has exactly 4 fields; no takeback guard. The decision-006 reuse is out of scope by human decision and is not counted | ok |
| 5.4 docstrings, type hints, `_` helpers, module loggers, no `print` | Read every def and class in the 3 files | ok |
| 5.4 no existing file modified except main.py | `git status --short`: `M backend/app/main.py` (human-authorized 2 lines, confirmed at `main.py:10`, `:84`) and `M docs/iteration-log-test-author.md` (tester's docs log, not production). Everything else is new | ok |

## (b) Tests vs. spec

Every name in sections 5.1, 5.2 and 5.3 exists in the matching file with the
specified inputs. The green report shows 223 passed (100 new). Assertions that
specifically defeat plausible wrong implementations:

- Sign convention: `test_context_computes_delta_and_bucket_from_both_positions`
  (50, 100 → 150). A `best - result` implementation would clamp to 0 and fail.
- Mate shortcut: `test_checkmating_move_...` (9999 → delta 0). Using `+MATE_SCORE`
  or 0 would give a blunder, and an extra analyser call fails twice (unexpected-FEN
  AssertionError and the `calls` check).
- Negative wrap: `test_select_move_negative_id_...` with -1 and -2 on a 2-move game.
  `history[move_id]` would return a move and fail.
- 422 vs 404 for a negative id: `test_explain_negative_move_id_...` fails if
  `Field(ge=0)` is missing, because `select_move` would then give 404.
- Check order: both `..._does_not_call_engine` tests assert `calls == []`.
- Ply indexing: `test_explain_uses_move_id_as_zero_based_ply_index` gives different
  scores and pv per FEN. An off-by-one would hit an unexpected FEN or produce the wrong verdict or tip.
- Exact cards at the API level (mistake, opponent pin, own pin) compare the whole body
  with `==`, so extra keys or wrong strings fail.
- Error paths are covered: 404 game, 404 move (1 move with id 1, and an empty game),
  422 (negative, missing field ×2), 503, and the service-level empty-analysis case for both sides.

### Evaluation of the three red-stage points

1. **Lazy `importlib` imports.** Acceptable. Each test resolves the module when it
   runs, so after green it behaves exactly like a module-level import. In
   `test_coach_api.py:52-65` the tolerance is narrow: only
   `ModuleNotFoundError` whose `exc.name` is exactly `app.services.position_analysis`
   is swallowed, and any other import error propagates. If the module were missing,
   the coach router (which imports it) could not be wired either, so a skipped
   override cannot let a request reach a real engine. There is no assertion weakness.
2. **`app.dependency_overrides[...] = lambda: fake`.** Correct, and it is the only correct
   form. `get_position_analyser` returns the analyser callable, so the override must
   return the fake. Installing `fake` directly would make FastAPI inspect
   `FakeAnalyser.__call__(fen: str)` as a dependency signature and require a `fen`
   query parameter (422). The 200 tests would catch that mistake, so this is safe either way.
3. **`FAKE_PATH not in message`** (`test_position_analysis.py:96`). This assertion is real.
   `str(FileNotFoundError(2, "No such file or directory", FAKE_PATH))` contains the
   path, so an implementation that interpolated `str(exc)` would fail. It is paired with
   `__cause__ is missing`, which checks the `raise ... from exc` chain. Limit: it covers
   only the OSError path. The startup-EngineError and analysis-error paths have no
   leakage assertion. The current code uses fixed reason strings on every path, so
   nothing leaks today.

## Non-blocking observations (no change required for this run)

- **O1 (test strength, spec-prescribed input).**
  `backend/tests/test_coach.py:363-373`
  (`test_stalemating_move_scores_result_as_zero_without_second_engine_call`) uses a
  before-score of 0, as spec 5.1 prescribes. Because
  `eval_loss = max(0, best + result)`, a wrong implementation that returns
  `-MATE_SCORE` (or any negative value) for every game-over position would also give
  `delta_cp == 0` and pass. So the H1-confirmed Q6 rule "other finished game = 0"
  (spec 2.2 step 2) is checked only for "no second analyser call", not for the value 0.
  The current code is correct (`coach.py:97-98`). Suggested direction for a later
  tester pass, routed to the human or tester and not the implementer: use a positive
  before-score (for example 50, which expects delta 50 and bucket `inaccuracy`), which
  separates 0 from `-MATE_SCORE`. That needs a spec 5.1 amendment.
- **O2 (error reason accuracy).** `backend/app/services/position_analysis.py:40-42`
  maps *any* `RuntimeError` from `open_engine` to the reason "STOCKFISH_PATH is not set".
  `NotImplementedError` (a RuntimeError subclass, raised for asyncio subprocesses under a
  Windows selector event loop) would be mislabelled. Spec 2.1 names only the
  missing-path RuntimeError, so this is in spec. It does not apply to the WSL/Linux
  environment. Possible future direction: check the variable's presence rather than the exception type.
- **O3 (minor untested branches, not acceptance criteria).** There are no tests for:
  an `EngineError` raised during startup (`position_analysis.py:37-38`), the "no
  analysis" 503 through HTTP (covered at service level, and the router catches the same
  class), the default depth passed to `engine.analyse`, and a `quit()` that raises
  (`position_analysis.py:45-50`, an addition the spec allows that logs only the class name).
- **O4 (process).** `docs/iteration-log-test-author.md` is a modified tracked file. It is
  the tester's own log from the red stage (log.md, G2 evidence), not production code,
  so it is not counted against spec 5.4.
- Lint was not evaluated (decision-009).
