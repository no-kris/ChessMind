# Spec: absolute pin detection service (Phase 3, first slice)

Run-id: `pin-detection-2026-11-17`
Author role: Planner
Status: awaiting H1 approval (revision 3)

## Changes since v1

Based on the human's H1 #1 answers (relayed; see `log.md`, "Stage 2: H1 #1"):

1. **Q1 (no prefix):** removed the `find pins failed: ` prefix from both
   message formats in section 3. Messages now match `moves.py` exactly in
   style. The router adds `"<operation> failed: "` (decision-004,
   `backend/app/api/games.py:107`). Dropped
   `test_invalid_fen_error_names_the_operation`. The parametrized
   `test_invalid_fen_raises_tactics_error` now also asserts the `repr` of the
   bad input and `"expected"` for every case, so both the parse-failure and
   `is_valid()`-failure branches are checked. The section 1 standards bullet
   now notes that the router names the operation.
2. **Q3 (squares + color + type):** `Pin` gains `pinned_color: str`
   (`"white"`/`"black"`) and `pinned_piece: str` (`"pawn"`, `"knight"`,
   `"bishop"`, `"rook"`, `"queen"`) after the three square fields (section
   2, contract items 6–7). Every expected `Pin` in section 5 now lists all five
   fields. Test 5.7 also asserts the field order and the new field values.
   Removed the Q3 item from section 8.
3. Section 9: Q1–Q4 marked resolved with the human's answers. Status set to
   "awaiting H1 approval (revision 2)".

Nothing else changed.

## Changes since v2

Based on the human's H1 #2 request (relayed; see `log.md`, "Stage 2: H1 #2"):

1. **Black non-knight pin:** added case `rook-on-rank-black-bishop` to 5.1:
   FEN `8/8/R2b3k/8/8/8/8/4K3 w - - 0 1`, expected
   `[Pin("d6", "a6", "h6", "black", "bishop")]`.
2. **Pinned queen:** added case `queen-pinned-on-diagonal` to 5.3: FEN
   `7k/8/8/4q3/8/8/KB6/8 b - - 0 1`, expected
   `[Pin("e5", "b2", "h8", "black", "queen")]`. The 5.3 note now names the
   along-the-line move for this case (`e5d4`, Black to move).
3. Updated the "Coverage of the new fields" paragraph in section 5.
4. **No-prefix assertion (Q1):** `test_invalid_fen_raises_tactics_error`
   (5.8, all four cases, so both failure branches) now also asserts
   `not str(exc_info.value).startswith("find pins failed")`.
5. **Rename:** the 5.1 test
   `test_absolute_pin_is_reported_with_pinned_pinner_and_king_squares` is now
   `test_absolute_pin_is_reported_with_squares_color_and_piece_type`. The 5.7
   reference to the 5.1 `rook-on-file` case now names the new test.
6. **Duplicate removed:** deleted
   `test_invalid_fen_error_names_bad_input_and_expectation` from 5.8.
7. Status set to "awaiting H1 approval (revision 3)". Section 9 records the
   H1 #2 request as resolved.

Nothing else changed.

## 1. Goal

Add a pure service module `backend/app/services/tactics.py` that takes a FEN
and returns every **absolute pin** for **both** sides. An absolute pin is an
enemy bishop, rook or queen on a line with a king, with exactly one piece
between them, and that piece is the king's own color. Each pin gives three
squares (the pinned piece, the pinning piece and the king), plus the pinned
piece's color and type.

This is a service module only. No router, endpoint, schema or `main.py`
change.

### Source in the plan

- `ai_chess_coach_project_plan.md` line 43 (Phase 3): "Implement pin detection
  using `board.is_pinned()` and custom relative pin calculations in Python."
  This spec covers only the **absolute** half of that bullet. Relative pins
  are out of scope (section 8), so the plan checkbox stays unticked.
- Section 3 "Per-move path": "python-chess Tactics — detects pins, forks, file
  control". This module is the pin part. Wiring it into the per-move payload
  is Phase 4 and is out of scope.

### Standards and decisions applied

- `.memory/knowledge/coding-standards.md`: docstring on every function and
  class, type hints on every signature, `logger = logging.getLogger(__name__)`,
  `_` prefix for private helpers, `UPPER_SNAKE_CASE` constants, error messages
  name the bad input and what was expected. The operation is named by the
  router that wraps the service (`"<operation> failed: "`), not by the
  service message (decision-004; human answer to Q1).
