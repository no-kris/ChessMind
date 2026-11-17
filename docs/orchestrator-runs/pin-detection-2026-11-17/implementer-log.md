# Implementer log: pin-detection-2026-11-17 (round 1 of max 3)

Author: implementer (endpoint-builder). Date: 2026-11-17.
Inputs: `spec.md` (approved at H1), `red-proof.md`, `backend/tests/test_tactics.py`,
`.memory/knowledge/coding-standards.md`, `docs/rubric-endpoint-builder.md`,
`.memory/project/decisions/decision-004.md`.

## Status

- Tests: **pending.** I have no test runner. The tester's green re-run is the check.
- Ruff: **pending.** I have no ruff. I wrote the module to default ruff rules
  (sorted imports: stdlib, then third-party `chess`; no unused names; lines <= 88).
  The pre-existing `EXE002` on `backend/app/main.py` is not mine and I did not touch it.
- Regression status of the 96 pre-existing tests: pending (no existing file changed).

## Files created

| Path | Kind |
|------|------|
| `backend/app/services/tactics.py` | new production module (`TacticsError`, `Pin`, `find_pins`) |
| `docs/orchestrator-runs/pin-detection-2026-11-17/implementer-log.md` | this log |

No existing file was modified. No test file was created or edited. No router,
endpoint or `app/api/**` file (decision-004: services only; spec Out of scope).
No dependency added (`python-chess` already in `backend/pyproject.toml`).
Nothing is imported from `moves.py`; the small validation helper is copied
(spec Decision 2 allows this).

`git status --short` after the build differs from the red-proof baseline only by
`?? backend/app/services/tactics.py` (plus the tester's `backend/tests/test_tactics.py`
and this log inside the already-untracked `docs/orchestrator-runs/`).

## Code layout (`backend/app/services/tactics.py`)

| Lines | What |
|-------|------|
| 9 | `PinColor = Literal["white", "black"]` |
| 11-12 | `_SIDES_IN_ORDER = (chess.WHITE, chess.BLACK)`: explicit white-then-black order (Decision 3), not a string sort |
| 14-17 | `_COLOR_NAMES`: `chess.Color` -> `"white"` / `"black"` (plain `str` at runtime) |
| 20-24 | ray step tables and slider sets: orthogonal -> rook/queen, diagonal -> bishop/queen |
| 27-28 | `class TacticsError(ValueError)` |
| 31-38 | `@dataclass(frozen=True) class Pin` with fields `pinned_square`, `pinning_square`, `king_square`, `color`, in that order |
| 41-44 | `_status_names` (copied from `moves.py`, not imported) |
| 47-60 | `_parse_fen`: parser `ValueError` -> `TacticsError ... from exc` (52-54); `is_valid()` false -> `TacticsError` (55-59) |
| 63-72 | `_ray`: walks squares out from the king to the board edge |
| 75-101 | `_pin_on_ray`: first piece must be own colour (89-91); the next piece must be an enemy slider matching the line (93-99); anything else gives no pin (90, 100, 101) |
| 104-116 | `_pins_for_side`: all 8 rays for one king, sorted by pinned square index (116) |
| 119-129 | `find_pins`: validate, then white's pins, then black's (126-129), returned as `tuple` |

## Failing tests in red-proof.md -> code meant to make them pass

All 14 tests (30 items) were red for one reason: `ModuleNotFoundError: No module
named 'app.services.tactics'` at `tests/test_tactics.py:12`. The new module fixes
that import. Behaviour per test:

| # | Test | Code (`backend/app/services/tactics.py`) |
|---|------|------------------------------------------|
| 1 | `test_starting_position_has_no_pins` | `_pin_on_ray:100` (second piece on each ray is an own piece or a non-slider) and `:101` (ray runs off the board) -> `find_pins:129` returns `()` |
| 2 | `test_absolute_pin_is_reported_with_pinned_pinning_and_king_squares` (E2-E8) | rays `:20-24`; pin built at `_pin_on_ray:93-99`, with the adjacent pinner (E8) handled because the walk does not require gaps; pinned pawn/queen (E6/E7): there is no piece-type check on the shield (`:88-92`) |
| 3 | `test_black_piece_pinned_against_black_king_is_reported` (E9) | `_SIDES_IN_ORDER:12` includes black; `color=_COLOR_NAMES[side]` `:98` gives `"black"` |
| 4 | `test_non_pin_lines_are_not_reported` (N1-N7) | N1 two own pieces -> `:100`; N2 enemy first -> `:90`; N3 own slider behind -> `:93` fails, `:100`; N4 bishop on file and N5 rook on diagonal -> slider-set mismatch at `:93`, `:100`; N6 knight -> `:100`; N7 check, enemy first -> `:90` |
| 5 | `test_multiple_pins_against_one_king_are_all_reported_in_square_order` (M1) | one pin per ray (`_pins_for_side:112-115`), sorted by square index `:116` -> d2, e2, f2 |
| 6 | `test_pins_for_both_sides_are_reported` (B1) | `find_pins:127-128` collects both kings; e2 is a shield for white and a pinner for black, which is allowed |
| 7 | `test_pins_are_ordered_white_king_first_then_by_pinned_square` (B2) | white first by tuple order `_SIDES_IN_ORDER:12` (not by sorting the `color` string), then index sort within side `:116` |
| 8 | `test_pins_do_not_depend_on_side_to_move` (B1/S1) | `board.turn` is never read; colour comes from the king's side `:98` |
| 9 | `test_find_pins_returns_a_tuple` | `find_pins:129` `return tuple(pins)` (also for no pins) |
| 10 | `test_pin_is_frozen` | `@dataclass(frozen=True)` `:31` |
| 11 | `test_invalid_fen_raises_tactics_error` (X1-X4) | X1/X2 parser error -> `_parse_fen:51-54`; X3 no kings / X4 opponent in check -> `:55-59`; both messages start with `invalid FEN` |
| 12 | `test_tactics_error_is_a_value_error` | `class TacticsError(ValueError)` `:27` |
| 13 | `test_pin_color_matches_pinned_kings_side` | `king_square` and `color` both come from the same `side` (`:97-98`, `_pins_for_side:106`) |
| 14 | `test_pin_has_four_fields_in_order` | field order `:35-38` |

