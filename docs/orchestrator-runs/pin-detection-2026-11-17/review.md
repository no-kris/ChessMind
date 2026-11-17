# Review: pin-detection-2026-11-17, round 1

Reviewer stage. Date: 2026-11-17.
Inputs: `spec.md` (v3, approved at H1 #3), `backend/app/services/tactics.py` (new, the only production change),
`backend/tests/test_tactics.py`, `red-proof.md`, `green-report-round-1.md`, `implementer-log.md`,
`.memory/knowledge/coding-standards.md`, `.memory/knowledge/testing-standards.md`, decision-002, decision-004.

## Verdict: **pass**

No blocking findings. `tactics.py` matches the spec's interface, pin rule, ordering, error contract, purity and
logging rules. The test file covers every acceptance criterion in section 5 as written, and the green run shows
123 passed with exit 0, using a test file identical to the one in red-proof.md. Five findings are recorded below as
**non-blocking**. Four are test-coverage gaps: the tests would not catch a wrong implementation, but this
implementation is correct on each point, as checked by reading the code. They need a follow-up spec/test change and
should not go back to the implementer, who cannot edit the frozen tests. The fifth is a note about a pipeline file.

Per the orchestrator's instructions, these items were accepted at H1 #3 and are **not** raised: the section 3 last
bullet not mentioning the no-prefix check, the stale cache note in section 7, and the 5.7 test name
`test_pin_is_frozen_dataclass_with_square_name_fields`. The `backend/app/main.py` line-ending change is
pre-existing and human-owned, so it was ignored. Lint is not a gate (decision-009). The ~104-char line at
`tactics.py:52` is not a finding.

## Findings (all non-blocking)

| # | Severity | Location | Spec statement / standard | Finding and suggested direction |
|---|---|---|---|---|
| F1 | major, non-blocking | `backend/tests/test_tactics.py:167-188` | Spec section 2, contract item 3: "ascending by the python-chess square index of `pinned_square` (`a1=0, b1=1, ..., h1=7, a2=8, ...`)" | Both ordering tests (e2<f7 and b2<h7) also pass if pins are sorted by the **string** `pinned_square` (file-major, e.g. it puts `"a2"` before `"b1"`) or by `king_square`. A plausible regression to `sort(key=lambda p: p.pinned_square)` would stay green. The current code is correct (`tactics.py:96` uses `chess.parse_square`). Direction: in a later spec revision, add a case with two pins where lexical and index order differ (for example pinned squares `b1` and `a2`), ideally two pins of the same color so the king square cannot be the key either. |
| F2 | minor, non-blocking | `backend/tests/test_tactics.py:211-229` | Spec section 3: "When (a) applies, chain the original exception (`raise ... from exc`)." | No test checks `exc_info.value.__cause__` is a `ValueError` for the `garbage`/`empty` cases, so dropping `from exc` would stay green. Section 5 does not require such a test, so the test file is not out of spec. The code does chain (`tactics.py:41-43`). Direction: add a `__cause__` assertion for the parse-failure cases in a later revision. |
| F3 | minor, non-blocking | `backend/tests/test_tactics.py:106-143` | Spec section 2, contract item 5: "The slider must match the line: a rook or queen on a rank or file, a bishop or queen on a diagonal." | 5.4 checks the rook/bishop line mismatch, but no case puts an enemy **non-slider** (knight, pawn, king) behind a lone blocker. An implementation that treats any enemy piece on the line as a pinner would pass every test. The code only scans `_SLIDER_TYPES` (`tactics.py:12`, `:69`). Direction: add a "knight-behind-blocker" style no-pin case. |
| F4 | minor, non-blocking | `backend/tests/test_tactics.py:146-164` | Spec section 2, contract item 2: "a new `list[Pin]` on each call" | No test checks that mutating a returned list does not affect a later call, so a cached or shared module-level list would pass. The code builds a fresh list on each call (`tactics.py:68`, `:95`). Direction: optional follow-up test that calls `find_pins` twice and mutates the first result. |
| F5 | info, non-blocking | `docs/iteration-log-test-author.md` (whole file, modified) | Spec section 5.9: "No files other than the two listed in section 6 are changed." | `git status --short` shows this file modified. red-proof.md says stage 3 (tester) appended to it, so it is a pipeline log, not a production or test change from the implementer. Recorded so the orchestrator or human can decide whether 5.9 covers pipeline logs. It does not affect this verdict. |

## Criteria verified and how

### Code vs. spec (`backend/app/services/tactics.py`)

- **Interface (section 2):** `logger = logging.getLogger(__name__)` at :8. `class TacticsError(ValueError)` at :15
  with the spec docstring word for word. `@dataclass(frozen=True) class Pin` at :19-27, with field order
  `pinned_square, pinner_square, king_square, pinned_color, pinned_piece` exactly as specified.
  `find_pins(fen: str) -> list[Pin]` at :92 with the spec docstring. Checked by reading the code.
- **Square format (item 1):** `chess.square_name` at :82-84.
- **Return type (item 2):** a new list from list concatenation at :95. When nothing matches, each `_pins_against`
  returns an empty list, so the result is `[]`, not `None`.
- **Ordering (item 3):** `pins.sort(key=lambda pin: chess.parse_square(pin.pinned_square))` at :96 sorts by
  python-chess square index. Color is not part of the key. Keys cannot clash: `chess.between(king, slider)` with
  exactly one occupant means each pinned square has one king line and one first slider beyond it, and a slider
  further back sees two blockers and is skipped (:74).
- **Both sides (item 4):** :95 scans `chess.WHITE` and `chess.BLACK`. `board.turn` is never read.
- **Pin rule (items 5 and 8):** `_slider_matches_line` (:52-60) allows rook/queen on the same rank or file and
  bishop/queen on an equal file/rank gap, and rejects any other geometry. Only enemy sliders are scanned
  (`board.pieces(piece_type, not color)`, :70), which covers "slider is the king's own color". The squares strictly
  between are `chess.between(king, slider) & board.occupied` with `popcount == 1` (:73-75), which covers "two or
  more pieces". The single blocker must be the king's color (:78), which covers "blocker is the slider's color".
  The check is purely geometric: no legality or mobility check, as item 5 requires. The king can never be the
  pinned piece because `between` excludes both endpoints.
- **`pinned_color` / `pinned_piece` (items 6-7):** `chess.COLOR_NAMES[color]` and
  `chess.PIECE_NAMES[piece.piece_type]` at :85-86, the exact strings the spec names.
- **Error class and messages (section 3):** `_parse_board` (:36-49). (a) catches the `ValueError` from
  `chess.Board(fen)` and raises `TacticsError(f"invalid FEN {fen!r} ({exc}); expected a valid FEN string") from exc`
  (:40-43). (b) when `not board.is_valid()`, it raises
  `invalid FEN {fen!r} (illegal position: {flags}); expected a reachable chess position` (:44-48). Neither message
  has an operation prefix (Q1, decision-004 message convention). No bare `ValueError` or HTTP error escapes.
- **`_status_names` (:30-33):** a local equivalent. `moves.py` is not imported (implementation note). It iterates
  `chess.Status` members and skips the zero member, so it returns flag names such as `NO_WHITE_KING`.
- **Purity (item 9):** no I/O, engine, LLM or network. Module-level state is three immutable tuples (:10-12). The
  board is local to each call.
- **Logging (item 10):** one `logger.debug` line with the pin count and canonical `board.fen()` (:97). No INFO log
  and no `print`.
- **Section 5.9 reviewer checks:** no `fastapi` or `app.api` import (imports are `logging`, `dataclasses`, `chess`
  only, :3-6). Docstrings are present on the module (:1), `TacticsError`, `Pin`, `find_pins` and all four private
  helpers (`_status_names`, `_parse_board`, `_slider_matches_line`, `_pins_against`). Every def has full type
  hints. Private helpers and constants use `_` / `_UPPER_SNAKE_CASE`. Descriptive names are used throughout
  (coding standards).
- **No scope creep (section 8):** `codebase_search "tactics"` under `backend/app` finds matches only in
  `tactics.py`, so there is no router, schema, endpoint or wiring. There are no relative pins, no caching and no
  refactor of `moves.py`. `git status --short` shows `tactics.py` as the only new or changed production file. The
  modified `main.py` is pre-existing, as red-proof.md's baseline confirms.
- **Out-of-scope defensive line:** `if king is None: return []` (:66-67) cannot be reached after `is_valid()`. It
  is harmless and not a behavior change. No finding.

### Tests vs. spec (`backend/tests/test_tactics.py`)

- **Location and layout:** the file is in `backend/tests/` (decision-002), one file per module, and test names
  describe behavior (testing standards).
- **5.1** (:17-46): all four cases with the spec's FENs and full five-field `Pin` values, compared with `==`.
- **5.2** (:49-68): both queen cases match the spec.
- **5.3** (:71-103): all three cases. Each one also checks on the test side that the along-the-line move
  (`e4e5`, `e2e3`, `e5d4`) is legal, so the precondition is real and the assertion is not vacuous.
- **5.4** (:106-143): all seven no-pin cases, each asserting `== []`. Checked that each case would fail under the
  wrong rule it targets. For example, `own-slider-behind` would report e2 if slider color were ignored, and
  `two-mixed-pieces-between` would report a pin if only same-color blockers were counted.
- **5.5** (:146-164): `isinstance(result, list)` and `== []` for the start position and bare kings.
- **5.6** (:167-188): both-sides, ordering and side-to-move tests, with the spec's expected lists. Together they
  reject a plain white-then-black or black-then-white concatenation. See F1 for what they miss.
- **5.7** (:191-208): field-name order, each attribute value and `FrozenInstanceError` on assignment.
- **5.8** (:211-229): all four invalid inputs, covering parse failure (a) and `is_valid()` failure (b), with
  `pytest.raises(TacticsError)`. Each asserts the key phrases `"invalid FEN"`, `repr(fen)` and `"expected"`, and that
  the message does not start with `"find pins failed"`. Only key phrases are asserted (testing standards).
  `test_tactics_error_is_a_value_error` (:232-234) asserts the subclass relationship.
- **Expected values are explicit** and come from spec section 5, not from the implementation. The red run failed
  first with `ModuleNotFoundError` (red-proof.md). There are no mocks, marks or env vars (spec section 4).
- **Error paths:** a happy path and failure paths are both present (testing standards minimum).
- **Test-file integrity:** green-report-round-1.md records the test file as identical to red-proof.md and reports
  27/27 tactics cases passing.

## Refused tool calls

None.