- `.memory/knowledge/testing-standards.md`: one test file per module, behavior
  names, `@pytest.mark.parametrize` for repeated cases, explicit expected
  values, public interface only, one happy-path and one failure test as a
  minimum.
- decision-002: tests go in `backend/tests/`.
- decision-004: services never import FastAPI and raise domain errors. A FEN
  that parses but fails `board.is_valid()` counts as an invalid FEN.
- decision-009: lint is not a gate. pytest only.

## 2. Public interface (exact)

Module: `backend/app/services/tactics.py`

```python
logger = logging.getLogger(__name__)

class TacticsError(ValueError):
    """Raised when a tactics query gets input it cannot analyse, such as an invalid FEN."""

@dataclass(frozen=True)
class Pin:
    """One absolute pin: a piece that cannot leave its line without exposing its own king."""
    pinned_square: str   # e.g. "e2"
    pinner_square: str   # e.g. "e8"
    king_square: str     # e.g. "e1"
    pinned_color: str    # "white" or "black": the pinned piece's (and king's) color
    pinned_piece: str    # "pawn", "knight", "bishop", "rook" or "queen"

def find_pins(fen: str) -> list[Pin]:
    """Return every absolute pin for both colors in the position, ordered by pinned square."""
```

Field order is exactly as above:
`pinned_square, pinner_square, king_square, pinned_color, pinned_piece`.

Contract:

1. **Square format:** lowercase algebraic square names as produced by
   `chess.square_name` (`"a1"` to `"h8"`).
2. **Return type:** a new `list[Pin]` on each call. No pins gives `[]` (an
   empty list, not `None`).
3. **Ordering (deterministic):** ascending by the python-chess square index of
   `pinned_square` (`a1=0, b1=1, ..., h1=7, a2=8, ..., h8=63`). This key is
   unique because a square holds at most one piece and a piece can be
   absolutely pinned along at most one line. Color is **not** a sort key, so
   a black pin on `b2` comes before a white pin on `h7`.
4. **Both sides:** pins are reported for White and Black regardless of the
   side to move. Changing only the side-to-move field (keeping the position
   valid) does not change the result.
5. **What counts as a pin.** A piece P of color C is reported iff all of these
   hold:
   - P is not C's king.
   - C's king K and an enemy slider S are on one line through P. The slider
     must match the line: a rook or queen on a rank or file, a bishop or
     queen on a diagonal.
   - P is the only piece on the squares strictly between K and S.
   `pinner_square` is S's square. The test is purely geometric. A pinned
   piece that can still move along the line (for example a rook pinned on a
   file, or a pawn that can push) is still a pin.
6. **`pinned_color`:** the color C of the pinned piece, which is also the
   king's color. Exactly `"white"` or `"black"` (lowercase), the same strings
   as `chess.COLOR_NAMES[color]`.
7. **`pinned_piece`:** the pinned piece's type, as a lowercase English name,
   the same strings as `chess.PIECE_NAMES[piece_type]`. Value set: `"pawn"`,
   `"knight"`, `"bishop"`, `"rook"`, `"queen"`. `"king"` never appears,
   because a king cannot be pinned (item 5).
8. **Not a pin:**
   - the only blocker is the slider's color;
   - two or more pieces between slider and king, whatever their colors;
   - the slider does not match the line (a rook on a diagonal, a bishop on a
     file or rank);
   - the slider is the king's own color.
9. **Purity:** no I/O, no engine, no LLM, no global state. The function does
   not mutate anything shared.
10. **Logging:** define the module logger as above. The function creates,
   updates and deletes nothing, so no INFO log is required. A single DEBUG
   line (canonical FEN and pin count) is allowed. Do not use `print`.

Implementation note (not a test contract): `chess.Board.is_pinned(color,
square)` finds pinned pieces. `chess.Board.pin(color, square)` returns the
**whole line** through the king (both directions, edge to edge), not just
king-to-pinner. So the pinner has to be found separately: it is the enemy
slider S on that line where `chess.SquareSet.between(king, S)` contains only
the pinned square. Private helpers must use a `_` prefix. Do not import from
or modify `moves.py`. In particular, do not import its private
`_status_names`. Write a local equivalent if needed.

## 3. Error behavior (exact)

- Error class: **new** `TacticsError(ValueError)` in `tactics.py`. `MoveError`
  is not reused because its name and docstring are about moves (Q2, resolved).
- `find_pins` raises `TacticsError` (never an HTTP error, never a bare
  `ValueError`) when:
  - (a) `chess.Board(fen)` raises `ValueError` (unparseable or empty FEN), or
  - (b) the board parses but `board.is_valid()` is `False` (for example no
    kings, or the side not to move is in check). This follows decision-004
    (Q4, resolved).
