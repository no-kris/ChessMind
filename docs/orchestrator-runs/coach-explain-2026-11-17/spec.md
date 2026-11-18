# Spec: "Why?" endpoint with offline templated explanation (Phase 5, first slice)

Run-id: `coach-explain-2026-11-17`
Author role: Planner
Status: awaiting H1 approval (revision 1). **Build is blocked on Q1 (wiring
needs a 2-line edit to the existing `backend/app/main.py`).**

## 1. Goal

Add `POST /api/coach/explain` with body `{game_id, move_id}`. It returns the
coach card `{"verdict", "praise", "concern", "tip"}`, built **only** by the
offline templated fallback from the move's bucket, centipawn loss, tactical
alerts and best line. No LLM is called in this slice.

The server rebuilds the move's context on request:
- the move comes from the session game store (`move_id` = 0-based ply index);
- `delta_cp` and `bucket` come from engine analysis of `fen_before` and
  `fen_after` through `engine.analyse`, then `classify.eval_loss` and
  `classify.bucket`;
- tactical alerts come from `tactics.find_pins(fen_after)`.

Nothing about a move's evaluation is stored today (`MoveResult` holds only
`move, san, fen_before, fen_after`), and Phase 2/4 caches don't exist yet. So
the endpoint has to run the engine on demand. Tests never touch a real
Stockfish: the engine sits behind a FastAPI dependency that tests override
(section 4).

### Source in the plan (`ai_chess_coach_project_plan.md`)

- Line 57: the route `POST /api/coach/explain` with `{ game_id, move_id }`, on
  demand only.
- Lines 58-70: server-side context `fen, move, delta_cp, bucket,
  tactical_alerts, best_line, prompt_version, schema_version`. This becomes the
  `MoveContext` dataclass (section 2.2).
- Lines 72-80: response keys `verdict, praise, concern, tip`. The verdict
  example `"Mistake — 150 CP lost."` (line 76) is the verdict template.
- Line 81: length rules. `verdict` is one short sentence, `tip` is one
  sentence, `praise`/`concern` are at most a phrase. These become the shape
  rules in section 2.3.
- Line 83: "offline fallback ... templated explanation built from the bucket
  and tactical alerts". In this slice the fallback is the **only** path.
- Lines 46-51 (Phase 4): `ΔE = E_best − (−E_result)` and bucket thresholds.
  Both are already implemented in `classify.py`, so this slice reuses them.
- Not built from the plan: line 71 (OpenAI SDK and provider env vars), the
  JSON-mode part of line 72, and line 82 (LLM cache). See section 8.

### Standards and decisions applied

- decision-004: 404 for an unknown game. Every error `detail` is a string
  `"<operation> failed: <problem>; expected <…>"`, and 422 is a string too
  (the handler already in `main.py` covers any included router). The
  operation name here is **`explain move`**. `move_id` is the 0-based ply
  index. Services raise domain errors and never import FastAPI. Only the
  router maps them to HTTP and builds the message from `exc.args[0]`.
- decision-005: handler is `async def`. Store methods are called
  synchronously. Swappable boundaries use a dependency getter. No new
  in-memory store or cache is added, so `conftest.py` needs no new reset.
- decision-006: `move_id` is reused after a takeback. **No `fen_before`
  field and no 409 path in this slice** (section 8, Q3).
- decision-009: pytest only, no lint gate.
- coding-standards: docstrings, type hints, `_` private helpers,
  `logging.getLogger(__name__)`, no `print`, error messages name the bad input
  and what was expected, no hardcoded paths (`STOCKFISH_PATH` stays the only
  engine setting), never log request bodies.
- testing-standards: `TestClient` for API tests, one test file per module, no
  network, mocked boundaries, explicit expected values, parametrize repeats,
  status code plus key phrase assertions. No test may need `STOCKFISH_PATH`
  or a Stockfish binary, and none uses `@pytest.mark.engine` or
  `@pytest.mark.llm`.

## 2. Interfaces (exact)

