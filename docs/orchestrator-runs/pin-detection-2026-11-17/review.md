# Review: pin-detection-2026-11-17, round 1 of max 3

Reviewer. Date: 2026-11-17.
Inputs: `spec.md` (approved at H1), `backend/tests/test_tactics.py` (and the
frozen copy in `red-proof.md`), `backend/app/services/tactics.py` (the only
changed production file), `implementer-log.md`, `green-report-round-1.md`,
`.memory/knowledge/coding-standards.md`, `.memory/knowledge/testing-standards.md`,
`.memory/project/decisions/decision-004.md`, and for comparison
`backend/app/services/moves.py`.

## Verdict: **PASS**

No blocking findings. There are four non-blocking findings (below). None of
them breaks a spec statement or an acceptance criterion, and none of them
needs another round.

## Findings

Each finding has a file:line, the spec statement it relates to, a severity and
a suggested direction. None of them needs to be fixed in this run.

1. **non-blocking** `backend/app/services/tactics.py:9`: the spec's
   "Public interface" lists only `TacticsError`, `Pin` and `find_pins`, and
   Decision 1 annotates `color: Literal["white", "black"]` inline. The module
   adds a public alias `PinColor = Literal["white", "black"]` and uses it at
   `:38`. The annotation means the same thing and the runtime value is still a
   plain `str`, so the behaviour matches the spec. The only change is one extra
   public name. Direction: keep it as it is (or make it private as
   `_PinColor`) when relative pins reuse the type. Do not change it now.
2. **non-blocking** `backend/tests/test_tactics.py:160-163`: Decision 2 says
   "The error is raised with `from exc` when it wraps the parser error", and
   the message should continue with "expected ...". The test checks only the
   key phrase `invalid FEN`, which is what criterion 11 and the testing
   standard ask for, so nothing asserts `__cause__` for X1/X2. I checked the
   code by reading it: `tactics.py:52-54` uses `from exc`, and both messages
   (`:53`, `:57-58`) end with an "expected ..." clause. Direction: a later
   slice could add a `__cause__ is not None` check for X1/X2.
3. **non-blocking** `backend/tests/test_tactics.py:183`: Decision 1 says the
   runtime value of `color` "is always the plain `str` `"white"` or
   `"black"`". The tests compare with `==`, so a `str`-subclass enum would also
   pass. No acceptance criterion asks for a check of the exact type. I checked
   the code by reading it: `tactics.py:14-17` maps to plain string literals.
   Direction: if the Phase 4 JSON payload depends on this, add
   `type(pin.color) is str` at that point.
4. **non-blocking (known, documentation only)**
   `docs/orchestrator-runs/pin-detection-2026-11-17/red-proof.md:178` and
   `docs/orchestrator-runs/pin-detection-2026-11-17/implementer-log.md:52`
   both say "30" test items. The real count is 31
   (1+7+1+7+1+1+1+1+2+1+4+1+2+1), which matches 127 - 96 in the green report.
   This relates to the criteria 1-14 mapping. It is a counting error in prose
   only. The test file is the same as the frozen copy. Direction: none needed.
   The green report already records it.

Out of scope for this review: the ruff `EXE002` on `backend/app/main.py:1` was
already there at baseline (red-proof.md, "Baseline"). It is not caused by this
build, and per decision-003 a human must change the file mode. Ruff reported no
`EXE002` for `backend/app/services/tactics.py`.

## (a) Code vs. spec: what was checked and how