- Message format: the problem only, with no operation prefix. This is the
  same style as `moves.py` (Q1, resolved). A future router adds
  `"<operation> failed: "`, as `backend/app/api/games.py:107` does for
  `MoveError`.
  - (a) `invalid FEN {fen!r} ({python-chess reason}); expected a valid FEN string`
  - (b) `invalid FEN {fen!r} (illegal position: {status flag names}); expected a reachable chess position`
- When (a) applies, chain the original exception (`raise ... from exc`).
- Tests assert key phrases only, never the whole string: `"invalid FEN"`,
  the `repr` of the bad input, and `"expected"`.

## 4. Mocking

None. The module uses only `python-chess`. No Stockfish (`@pytest.mark.engine`
is not used), no LLM (`@pytest.mark.llm` is not used), no network and no
fixtures files. Tests need no env vars.

## 5. Acceptance criteria (test names for `backend/tests/test_tactics.py`)

All FENs below have been checked by hand: both kings present, no pawns on
ranks 1 or 8, castling and en passant set to `-`, and the side not to move
not in check. Expected values are written as
`Pin(pinned_square, pinner_square, king_square, pinned_color, pinned_piece)`,
positionally in the field order of section 2. Every expected `Pin` lists all
five fields. Because the tests compare whole `Pin` values with `==`, every
test in 5.1, 5.2, 5.3 and 5.6 asserts `pinned_color` and `pinned_piece` as
well as the squares. Test 5.7 also checks them by attribute.

Coverage of the new fields across these cases: `pinned_color` `"white"` in
`rook-on-rank`, `rook-on-file`, `queen-on-diagonal`, `rook-pinned-on-file`,
`pawn-pinned-on-file` and one pin in each 5.6 test. `"black"` in
`rook-on-rank-black-bishop`, `bishop-on-diagonal`, `queen-on-file`,
`queen-pinned-on-diagonal` and one pin in each 5.6 test. `pinned_piece`
covers all five values: `"pawn"`, `"knight"`, `"bishop"`, `"rook"` and
`"queen"` (`"queen"` in `queen-pinned-on-diagonal`). Black pinned pieces
cover `"knight"`, `"bishop"` (`rook-on-rank-black-bishop`) and `"queen"`
(`queen-pinned-on-diagonal`).

### 5.1 Happy path: one pin per line type (parametrized)

`test_absolute_pin_is_reported_with_squares_color_and_piece_type`, with
these cases (`id`, FEN, expected):

| id | FEN | expected |
|---|---|---|
| `rook-on-rank` | `4k3/8/8/8/K1N4r/8/8/8 w - - 0 1` | `[Pin("c4", "h4", "a4", "white", "knight")]` |
| `rook-on-rank-black-bishop` | `8/8/R2b3k/8/8/8/8/4K3 w - - 0 1` | `[Pin("d6", "a6", "h6", "black", "bishop")]` |
| `rook-on-file` | `k3r3/8/8/8/8/8/4B3/4K3 w - - 0 1` | `[Pin("e2", "e8", "e1", "white", "bishop")]` |
| `bishop-on-diagonal` | `6k1/5n2/8/8/8/1B6/8/4K3 w - - 0 1` | `[Pin("f7", "b3", "g8", "black", "knight")]` |

`rook-on-rank-black-bishop` check: white rook a6, black bishop d6, black king
h6 (b6, c6, e6, f6, g6 empty); white king e1. Black (not to move) is not in
check because d6 blocks the a6 rook. The h6 king's other lines (h-file, g7–f8,
g5–c1) and all eight lines from e1 are empty, so this is the only pin.

### 5.2 Queen as the only slider (parametrized)

`test_queen_is_a_pinner_on_files_and_diagonals`

| id | FEN | expected |
|---|---|---|
| `queen-on-file` | `4k3/8/8/4n3/8/8/4Q3/K7 w - - 0 1` | `[Pin("e5", "e2", "e8", "black", "knight")]` |
| `queen-on-diagonal` | `q3k3/8/8/8/8/8/6R1/7K w - - 0 1` | `[Pin("g2", "a8", "h1", "white", "rook")]` |

### 5.3 Pinned piece that can still move along the line (parametrized)

`test_pinned_piece_that_can_move_along_the_line_is_still_a_pin`