### 2.1 `backend/app/services/position_analysis.py` (new). Production engine boundary

```python
PositionAnalyser = Callable[[str], Awaitable[list[dict]]]
# Takes a canonical FEN. Returns engine.analyse-shaped lines:
# [{"score_cp": int, "pv": [uci, ...]}, ...], best line first,
# scored from the side to move's point of view.

class EngineUnavailableError(RuntimeError):
    """Raised when the engine cannot be started or returns no analysis."""

async def analyse_position(fen: str) -> list[dict]:
    """Open Stockfish, analyse one position (multipv=1), close it, and return the lines."""

def get_position_analyser() -> PositionAnalyser:
    """Return analyse_position; a FastAPI dependency so tests can swap in a fake."""
```

Behavior:
- `analyse_position` calls the existing `engine.open_engine()` and
  `engine.analyse(engine, chess.Board(fen), multipv=1)` (default depth). It
  always calls `await engine.quit()` in a `finally` once the engine was
  opened.
- These failures are wrapped in `EngineUnavailableError` with `raise ... from
  exc`: the `RuntimeError` from `open_engine` (missing `STOCKFISH_PATH`), an
  `OSError` (for example a bad path), and `chess.engine.EngineError` /
  `chess.engine.EngineTerminatedError`. Message:
  `engine unavailable ({reason}); expected a working Stockfish binary at STOCKFISH_PATH`.
  The message never includes the env var's value.
- Do not edit `engine.py`.

### 2.2 `backend/app/services/coach.py` (new). Pure coaching service, no FastAPI, no engine import beyond `MATE_SCORE`

```python
PROMPT_VERSION = 1
SCHEMA_VERSION = 1
OWN_PIECE_PINNED = "own_piece_pinned"
OPPONENT_PIECE_PINNED = "opponent_piece_pinned"

class MoveNotFoundError(LookupError):
    """Raised when a move_id is not a valid ply index in the game's history."""

@dataclass(frozen=True)
class MoveContext:
    """Structured context for one played move (plan Phase 5), the input to the explanation templates."""
    fen: str                          # canonical fen_before
    move: str                         # UCI
    san: str
    delta_cp: int                     # >= 0
    bucket: str                       # "good" | "inaccuracy" | "mistake" | "blunder"
    tactical_alerts: tuple[str, ...]
    best_line: str                    # space-joined UCI pv from fen_before, "" if none
    prompt_version: int = PROMPT_VERSION
    schema_version: int = SCHEMA_VERSION

@dataclass(frozen=True)
class Explanation:
    """The coach card: verdict, praise, concern and tip."""
    verdict: str
    praise: str
    concern: str
    tip: str

def select_move(game: Game, move_id: int) -> MoveResult:
    """Return the move at this 0-based ply index, or raise MoveNotFoundError."""

async def build_move_context(move: MoveResult, analyser: PositionAnalyser) -> MoveContext:
    """Evaluate a recorded move with the analyser and the pin detector and bundle its context."""

def build_fallback_explanation(context: MoveContext) -> Explanation:
    """Build the templated coach card from bucket, centipawn loss, alerts and best line."""
```

`select_move`:
- Raises `MoveNotFoundError` when `move_id < 0` or `move_id >=
  len(game.history)`. **A negative index must never wrap around** to the end
  of the history. Message (no operation prefix):
  `no move with id {move_id} in game {game_id!r}; expected a move_id from 0 to {n-1}`.
  When the history is empty, the message instead says
  `...; expected a game with at least one recorded move`.

`build_move_context` (the steps are the contract):
1. `lines_before = await analyser(move.fen_before)`. If it returns `[]`, raise
   `EngineUnavailableError` (`engine returned no analysis for FEN {fen!r}; expected at least one line`).
   `best_cp = lines_before[0]["score_cp"]` and
   `best_line = " ".join(lines_before[0]["pv"])`.
