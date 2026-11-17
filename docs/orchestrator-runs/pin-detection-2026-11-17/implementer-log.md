# Implementer log: pin-detection-2026-11-17

Round: 1 of at most 3. Date: 2026-11-17.
Inputs: spec.md (v3), red-proof.md, `backend/tests/test_tactics.py` (frozen, not modified).
Regression status: **pending**. The implementer has no test runner, so the tester's green re-run is the check.

## Files created

- `backend/app/services/tactics.py` (new). Nothing else was created or modified apart from this log.

No router, schema, endpoint, `main.py`, `services/__init__.py`, test, conftest or `.memory/` change.

## Approach

Purely geometric check that follows spec section 2, contract item 5. For each color C, take C's king K. For every enemy
bishop, rook and queen S, `_slider_matches_line` checks that S moves along the K-S line (rook/queen for same rank or
file, bishop/queen for equal file and rank gaps, otherwise no line). Then `chess.between(K, S) & board.occupied` must
hold exactly one square, and the piece on it must be C's own. The pinner is S itself, so the "`board.pin()` returns
the whole line" problem from the spec note does not come up (`board.pin()` / `is_pinned()` are not used). Both colors
are collected and sorted by `chess.parse_square(pinned_square)`. Color and piece names come from `chess.COLOR_NAMES` /
`chess.PIECE_NAMES`. Parsing is in `_parse_board`, with a local `_status_names` copy (moves.py is not imported).

## Test-to-code map (red-proof.md, 11 functions / 27 cases)

Line numbers refer to `backend/app/services/tactics.py`.

| Test (cases) | Code meant to make it pass |
|---|---|
| import of `Pin, TacticsError, find_pins` (red reason) | module exists; `TacticsError` :15, `Pin` :19-27, `find_pins` :92-98 |
| `test_absolute_pin_is_reported_with_squares_color_and_piece_type` (4) | `_slider_matches_line` :52-60, `_pins_against` :63-89 |
| `test_queen_is_a_pinner_on_files_and_diagonals` (2) | queen is in both `_ORTHOGONAL_SLIDERS` :10 and `_DIAGONAL_SLIDERS` :11 |
| `test_pinned_piece_that_can_move_along_the_line_is_still_a_pin` (3) | geometric only, no mobility or legality check, :73-79 |
| `test_line_without_absolute_pin_returns_no_pins` (7) | blocker is the slider's colour :78-79; 2+ blockers :73-75; slider/line mismatch :71-72 with :56-60; own-colour slider never scanned :70 (`not color`) |
| `test_position_without_pins_returns_empty_list` (2) | new list built per call :95, `[]` when nothing matches |
| `test_pins_for_both_sides_are_reported_in_one_position` (1) | both colours :95 |
| `test_pins_are_ordered_by_pinned_square_not_by_color` (1) | sort by square index :96 |
| `test_result_does_not_depend_on_side_to_move` (1) | turn never read; both colours always scanned :95 |
| `test_pin_is_frozen_dataclass_with_square_name_fields` (1) | `@dataclass(frozen=True)` and field order :19-27; `chess.square_name` :82-84; names :85-86 |
| `test_invalid_fen_raises_tactics_error` (4) | `_parse_board` :36-49: (a) parse `ValueError` -> `TacticsError ... from exc` :40-43 (`garbage`; `empty`, where python-chess raises `ValueError("empty fen")`); (b) `not is_valid()` :44-48 (`no-kings`, `opposite-side-in-check`). No prefix. Contains `invalid FEN`, `repr(fen)` and `expected` |
| `test_tactics_error_is_a_value_error` (1) | `class TacticsError(ValueError)` :15 |

Every case was traced by hand against the spec FENs, for example the ordering FEN: b2 (index 9, black, pinned by f6)
comes before h7 (index 55, white, pinned by h1). The g7-b2 diagonal from h8 holds two pieces (f6, b2), so it gives no
extra pin. All 27 are expected to pass. None are known to be blocked.

## Interface and contract (service, not a route)

No HTTP routes. This is a service module only (spec section 1). Public interface, from spec section 2:

- `TacticsError(ValueError)`: spec section 3, Q2.
- `Pin(pinned_square, pinner_square, king_square, pinned_color, pinned_piece)`, frozen: spec section 2, contract
  items 1, 6 and 7.
- `find_pins(fen: str) -> list[Pin]`: contract items 2-5 and 8. Pure, with no I/O, engine, LLM or global mutable
  state (item 9). One DEBUG log line with the pin count and canonical FEN (item 10).
- Errors (spec section 3): (a) `invalid FEN {fen!r} ({reason}); expected a valid FEN string`, chained `from exc`;
  (b) `invalid FEN {fen!r} (illegal position: {flags}); expected a reachable chess position`.
- Plan source: `ai_chess_coach_project_plan.md` line 43 (Phase 3 pin detection, absolute half only) and the
  section 3 "Per-move path" python-chess Tactics bullet. No LLM is used, so the per-move path stays LLM-free.

## Mocking

None (spec section 4). The module depends only on python-chess. There is no Stockfish and no LLM to replace.

## Loop findings addressed

None. This is round 1.

## Deferred / follow-ups

- Relative pins, the en passant rank pin, forks and file control are out of scope (spec section 8).
- Shared-code follow-up (not done): `_status_names` and FEN parse/validate now exist in both `moves.py` and
  `tactics.py`. A later shared helper (e.g. `app/services/fen.py`) could remove the duplication. Spec section 8 marks
  this refactor out of scope.
- The `_slider_matches_line` signature line is about 104 characters long. Lint is not a gate (decision-009), but
  ruff's E501 would flag it if the knowledge standards' ruff rule were applied.
- Wiring into the per-move payload is Phase 4 and is not done.