| id | FEN | expected |
|---|---|---|
| `rook-pinned-on-file` | `k3r3/8/8/8/4R3/8/8/4K3 w - - 0 1` | `[Pin("e4", "e8", "e1", "white", "rook")]` |
| `pawn-pinned-on-file` | `k3r3/8/8/8/8/8/4P3/4K3 w - - 0 1` | `[Pin("e2", "e8", "e1", "white", "pawn")]` |
| `queen-pinned-on-diagonal` | `7k/8/8/4q3/8/8/KB6/8 b - - 0 1` | `[Pin("e5", "b2", "h8", "black", "queen")]` |

`queen-pinned-on-diagonal` check: black king h8, black queen e5, white bishop
b2 on the a1–h8 diagonal (g7, f6, d4, c3 empty); white king a2. Black is to
move, and White (not to move) is not in check: the e5 queen's lines (e-file,
rank 5, b8–h2 and a1–h8 diagonals) do not reach a2. The h8 king's other lines
(rank 8, h-file) are empty. From a2, the only piece on any line is White's own
b2 bishop, with c2–h2 empty behind it, so White has no pin.

The test may also assert, with python-chess and test-side only, that a move
along the line is legal (`e4e5`, `e2e3` and `e5d4` respectively). This shows
the precondition holds.

### 5.4 No pin (parametrized, all expect `[]`)

`test_line_without_absolute_pin_returns_no_pins`

| id | FEN | why no pin |
|---|---|---|
| `blocker-same-color-as-pinner-file` | `k3r3/8/8/8/4p3/8/8/4K3 w - - 0 1` | only blocker (e4) is black, like the rook |
| `blocker-same-color-as-pinner-diagonal` | `6k1/8/8/3N4/8/1B6/8/4K3 w - - 0 1` | only blocker (d5) is white, like the bishop |
| `two-own-pieces-between` | `k3r3/8/8/8/8/4B3/4N3/4K3 w - - 0 1` | e2 and e3 both between |
| `two-mixed-pieces-between` | `k3r3/8/8/8/4p3/8/4N3/4K3 w - - 0 1` | e2 (white) and e4 (black) between |
| `bishop-on-file` | `k3b3/8/8/8/8/8/4N3/4K3 w - - 0 1` | bishop cannot pin on a file |
| `rook-on-diagonal` | `6k1/5n2/8/8/8/1R6/8/4K3 w - - 0 1` | rook cannot pin on a diagonal |
| `own-slider-behind` | `4R3/8/k7/8/8/8/4N3/4K3 w - - 0 1` | e8 rook is the king's own color |

### 5.5 Positions with no pins at all (parametrized)

`test_position_without_pins_returns_empty_list`. Assert `== []` and
`isinstance(result, list)`.

| id | FEN |
|---|---|
| `start-position` | `rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1` |
| `bare-kings` | `4k3/8/8/8/8/8/8/4K3 w - - 0 1` |

### 5.6 Both sides, ordering and side to move

- `test_pins_for_both_sides_are_reported_in_one_position`
  FEN `4r1k1/5n2/8/8/8/1B6/4B3/4K3 w - - 0 1`.
  Expected `[Pin("e2", "e8", "e1", "white", "bishop"), Pin("f7", "b3", "g8", "black", "knight")]`.
- `test_pins_are_ordered_by_pinned_square_not_by_color`
  FEN `7K/7N/5B2/8/8/8/1n6/k6r w - - 0 1`.
  Expected `[Pin("b2", "f6", "a1", "black", "knight"), Pin("h7", "h1", "h8", "white", "knight")]`
  (the black pin comes first).
- `test_result_does_not_depend_on_side_to_move`
  FEN `7K/7N/5B2/8/8/8/1n6/k6r b - - 0 1` (the same position with Black to
  move) gives the same expected list as the previous test.

### 5.7 Return shape

- `test_pin_is_frozen_dataclass_with_square_name_fields`: on the `rook-on-file`
  case of `test_absolute_pin_is_reported_with_squares_color_and_piece_type`
  (5.1):
  - `[f.name for f in dataclasses.fields(Pin)] == ["pinned_square",
    "pinner_square", "king_square", "pinned_color", "pinned_piece"]`;
  - `result[0].pinned_square == "e2"`, `result[0].pinner_square == "e8"`,
    `result[0].king_square == "e1"`, `result[0].pinned_color == "white"`,
    `result[0].pinned_piece == "bishop"`;
  - assigning to a field raises `dataclasses.FrozenInstanceError`.

### 5.8 Failure: invalid FEN (parametrized)