2. Build `board_after = chess.Board(move.fen_after)`.
   - If `board_after.is_checkmate()`: `result_cp = -MATE_SCORE` (imported
     from `engine.py`). **The analyser is not called** for `fen_after`.
   - Otherwise, if `board_after.is_game_over()` (stalemate, insufficient
     material, and so on, `claim_draw=False`): `result_cp = 0` and the
     analyser is not called.
   - Otherwise `lines_after = await analyser(move.fen_after)`. If it returns
     `[]`, raise `EngineUnavailableError` as in step 1.
     `result_cp = lines_after[0]["score_cp"]`.
3. `delta_cp = classify.eval_loss(best_cp, result_cp)` and
   `bucket = classify.bucket(delta_cp)`.
4. Alerts come from `tactics.find_pins(move.fen_after)`. The mover is the
   side to move in `fen_before`. Add `OWN_PIECE_PINNED` if any pin has
   `pinned_color` equal to the mover's color. Add `OPPONENT_PIECE_PINNED` if
   any pin has the other color. Each alert appears at most once, in the order
   own then opponent. With no pins the tuple is `()`.
5. Return `MoveContext(fen=move.fen_before, move=move.move, san=move.san, ...)`.
`EngineUnavailableError` raised by the analyser propagates unchanged.

### 2.3 Template table for `build_fallback_explanation` (exact strings)

`LABEL`: `good → "Good"`, `inaccuracy → "Inaccuracy"`, `mistake → "Mistake"`, `blunder → "Blunder"`.

- **verdict** = `f"{LABEL} — {delta_cp} CP lost."` The separator is
  `" — "` (space, U+2014 em dash, space), as in plan line 76.
- **praise**:
  - if `OPPONENT_PIECE_PINNED` in alerts: `"Pins an enemy piece"`
  - else by bucket: good `"Solid, engine-approved choice"`, inaccuracy
    `"A reasonable idea"`, mistake `"The idea is understandable"`, blunder
    `"Still time to fight back"`
- **concern**:
  - if `OWN_PIECE_PINNED` in alerts: `"Leaves your piece pinned"`
  - else by bucket: good `"Nothing major"`, inaccuracy
    `"Slightly imprecise"`, mistake `"Gives away a clear edge"`, blunder
    `"Throws away the position"`
- **tip**:
  - bucket good: `"Keep checking captures, checks and threats."`
  - not good and `best_line` non-empty:
    `f"Consider {best_line.split()[0]} instead."` (UCI, for example
    `"Consider e2e4 instead."`)
  - not good and `best_line` empty: `"Check every capture and threat before moving."`

Shape rules from plan line 81, which the templates must satisfy:
- `verdict` and `tip` each end with `.` and contain exactly one of `.`, `!`
  or `?`. An em dash is not a terminator.
- `praise` and `concern` contain none of `.`, `!`, `?` and have at most 6
  words (`len(s.split()) <= 6`).
- All four are non-empty, single-line strings.

### 2.4 `backend/app/api/coach.py` (new). Router

```python
router = APIRouter(prefix="/api/coach", tags=["coach"])

class ExplainRequest(BaseModel):
    """Body of a "Why?" request: which game and which ply to explain."""
    game_id: str
    move_id: int = Field(ge=0)

class ExplainOut(BaseModel):
    """The coach card returned to the UI."""
    verdict: str
    praise: str
    concern: str
    tip: str

@router.post("/explain")   # 200
async def explain_move(body: ExplainRequest, store: StoreDep, analyser: AnalyserDep) -> ExplainOut: ...
```

`StoreDep = Annotated[GameStore, Depends(get_game_store)]` and
`AnalyserDep = Annotated[PositionAnalyser, Depends(get_position_analyser)]`.
The router re-declares `StoreDep` locally rather than importing it from
`games.py`, which may not be edited.

### 2.5 HTTP contract

