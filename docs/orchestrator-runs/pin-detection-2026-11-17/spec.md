# Spec: absolute pin detection service (Phase 3, first slice)

Run-id: `pin-detection-2026-11-17`. Status: draft for H1 human approval.

## Goal

Add a new service module `backend/app/services/tactics.py`. Given a FEN, it
returns every absolute pin for both sides. Each pin reports the pinned
piece's square, the pinning piece's square, the king's square and the colour
of the pinned side.

This is the first slice of the plan's Phase 3 pin item
(`ai_chess_coach_project_plan.md` line 43: "Implement pin detection using
`board.is_pinned()` and custom relative pin calculations in Python"). This
slice covers absolute pins only. Relative pins are a later slice (see Out of
scope).

## Context checked

- `backend/pyproject.toml`: `python-chess>=1.999` is already a runtime
  dependency, so the module uses `import chess`. **No new dependency is
  needed.**
- Existing service conventions (`backend/app/services/moves.py`,
  `game_store.py`):
  - Each service defines its own domain error as a subclass of a builtin
    exception (`MoveError(ValueError)` and so on).
  - Services do not import FastAPI.
  - Results are frozen dataclasses (`MoveResult`).
  - Read-only collections are tuples (`Game.history`).
  - An invalid FEN is either a FEN that `chess.Board(fen)` rejects with
    `ValueError`, or one that parses but fails `board.is_valid()`.
  - Error messages read `invalid FEN '<fen>' (<reason>); expected ...` and
    have no operation prefix.
- decision-004: services raise domain errors and only routers map them to
  HTTP. Message convention: problem plus what was expected, with no
  operation prefix. A FEN where `board.is_valid()` is false counts as an
  invalid FEN.
- decision-002: tests go in `backend/tests/`, one test file per module.
- Coding and testing standards: every function and class has a docstring;
  every signature has type hints; use `logging.getLogger(__name__)` and never
  `print`; use explicit expected values; use `parametrize` for repeated
  cases; check the error's key phrase, not the whole string.
- Memory: no entries used here are past their review date. decision-004 is
  user-confirmed (2026-11-17).

## Public interface (settled decisions)

```python
# backend/app/services/tactics.py
from typing import Literal

class TacticsError(ValueError): ...

@dataclass(frozen=True)
class Pin:
    pinned_square: str                 # e.g. "c3"
    pinning_square: str                # e.g. "b4"
    king_square: str                   # e.g. "e1"
    color: Literal["white", "black"]   # side of the pinned piece and its king

def find_pins(fen: str) -> tuple[Pin, ...]: ...
```

### Decision 1: output type and shape

- **Choice:** `find_pins(fen: str) -> tuple[Pin, ...]`. `Pin` is a
  `@dataclass(frozen=True)` with exactly four fields, in this order:
  1. `pinned_square: str`
  2. `pinning_square: str`
  3. `king_square: str`
  4. `color: Literal["white", "black"]`

  The three square fields each hold a lowercase algebraic square name
  (`"e4"`), the same format as `chess.square_name`. If there are no pins,
  the function returns an empty tuple `()`.
- **Reason:** This matches the existing `MoveResult` frozen dataclass and the
  read-only tuple pattern in `Game.history`. Square names are plain strings,
  so they work with JSON as-is for the Phase 4 payload. The square field
  names follow the goal's wording ("pinned piece's square", "pinning piece's
  square", "king's square").
- **Colour field (human answer to former Open question 1):** `color` is the
  side of the pinned piece and of the king it shields. Its runtime value is
  always the plain `str` `"white"` or `"black"` (lowercase, the same strings
  as `chess.COLOR_NAMES`). The annotation is `Literal["white", "black"]`.
  - **Reason for `Literal`:** it documents and type-checks the only two legal
    values, while the runtime value stays a plain `str` that serialises to
    JSON unchanged. A `chess.Color` bool was rejected because `true`/`false`
    is unclear in a JSON payload.
  - **Reason for placing it last:** the three square fields keep the
    positions the previous draft gave them, so positional construction only
    gains a fourth argument.
- `Pin` has no piece-type field (see Out of scope).

### Decision 2: invalid FEN behaviour

- **Choice:** `find_pins` raises `TacticsError(ValueError)`, defined in
  `backend/app/services/tactics.py`. It does this in two cases:
  - `chess.Board(fen)` raises `ValueError`. This covers malformed text and
    the empty string.
  - The FEN parses but `board.is_valid()` is false. This covers no kings,
    the side not to move being in check, and similar cases.
- The message starts with the key phrase `invalid FEN`. It follows the
  decision-004 convention: problem plus "expected ...", with no operation
  prefix. Example:
  `invalid FEN 'not a fen' (<parser reason>); expected a valid FEN string`.
  For the `is_valid()` case it should say the position is illegal and that a
  reachable chess position was expected, like `moves.py`.
- The error is raised with `from exc` when it wraps the parser error.
- **Reason:** decision-004 says services raise domain errors and never touch
  HTTP. Subclassing `ValueError` means a future router can map it to 400,
  just like `MoveError`. Defining the error in the new module keeps all
  production changes in new files. A shared errors module would mean editing
  existing files, which the human has kept out of scope for this run.
- The implementer must **not** import private helpers from `moves.py` (for
  example `_status_names`). Copying a small amount of validation code is
  acceptable. Unifying it is out of scope.

### Decision 3: ordering

- **Choice:** Return pins sorted by:
  1. the `color` field: **`"white"` first, then `"black"`**;
  2. within each colour, the pinned square's python-chess index, ascending
     (a1=0, b1=1, ..., h1=7, a2=8, ..., h8=63; rank-major from a1).
- The rule is now expressed via the `color` field. This is the same order as
  the previous draft's "colour of the king being pinned against", because
  `color` is by definition the king's side.
- **Implementation note:** the order is white-then-black, which is **not**
  alphabetical (`"black" < "white"`). Sorting on the raw `color` string
  would put black first and fail tests 6, 7 and 8. The sort key must map
  white before black explicitly.
- **Reason:** This is a simple, total and deterministic order that tests can
  state exactly. Each pinned square lies on exactly one ray from its king, so
  it can appear at most once, and the order never ties.

### Decision 4: scope and edge-case handling

- **Absolute pins only.** A pin is reported when all of the following hold:
  - a king K of colour C and an enemy sliding piece S share a line;
  - S's movement type matches the line: a rook or queen on a rank or file,
    a bishop or queen on a diagonal;
  - exactly one piece P sits on the squares strictly between K and S;
  - P has colour C.

  The pin is reported as `Pin(pinned_square=P, pinning_square=S,
  king_square=K, color=C)`, with C written as `"white"` or `"black"`.
- **Pinned piece colour:** The pinned piece is always the same colour as the
  king it shields, so `color` describes both. If the single piece between K
  and S belongs to S's side, nothing is reported. That is a
  discovered-attack battery, not a pin.
- **Pinned piece type:** Any non-king piece can be pinned: pawn, knight,
  bishop, rook or queen. A pin is reported whether or not the pinned piece
  can still move along the pin line or capture the pinner.
- **Not pins:**
  - zero pieces between K and S (that is a check);
  - two or more pieces between K and S;
  - a non-slider behind the piece (knight, pawn or king);
  - a slider whose movement type does not match the line (a rook on a
    diagonal, a bishop on a rank or file);
  - a slider of K's own colour behind the piece.
- **No pins:** Returns `()`.
- **Both sides pinned:** All pins for both kings are returned in one tuple,
  ordered by Decision 3. A piece can be pinned and also be a pinner at the
  same time, as in mutual rook pins on one file. Both pins are reported.
- **Multiple pins against one king:** All are returned, up to one per ray,
  ordered by pinned square.
- **Side to move:** Pins are geometric. The result does not depend on whose
  turn it is. The FEN must still pass `is_valid()`.
- **Purity:** The function is stateless and read-only. It creates, updates
  and deletes nothing, so the coding standard's create/update/delete logging
  rule does not apply. No logging is required, and it must not use `print`.
- **Implementation is not mandated:** The plan mentions
  `board.is_pinned()`. That method does not return the pinner's square, so
  the implementer may use `board.pin()`, attack masks or ray walking. Tests
  check only behaviour through `find_pins`.

## Behaviour statements with worked examples

All FENs below were checked by hand to pass `board.is_valid()`: both kings
are present and the side not to move is not in check. The expected values
come from chess rules, not from an implementation.

| # | FEN | Expected `find_pins` result |
|---|-----|-----------------------------|
| E1 | `rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1` | `()` |
| E2 | `4k3/8/8/8/1b6/2N5/8/4K3 w - - 0 1` (bishop on diagonal) | `(Pin("c3","b4","e1","white"),)` |
| E3 | `k7/8/8/8/4r3/8/4B3/4K3 w - - 0 1` (rook on file) | `(Pin("e2","e4","e1","white"),)` |
| E4 | `k7/8/8/8/8/8/8/r1N1K3 w - - 0 1` (rook on rank) | `(Pin("c1","a1","e1","white"),)` |
| E5 | `k7/8/8/8/8/8/8/K1R3q1 w - - 0 1` (queen on rank) | `(Pin("c1","g1","a1","white"),)` |
| E6 | `k7/8/8/8/7q/8/5P2/4K3 w - - 0 1` (queen on diagonal, pinned pawn) | `(Pin("f2","h4","e1","white"),)` |
| E7 | `k7/8/8/8/4r3/8/4Q3/4K3 w - - 0 1` (pinned queen) | `(Pin("e2","e4","e1","white"),)` |
| E8 | `k7/8/8/8/8/4r3/4R3/4K3 w - - 0 1` (pinner adjacent; pinned piece can capture it) | `(Pin("e2","e3","e1","white"),)` |
| E9 | `4k3/8/2n5/1B6/8/8/8/4K3 b - - 0 1` (black piece pinned) | `(Pin("c6","b5","e8","black"),)` |
| N1 | `4k3/8/8/8/1b6/2N5/3P4/4K3 w - - 0 1` (two own pieces between) | `()` |
| N2 | `4k3/8/8/8/1b6/2n5/8/4K3 w - - 0 1` (piece between is the pinner's own colour) | `()` |
| N3 | `k7/8/8/8/4R3/8/4B3/4K3 w - - 0 1` (own-colour slider behind) | `()` |
| N4 | `k7/8/8/8/4b3/8/4N3/4K3 w - - 0 1` (bishop on a file) | `()` |
| N5 | `k7/8/8/8/1r6/2N5/8/4K3 w - - 0 1` (rook on a diagonal) | `()` |
| N6 | `k7/8/8/8/8/4n3/4N3/4K3 w - - 0 1` (knight behind) | `()` |
| N7 | `4k3/8/8/8/1b6/8/8/4K3 w - - 0 1` (check with nothing between) | `()` |
| M1 | `k7/4r3/8/8/1b5q/8/3NBP2/4K3 w - - 0 1` (three pins on one king) | `(Pin("d2","b4","e1","white"), Pin("e2","e7","e1","white"), Pin("f2","h4","e1","white"))` |
| B1 | `4k3/4r3/8/8/8/8/4R3/4K3 w - - 0 1` (mutual rook pins) | `(Pin("e2","e7","e1","white"), Pin("e7","e2","e8","black"))` |
| B2 | `7K/6N1/5b2/8/8/2B5/1n6/k7 w - - 0 1` (both sides pinned; black's pinned square b2 has a lower index than white's g7) | `(Pin("g7","f6","h8","white"), Pin("b2","c3","a1","black"))` |
| S1 | B1 with `b` to move: `4k3/4r3/8/8/8/8/4R3/4K3 b - - 0 1` | same as B1: `(Pin("e2","e7","e1","white"), Pin("e7","e2","e8","black"))` |

`Pin("c3","b4","e1","white")` is shorthand for
`Pin(pinned_square="c3", pinning_square="b4", king_square="e1",
color="white")`. Tests may use either form; the keyword form is preferred
for readability.

Invalid FEN inputs, each of which raises `TacticsError` with a message
containing `invalid FEN`:

| # | FEN | Why |
|---|-----|-----|
| X1 | `not a fen` | parser rejects it |
| X2 | `""` (empty string) | parser rejects it ("empty fen") |
| X3 | `8/8/8/8/8/8/8/8 w - - 0 1` | parses, but no kings (`is_valid()` false) |
| X4 | `4k3/8/8/8/8/8/8/4RK2 w - - 0 1` | parses, but the side not to move is in check (`is_valid()` false) |

## Acceptance criteria (pytest test names, all in `backend/tests/test_tactics.py`)

Tests marked **[colour]** compare full `Pin` values, so they now assert the
`color` field as part of the expected result.

1. `test_starting_position_has_no_pins`: E1 returns `()`.
2. `test_absolute_pin_is_reported_with_pinned_pinning_and_king_squares`
   **[colour]**: parametrized over E2 to E8 (each pinner type and line,
   pinned pawn, pinned queen, adjacent pinner). Each returns exactly the one
   expected `Pin`, including `color="white"`.
3. `test_black_piece_pinned_against_black_king_is_reported` **[colour]**:
   E9, including `color="black"`.
4. `test_non_pin_lines_are_not_reported`: parametrized over N1 to N7. Each
   returns `()`.
5. `test_multiple_pins_against_one_king_are_all_reported_in_square_order`
   **[colour]**: M1 returns the exact three-element tuple.
6. `test_pins_for_both_sides_are_reported` **[colour]**: B1 returns both
   mutual pins, the first with `color="white"` and the second with
   `color="black"`.
7. `test_pins_are_ordered_white_king_first_then_by_pinned_square`
   **[colour]**: B2 returns the exact tuple. The `color="white"` pin comes
   first even though b2 has a lower index than g7. This test checks the
   Decision 3 order, which is now stated via the `color` field (name kept
   from the previous draft; `color` always equals the king's side).
8. `test_pins_do_not_depend_on_side_to_move` **[colour]**: B1 and S1 return
   equal results. Equality compares all four fields, so `color` is included
   implicitly; `color` must not follow the side to move.
9. `test_find_pins_returns_a_tuple`: the result type is `tuple`, for both a
   position with pins (E2) and one without (E1).
10. `test_pin_is_frozen`: assigning to a field of a returned `Pin` raises
    `dataclasses.FrozenInstanceError`.
11. `test_invalid_fen_raises_tactics_error`: parametrized over X1 to X4.
    `pytest.raises(TacticsError, match="invalid FEN")`.
12. `test_tactics_error_is_a_value_error`: `issubclass(TacticsError,
    ValueError)` is true, so a future router can map it to 400 like
    `MoveError` (decision-004).
13. **New:** `test_pin_color_matches_pinned_kings_side`: parametrized with
    explicit expected values: E2 -> `color == "white"`, E9 ->
    `color == "black"`. For each case it also asserts that the colour of the
    piece on `king_square` in the FEN is that side (via
    `chess.Board(fen).piece_at(chess.parse_square(pin.king_square)).color`
    mapped to `"white"`/`"black"`), so the field is tied to the king's side
    and not to the side to move or the pinner. (E9 has black to move and E2
    white to move; B1/S1 in test 8 cover the case where the side to move
    differs from a pin's colour.)
14. **New:** `test_pin_has_four_fields_in_order`: `[f.name for f in
    dataclasses.fields(Pin)] == ["pinned_square", "pinning_square",
    "king_square", "color"]`. This pins down the field order stated in
    Decision 1, which the positional shorthand relies on.

These cover the testing standard's minimum of one happy path and one failure
per new module. No test needs the `engine` or `llm` marker.

## Mocking

None needed. The module is pure python-chess: no Stockfish, no LLM, no
network, no filesystem and no in-memory store. Nothing needs mocking, and the
tests need no env vars.

## Files to create

- `backend/app/services/tactics.py`: `TacticsError`, `Pin`, `find_pins`.
  Private helpers are prefixed `_`. Every function and class has a docstring
  and every signature has type hints.
- `backend/tests/test_tactics.py`: the tests above (backend-tester).

No existing files change. No changes to `pyproject.toml` or `uv.lock`
(python-chess is already present). No changes to `conftest.py`, because
there is no state to reset.

## Out of scope

- Relative pins (against a queen, rook or other valuable piece), which the
  plan's "custom relative pin calculations" refers to. This is a later slice.
- Skewers, x-rays, discovered attacks and checks. Pins "through" two pieces
  are not reported.
- Forks and file control (the other Phase 3 bullets, plan lines 44-45).
- Any router, endpoint or HTTP mapping of `TacticsError`. Under decision-004
  this belongs to a later router change.
- Wiring pins into the per-move path, the Phase 4 JSON payload or Phase 5
  `tactical_alerts`.
- Caching pin results.
- Pin legality nuances such as the horizontal en-passant pin, and whether
  the pinned piece has legal moves.
- A piece-type field on `Pin`.
- Chess960/Shredder-FEN castling notation and variants.
- Accepting a `chess.Board` or non-`str` input.
- Refactoring `moves.py` to share FEN validation (human decision for this
  run).
- Any memory or decision-record entries. Recording `TacticsError` in
  decision-004 is done by the main session after the code lands, not by any
  role in this run.

## Resolved questions (human answers, 2026-11-17)

1. **Colour field on `Pin`:** yes. Added as `color`; see Decision 1.
2. **Shared FEN validation and errors:** stays out of scope for this run.
3. **Decision record for `TacticsError`:** the main session will add it to
   decision-004 (not a new decision) once the code is in place. This spec
   does not change memory.
4. **decision-004 review:** removed. The human confirmed decision-004; it is
   now marked user-confirmed.

## Open questions for the human

None.

## Revision history

Changes from the previous draft (same run-id, same status):

- **Goal:** now says each pin also reports the colour of the pinned side.
- **Context checked:** the memory note now says decision-004 is
  user-confirmed (2026-11-17), replacing "agent choice, not yet reviewed".
- **Public interface:** `Pin` gains a fourth field
  `color: Literal["white", "black"]`, placed last; `from typing import
  Literal` added to the sketch.
- **Decision 1:** "exactly three `str` fields" became four fields with a
  stated order; added the colour definition, the type choice and its
  reasons, and the reason for placing it last. Removed the sentence saying
  there is no colour field and the pointer to Open question 1.
- **Decision 2:** the two pointers to Open question 2 now say the shared
  validation is out of scope by human decision. No behaviour change.
- **Decision 3:** the ordering rule is now stated via the `color` field
  (same resulting order). Added the note that white-before-black is not
  alphabetical.
- **Decision 4:** the reported pin now includes `color=C`; the
  pinned-piece-colour bullet says `color` describes both the piece and the
  king.
- **Examples table:** E2 to E9, M1, B1, B2 and S1 now include colour (S1
  also spells out its tuple). The shorthand note now covers the four-field
  form.
- **Acceptance criteria:** tests 2, 3, 5, 6, 7 and 8 are marked as now
  asserting colour (wording updated). Added test 13
  `test_pin_color_matches_pinned_kings_side` and test 14
  `test_pin_has_four_fields_in_order`. Test names 1 to 12 are unchanged.
- **Out of scope:** "Piece-type or colour fields" became "A piece-type
  field"; the FEN-validation item notes it is a human decision; the
  memory item notes the main session will update decision-004.
- **Open questions:** all four moved to a new "Resolved questions" section
  with the human's answers. No open questions remain.