`test_invalid_fen_raises_tactics_error`, with
`pytest.raises(TacticsError) as exc_info`. For every case, `str(exc_info.value)`
contains `"invalid FEN"`, `repr(input)` and `"expected"`, and the test also
asserts (Q1, no prefix):

```python
assert not str(exc_info.value).startswith("find pins failed")
```

Because this assertion is in the parametrized test, it covers both the
parse-failure branch (a) and the `is_valid()`-failure branch (b).

| id | input | reason |
|---|---|---|
| `garbage` | `"not a fen"` | parse failure |
| `empty` | `""` | parse failure |
| `no-kings` | `"8/8/8/8/8/8/8/8 w - - 0 1"` | parses, `is_valid()` false |
| `opposite-side-in-check` | `"4k3/8/8/8/8/8/8/4R1K1 w - - 0 1"` | parses, Black (not to move) is in check from e1 |

Further failure test:

- `test_tactics_error_is_a_value_error`: `issubclass(TacticsError, ValueError)`.

### 5.9 Reviewer-only checks (not tests)

- `tactics.py` does not import `fastapi` or anything from `app.api`.
- There is a docstring on the module, `TacticsError`, `Pin`, `find_pins` and
  every private helper. Every signature has type hints. Private helpers use
  the `_` prefix. The module logger is `logging.getLogger(__name__)`. There is
  no `print`.
- No files other than the two listed in section 6 are changed.

## 6. Files

Create:
- `backend/app/services/tactics.py`
- `backend/tests/test_tactics.py`

Do not touch:
- `backend/app/main.py` (it has a pre-existing, human-owned line-ending
  change)
- `backend/app/services/moves.py`, `classify.py`, `engine.py`, `game_store.py`
- any router, schema, `conftest.py`, `ai_chess_coach_project_plan.md`
  (checkbox stays unticked)
- `.memory/knowledge/`, `.memory/reference/`

No new dependencies. `python-chess` is already installed.

## 7. Notes for the tester

- `backend/.pytest_cache/v/cache/nodeids` already lists node ids such as
  `tests/test_tactics.py::test_absolute_pin_is_reported_with_pinned_pinning_and_king_squares[E2-bishop-on-diagonal]`.
  However, `backend/tests/test_tactics.py` does **not** exist. Treat that
  cache entry as stale and leftover from an earlier attempt. It is not a spec
  input. Use the test names in section 5.
- The red run should fail on `ImportError` / `ModuleNotFoundError` for
  `app.services.tactics` (or on missing names) before the implementation
  exists.

## 8. Out of scope

- Relative pins (a piece pinned to a queen, rook or other valuable piece
  rather than the king). These are the second half of plan line 43 and a
  later slice.
- En passant "horizontal" pins (two pawns between king and rook on a rank).
- Forks, file control, and the other Phase 3 bullets.
- Any API endpoint, router, Pydantic schema or change to the per-move
  payload (Phase 4). Also any change to `tactical_alerts` (Phase 5).
- Caching pin results.
- Refactoring the shared FEN validation out of `moves.py` (see Q2).
- Ruff or lint fixes (decision-009).
- Writing memory entries. The orchestrator or human records any decision
  after H1.

## 9. Open questions for the human (H1)

All four v1 questions were resolved at H1 #1 (answers relayed by the
coordinator, recorded in `log.md` "Stage 2: H1 #1"):

- **Q1: error message prefix. Resolved: "No prefix (Recommended)".** The
  service message contains only the problem (`invalid FEN 'x'; expected
  ...`), matching `moves.py` and decision-004. The router adds
  `"<operation> failed: "` (`backend/app/api/games.py:107`). Applied in
  section 3. `test_invalid_fen_error_names_the_operation` was dropped.
  Since v3, 5.8 asserts the message does not start with `"find pins failed"`.
- **Q2: error class. Resolved: "New TacticsError".**
  `TacticsError(ValueError)` in `tactics.py`. No change from v1.
- **Q3: `Pin` fields. Resolved: "Squares + color + type".** `Pin` keeps the
  three squares and adds `pinned_color` and `pinned_piece`, with the
  representation chosen by the planner (section 2, contract items 6–7).
- **Q4: invalid-but-parseable positions. Resolved: "Reject all invalid".**
  Any FEN where `board.is_valid()` is false raises `TacticsError`. No change
  from v1.

H1 #2 request (relayed by the coordinator, recorded in `log.md` "Stage 2: H1
#2"): **resolved in v3.** Black non-knight pin and pinned-queen cases added,
no-prefix assertion added, 5.1 test renamed, duplicate 5.8 test removed (see
"Changes since v2").

No new open questions.