| Case | Status | `detail` key phrases (string) |
|---|---|---|
| Recorded move explained | **200**, body exactly `{verdict, praise, concern, tip}` (all strings) | n/a |
| Missing/mistyped `game_id` or `move_id`, or `move_id < 0` | **422** (existing handler in `main.py`) | `"invalid request"`, `"move_id"` / `"game_id"` |
| Unknown `game_id` | **404** | `"explain move failed"`, `"no game with id"` |
| `move_id >= len(history)` (including any id on an empty game) | **404** | `"explain move failed"`, `"no move with id"` |
| Engine unavailable or no analysis | **503** | `"explain move failed"`, `"engine unavailable"` or `"no analysis"` |

Check order: 422 (FastAPI) → 404 game → 404 move → engine (503) → 200. The
router calls `store.get` before `select_move`, and calls `select_move` before
the analyser, so an unknown game or move never starts the engine.

**Why 404 for an out-of-range `move_id`.** decision-004 maps "the thing named
by the id does not exist" to 404 (unknown game, `GameNotFoundError(KeyError)`).
`move_id` is defined as an index into the history, so an index past the end
names a move that does not exist, which is the same kind of error. 400 is
reserved for bad chess input (FEN or move), and the request contains none. 409
is reserved for state conflicts, and decision-006's takeback case is out of
scope here. `MoveNotFoundError` subclasses `LookupError`, which matches
`GameNotFoundError(KeyError)` (a `LookupError`) and `NoMovesError(LookupError)`.
A **negative** `move_id` is a malformed field value rather than a missing
move, so it is rejected by the schema (`Field(ge=0)`) with 422. This fits
decision-004's "422 missing or mistyped body field". `select_move` still
guards negatives (defence in depth, unit-tested).

**Why 503 for the engine.** The engine is an external dependency that is
temporarily unavailable. It is not a client error and not an unexpected bug.
See Q2 for the alternative of degrading instead.

Logging: one INFO line per success, `game %s: explained move %d (bucket %s,
source fallback)`. Rejections are logged at INFO with the game id and
move_id, as `games.py` does. Never log the request body.

## 3. Error behavior summary

- The service messages have no operation prefix. The router adds
  `"explain move failed: "` and uses `exc.args[0]` (`GameNotFoundError` is a
  `KeyError`, whose `str()` adds quotes).
- `TacticsError` cannot occur for stored FENs, which are canonical and valid,
  so the router does not map it. If it ever occurs, it is a 500 bug.
- No new module imports `fastapi` except `app/api/coach.py`. No module imports
  `openai`.

## 4. Mocking

- **Stockfish:** override the dependency with
  `app.dependency_overrides[get_position_analyser] = fake`. `fake` is an async
  callable that takes a FEN, looks the FEN up in a dict of canned lines, and
  records the FENs it was called with. Clear the override in a fixture
  teardown inside `test_coach_api.py`, so `conftest.py` stays unchanged. Use
  the canonical FENs taken from the `MoveOut.fen_before`/`fen_after` values
  returned when the test posts its moves.
- **`analyse_position` unit tests:** follow `test_engine_unit.py`.
  Monkeypatch `STOCKFISH_PATH` (delete it) and/or
  `chess.engine.popen_uci`, with a fake engine object that has `async
  analyse(...)` and `async quit()`. No binary.
- **LLM:** nothing to mock, since there is no client. A reviewer check
  confirms that `openai` is not imported.
- Async service tests use `@pytest.mark.anyio`, as `test_engine_unit.py`
  does.

Reachable positions used below (UCI sequences from the start position):
- `PIN_ON_OPPONENT`: `d2d4 d7d5 c2c4 e7e6 b1c3 f8b4`. `move_id` 5, mover
  Black. After it, the white knight on c3 is absolutely pinned by the b4
  bishop to e1 (d2 is empty). There are no other pins.
- `PIN_ON_OWN`: `d2d4 e7e6 c2c4 f8b4 b1c3`. `move_id` 4, mover White, who
  blocks the check with Nc3. The knight on c3 is then pinned to e1.
- `FOOLS_MATE`: `f2f3 e7e5 g2g4 d8h4`. `move_id` 3 is checkmate.
- Stalemate (service-level only):
  `apply_move("k7/8/8/1Q6/8/8/8/K7 w - - 0 1", "b5b6")`.