## Contract (service API; there are no routes in this slice)

No HTTP routes, methods or status codes: spec "Out of scope" excludes any router
and HTTP mapping, and decision-004 says only routers map domain errors to HTTP.
`TacticsError(ValueError)` is ready for a later router to map to 400, like `MoveError`.

| Item | Behaviour | Spec | Plan |
|------|-----------|------|------|
| `find_pins(fen: str) -> tuple[Pin, ...]` | all absolute pins for both sides; `()` if none | Public interface; Decision 1; criteria 1, 9 | `ai_chess_coach_project_plan.md` line 43 (pin detection) |
| `Pin` | frozen dataclass: `pinned_square`, `pinning_square`, `king_square` (lowercase `chess.square_name`), `color` (`"white"`/`"black"`, plain `str`, annotated `Literal`) | Decision 1; criteria 10, 13, 14 | line 43 |
| Pin rule | king K, exactly one own piece P, then an enemy slider S whose type matches the line | Decision 4; criteria 2-4 | line 43 (absolute-pin slice only) |
| Ordering | white then black (explicit), then pinned square index ascending | Decision 3; criteria 5-7 | n/a |
| Side to move | ignored for detection; FEN must still be valid | Decision 4; criterion 8 | n/a |
| Error: unparseable FEN | `TacticsError("invalid FEN '<fen>' (<parser reason>); expected a valid FEN string")`, raised `from exc` | Decision 2; criterion 11 (X1, X2) | n/a (decision-004 message convention, no operation prefix) |
| Error: illegal position | `TacticsError("invalid FEN '<fen>' (illegal position: <STATUS_FLAGS>); expected a reachable chess position")` | Decision 2; criterion 11 (X3, X4) | n/a |
| Error type | `TacticsError` subclasses `ValueError` | Decision 2; criterion 12 | decision-004 error rule |

No LLM call, no Stockfish, no I/O, no state, no logging (spec Decision 4
"Purity": no create/update/delete, so the logging rule does not apply; no `print`).

## Mocking

None. The tests mock nothing (spec "Mocking"): the module is pure python-chess
with no LLM client, Stockfish, network, filesystem or store. There is nothing to replace.

## Spec readings I chose (for the reviewer to confirm)

- **Implementation method:** ray walking instead of `board.pin()`/`is_pinned()`,
  because those do not return the pinner's square (Decision 4 allows this).
- **Pin color annotation:** I added a module-level alias `PinColor =
  Literal["white", "black"]` and used it for `Pin.color`. This is equivalent to
  the spec's inline `Literal` and is public only as a type alias. If the
  reviewer wants the literal written inline, it is a one-line change.
- **`king is None` guard** in `_pins_for_side:107-108`: unreachable after
  `is_valid()`. It is there only so the type narrows to `chess.Square`. It is not
  behaviour.
- No open spec questions were hit; the spec lists none.

## Loop-round findings

Round 1: none received.

## Deferred / follow-ups

- Relative pins, skewers, forks, file control, routers and payload wiring are all
  out of scope per the spec and were not started.
- Follow-up (shared code, not done): FEN validation and `_status_names` are now
  duplicated between `moves.py` and `tactics.py`. Unifying them needs edits to
  `moves.py`, which the human kept out of scope for this run.
- Follow-up (main session, per spec Resolved question 3): record `TacticsError`
  -> 400 in decision-004.
- Risk for the verifier: decision-003 notes that new files can arrive with mode
  777, which ruff reports as `EXE002`. I cannot see or change file modes, and must
  not. If `EXE002` appears for `app/services/tactics.py`, a human should
  `chmod 644 backend/app/services/tactics.py`.