| Spec statement | Result | Evidence |
|---|---|---|
| Public interface: `TacticsError(ValueError)`, frozen `Pin`, `find_pins(fen: str) -> tuple[Pin, ...]` | met | `tactics.py:27-28`, `:31-38`, `:119` |
| Decision 1: exactly four fields in the order pinned, pinning, king, color | met | `tactics.py:35-38` |
| Decision 1: lowercase square names in `chess.square_name` format | met | `tactics.py:95-97` use `chess.square_name` |
| Decision 1: `color` is the side of the pinned piece and its king, as a plain `"white"`/`"black"` | met | `tactics.py:14-17`, `:98` (`side` is the king's side, `:106`) |
| Decision 1: no pins returns `()` | met | `tactics.py:129` `tuple(pins)` on an empty list |
| Decision 2: parser `ValueError` -> `TacticsError`, `invalid FEN ... ; expected a valid FEN string`, `from exc` | met | `tactics.py:49-54` |
| Decision 2: `is_valid()` false -> `TacticsError`, illegal position and expected a reachable position | met | `tactics.py:55-59`; same wording as `moves.py:39-43` |
| Decision 2 / decision-004: no operation prefix in the message | met | both messages start with `invalid FEN` |
| Decision 2: no private imports from `moves.py` (copying is allowed) | met | imports are only `collections.abc`, `dataclasses`, `typing`, `chess` (`tactics.py:3-7`); `_status_names` at `:41-44` is a copy of `moves.py:21-24` |
| Decision 3: white first, set explicitly (not by string sort), then pinned square index ascending | met | `tactics.py:12` `_SIDES_IN_ORDER = (WHITE, BLACK)`; `:116` sorts by `chess.parse_square` (index a1=0 ... h8=63) |
| Decision 4: the pin rule (one own piece between, then an enemy slider of the right type for the line) | met | `tactics.py:86-101`: an enemy first gives None (check / N2 / N7); the second piece must be enemy and in the slider set for the ray (orthogonal -> R/Q, diagonal -> B/Q at `:23-24`, `:109-110`); anything else gives None (N1, N3, N4, N5, N6) |
| Decision 4: any non-king piece can be pinned, whether it can move or capture | met | the type of the shield piece is not checked (`:88-92`); an adjacent pinner works because the walk skips only empty squares |
| Decision 4: both sides; a piece can be pinned and also be a pinner | met | `tactics.py:127-128` checks each king on its own |
| Decision 4: does not depend on side to move | met | `board.turn` is never read |
| Decision 4: purity, no `print`, no logging required | met | no I/O, no state, no `print` |
| Coding standards: docstrings, type hints, `_` prefix for private names, UPPER_SNAKE constants | met | every class and function has a docstring and full signature hints; private helpers and constants have `_` and UPPER_SNAKE names |
| Out of scope: no router/HTTP, no relative pins/skewers/forks, no piece-type field, no caching, no memory edits | met | the module has none of these; `app/api/**` is not touched |
| "No existing files change" | met | my `git_status` run matches the red-proof baseline exactly, apart from `?? backend/app/services/tactics.py` and `?? backend/tests/test_tactics.py`. `M backend/app/main.py` and the other `M` lines were already in the baseline |

I also checked these spec examples by hand against the code path: E2, E5, B2
(including the a1-h8 diagonal between the two kings, which stops at g7/f6),
M1 and X4. All give the values in the spec.

## (b) Tests vs. spec: what was checked and how

| # | Criterion | Test (`backend/tests/test_tactics.py`) | Expected values from spec? | Would a wrong implementation pass? |
|---|---|---|---|---|
| 1 | E1 -> `()` | `:25-27` | yes | no |
| 2 | E2-E8 single pin, with `color="white"` | `:30-72`, 7 params, full `Pin` equality against a 1-tuple | yes, all FENs and pins match the spec table | no: each pinner type and line, pinned pawn/queen and adjacent pinner are covered |
| 3 | E9 black pin | `:75-80` | yes | no |
| 4 | N1-N7 -> `()` | `:83-97`, 7 params | yes | no: each "not a pin" rule in Decision 4 has a case |
| 5 | M1 three pins in order | `:100-107`, exact 3-tuple | yes | no: catches missing rays and wrong order |
| 6 | B1 both sides | `:110-112` | yes | no |
| 7 | B2 white first even though b2 < g7 | `:115-121` | yes | no: a sort by raw `color` string or by index only fails here |
| 8 | B1 == S1 | `:124-129`, also equal to `B1_EXPECTED` | yes | no: a colour or filter based on side to move fails |
| 9 | returns a tuple (E2, E1) | `:132-141`, `type(...) is tuple` | yes | no |
| 10 | frozen `Pin` | `:144-148`, `FrozenInstanceError` | n/a | no |
| 11 | X1-X4 raise `TacticsError` with `invalid FEN` | `:151-163` | yes | no: missing `is_valid()` fails X3/X4; a bare `ValueError` fails the type check |
| 12 | `issubclass(TacticsError, ValueError)` | `:166-168` | n/a | no |
| 13 | color matches the king's side (E2 white, E9 black), checked against the board | `:171-188` | yes | no |
| 14 | field names and order | `:191-198` | yes | no |

- No assertion is vacuous. Every positive case compares the full tuple of
  frozen `Pin` values, so extra, missing or reordered pins fail.
- Error paths are covered: parser errors (X1, X2), illegal positions (X3, X4)
  and the error type (12).
- Testing standards: `parametrize` is used for repeated cases, the error check
  uses its key phrase, nothing is mocked or needs to be, no env vars or marks
  are needed, and the file is in `backend/tests/` (decision-002). The minimum
  of one happy path and one failure per new module is met.
- G2: the green report says the test file is identical to the red-proof copy.
  I compared the two contents I read and found no differences.
- Green run: 127 passed, including all 31 `test_tactics.py` items, and 96/96
  pre-existing tests passed (green-report-round-1.md).

## Notes

- No tool call was refused during this review.
- Memory startup: SCOPE.md matches (ChessMind). No entry I used is past its
  review date.