## 5. Acceptance criteria (test names)

### 5.1 `backend/tests/test_coach.py` (service, no HTTP)

Templates (construct `MoveContext` directly):
- `test_verdict_names_bucket_and_centipawns_lost`. Parametrized:
  (good, 0) → `"Good — 0 CP lost."`, (inaccuracy, 45) →
  `"Inaccuracy — 45 CP lost."`, (mistake, 150) → `"Mistake — 150 CP lost."`,
  (blunder, 420) → `"Blunder — 420 CP lost."`.
- `test_praise_and_concern_follow_bucket_without_alerts`. Parametrized over
  the 4 buckets with the exact strings in 2.3.
- `test_opponent_pin_alert_sets_praise`. Praise is `"Pins an enemy piece"`;
  the concern is unchanged from the bucket default.
- `test_own_pin_alert_sets_concern`. Concern is `"Leaves your piece pinned"`.
- `test_both_pin_alerts_set_praise_and_concern`.
- `test_tip_for_good_move_is_general_advice`.
- `test_tip_for_non_good_move_names_best_move_from_best_line`. Mistake with
  `best_line="e2e4 e7e5"` gives `"Consider e2e4 instead."`.
- `test_tip_without_best_line_falls_back_to_general_check`.
- `test_explanation_respects_plan_length_rules`. Parametrized over every
  bucket × alert combination. Applies the shape rules in 2.3.

Move lookup:
- `test_select_move_returns_move_at_ply_index`.
- `test_select_move_out_of_range_raises_move_not_found`. Parametrized
  over `len(history)` and `len(history)+5`. The message contains
  `"no move with id"` and `"expected"`.
- `test_select_move_negative_id_raises_instead_of_wrapping`. With 2 moves,
  `move_id=-1` raises `MoveNotFoundError`.
- `test_select_move_on_empty_game_raises_move_not_found`.
- `test_move_not_found_error_is_a_lookup_error`.

Context building (fake analyser, `@pytest.mark.anyio`):
- `test_context_computes_delta_and_bucket_from_both_positions`. Before
  `[{"score_cp": 50, "pv": ["g1f3", "b8c6"]}]`, after `[{"score_cp": 100,
  "pv": []}]`. Expect `delta_cp == 150`, `bucket == "mistake"`,
  `best_line == "g1f3 b8c6"`.
- `test_context_calls_analyser_with_fen_before_then_fen_after`.
- `test_context_reports_opponent_pin_alert` (`PIN_ON_OPPONENT` move) → `("opponent_piece_pinned",)`.
- `test_context_reports_own_pin_alert` (`PIN_ON_OWN` move) → `("own_piece_pinned",)`.
- `test_context_without_pins_has_no_alerts` (`e2e4` from the start) → `()`.
- `test_checkmating_move_scores_result_as_mate_without_second_engine_call`.
  `FOOLS_MATE` move 3, before-score 9999. The analyser is called once
  (`fen_before` only), and the result is `delta_cp == 0`, bucket `"good"`.
- `test_stalemating_move_scores_result_as_zero_without_second_engine_call`.
  Before-score 0 gives `delta_cp == 0`, and the analyser is called once.
- `test_context_carries_move_fields_and_versions`. Checks `fen == fen_before`,
  `move`, `san`, `prompt_version == 1`, `schema_version == 1`.
- `test_empty_analysis_raises_engine_unavailable`. Parametrized over the
  before and after positions returning `[]`.

### 5.2 `backend/tests/test_position_analysis.py` (no binary)

- `test_analyse_position_without_stockfish_path_raises_engine_unavailable`.
  Checks the key phrase `"engine unavailable"`, and that `popen_uci` is not
  called.
- `test_analyse_position_wraps_os_error_as_engine_unavailable`.
  `popen_uci` raises `FileNotFoundError`.
- `test_analyse_position_returns_lines_and_quits_engine`. A fake engine
  returns one info, the result is `[{"score_cp": ..., "pv": [...]}]`, and
  `quit` is awaited once.
- `test_analyse_position_quits_engine_when_analysis_fails`. The fake
  `analyse` raises `chess.engine.EngineError`, so `EngineUnavailableError` is
  raised and `quit` is still awaited.
- `test_get_position_analyser_returns_analyse_position`.
- `test_engine_unavailable_error_is_a_runtime_error`.

### 5.3 `backend/tests/test_coach_api.py` (`TestClient(app)`, fake analyser override)

- `test_explain_returns_200_with_exactly_four_string_keys`.
- `test_explain_mistake_returns_templated_card`. One `e2e4` move with fake
  scores giving delta 150 and `pv ["d2d4"]`. Expect exactly
  `{"verdict": "Mistake — 150 CP lost.", "praise": "The idea is understandable", "concern": "Gives away a clear edge", "tip": "Consider d2d4 instead."}`.
- `test_explain_reports_pin_on_opponent_in_praise` (`PIN_ON_OPPONENT`,
  move_id 5).
- `test_explain_reports_own_pinned_piece_in_concern` (`PIN_ON_OWN`, move_id 4).
- `test_explain_uses_move_id_as_zero_based_ply_index`. Two moves
  (`e2e4`, `e7e5`) with different fake scores per FEN. `move_id` 0 and 1
  return different verdicts that match their own scores.
- `test_explain_unknown_game_returns_404`. Key phrases `"explain move failed"`
  and `"no game with id"`.
- `test_explain_move_id_out_of_range_returns_404`. Parametrized: a game with
  1 move and `move_id` 1, and a game with no moves and `move_id` 0. Key phrase
  `"no move with id"`.
- `test_explain_negative_move_id_returns_422_with_string_detail`.
  `isinstance(detail, str)`, and the detail contains `"move_id"`.
- `test_explain_missing_field_returns_422_with_string_detail`. Parametrized
  over a missing `game_id` and a missing `move_id`.
- `test_explain_unknown_game_does_not_call_engine` and
  `test_explain_out_of_range_move_does_not_call_engine`. The fake records zero
  calls.
- `test_explain_engine_unavailable_returns_503`. The fake raises
  `EngineUnavailableError`. Key phrases `"explain move failed"` and
  `"engine unavailable"`.
- `test_explain_does_not_change_game_history`. `GET /api/games/{id}` before
  and after gives an identical body.
- `test_explain_after_takeback_explains_the_replacement_move`. Documents
  decision-006 as current behavior: play `e2e4`, take it back, play `d2d4`,
  explain move_id 0. The analyser is called with `d2d4`'s `fen_after` (the
  new move), and the request succeeds. No 409.

### 5.4 Reviewer-only checks (not tests)

- `app/services/coach.py` and `position_analysis.py` do not import `fastapi`
  or `app.api`. No new file imports `openai` or reads any env var other than
  `STOCKFISH_PATH` (and that only via `engine.open_engine`).
- Docstrings, type hints, `_` private helpers, module loggers, and no
  `print`.
- No existing file is modified except the Q1-approved lines in `main.py`.

## 6. Files

Create (implementer):
- `backend/app/services/position_analysis.py`
- `backend/app/services/coach.py`
- `backend/app/api/coach.py`

Create (tester):
- `backend/tests/test_coach.py`
- `backend/tests/test_position_analysis.py`
- `backend/tests/test_coach_api.py`

**Requires an edit to an existing file (blocked, see Q1):**
- `backend/app/main.py`: add `from app.api.coach import router as coach_router`
  next to the other router imports, and `app.include_router(coach_router)`
  after `app.include_router(games_router)`. Two lines, nothing else.

There is no way to wire the router without editing an existing file.
FastAPI routes are reachable only through `app.include_router` on the `app`
object in `main.py`. Nothing auto-discovers modules under `app/api/`, and an
import-side-effect hack (for example from a new `app/api/__init__.py`) would
create a circular import with `main.py`. That hack is rejected. Without the
edit, all of 5.3 returns 404 Not Found and cannot go green.

Do not touch: `routes.py`, `games.py`, `game_store.py`, `moves.py`,
`engine.py`, `classify.py`, `tactics.py`, `conftest.py`, `pyproject.toml`
(no new dependencies), `ai_chess_coach_project_plan.md` (the Phase 5
checkboxes stay unticked because this is a partial slice), `.memory/`, and
`.claude/`.

## 7. Notes for the tester

- `backend/.pytest_cache/v/cache/nodeids` lists stale ids such as
  `tests/test_coach_api.py::test_fallback_is_not_cached_so_a_later_click_reaches_the_llm`.
  No `test_coach_api.py` exists. These ids are leftovers from an earlier
  attempt and describe an LLM and cache design that is **out of scope**.
  Ignore them and use the names in section 5.
- Red is expected as `ModuleNotFoundError` for `app.services.coach`,
  `app.services.position_analysis` and `app.api.coach`. Until `main.py` is
  wired, API tests that import only `app.main` would fail with 404 instead.
- Build the expected strings from the table in 2.3, written out literally. Do
  not import template constants from the implementation.

## 8. Out of scope

- Any real LLM call: OpenAI SDK, `base_url`/`api_key`/`model` env vars, Groq
  or OpenAI configuration, JSON mode, prompt text, `@pytest.mark.llm` tests
  (plan lines 71-72).
- The LLM explanation cache and its hash key (plan line 82). Phase 2's
  evaluation cache is also out, so each "Why?" opens Stockfish and runs two
  analyses at most.
- decision-006 takeback guard: no `fen_before` field on the request and no
  409 path (Q3).
- Forks, file control and relative pins as alerts. Only absolute pins
  (`find_pins`) feed alerts.
- Returning the context (`delta_cp`, `bucket`, `best_line`, and so on) or a
  `source` field in the response. The response is exactly the four keys.
- The per-move analysis payload (Phase 4), any frontend or "Why?" button
  (Phase 6), and fixing the OpenAPI 422 schema gap noted in decision-004.
- SAN in the tip. The tip uses the UCI best move.
- Memory entries. The orchestrator or human records decisions after H1.

## 9. Open questions for the human (H1)

- **Q1 (blocking): wiring `main.py`.** The router must be included in
  `backend/app/main.py`, which is an existing file the implementer may not
  edit. Options:
  (a) **Recommended:** approve a one-time, two-line edit by the implementer,
  exactly as in section 6.
  (b) The human makes those two lines themselves before the green run.
  (c) Ship the router unwired, so section 5.3 cannot pass. Not recommended.
- **Q2: engine failure → 503 or degrade?** The plan's "Why? always responds"
  (line 83) is about LLM failure, but with no engine there is no bucket to
  template from. The spec returns 503 `engine unavailable`. Alternative: return
  200 with a bucket-less generic card. Confirm 503.
- **Q3: decision-006 `move_id` reuse after takeback.** This slice explains
  whatever move sits at that index now, and
  `test_explain_after_takeback_explains_the_replacement_move` locks in that
  current behavior. Options for later: the client clears per-move UI on
  takeback, or a later slice adds an optional `fen_before` and a 409. That
  test would then need to change. Not built here, as instructed.
- **Q4: alert vocabulary.** The plan's example uses bare motif names
  (`"pin"`, `"fork"`, line 66). Templating needs to know who is pinned, so
  this spec uses `"own_piece_pinned"` / `"opponent_piece_pinned"`. Accept, or
  prefer `"pin"` plus a separate direction field?
- **Q5: template wording.** The exact strings in 2.3 are planner-chosen. The
  human may reword them before the tester freezes them, as long as the
  line-81 shape rules hold.
- **Q6: checkmate/game-over shortcut.** The spec skips the engine for a
  game-over `fen_after` (mate gives `-MATE_SCORE`, other endings give 0) so
  terminal positions never depend on Stockfish's behavior there. Confirm.
