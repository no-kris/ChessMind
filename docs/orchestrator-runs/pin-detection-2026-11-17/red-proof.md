# Red proof: pin-detection-2026-11-17 (stage 3)

Author: backend-tester. Date: 2026-11-17.
Spec: `docs/orchestrator-runs/pin-detection-2026-11-17/spec.md` (draft 2, approved at H1).

## New test files

| Path | Status |
|------|--------|
| `backend/tests/test_tactics.py` | new (only new file under `backend/tests/`) |

No existing test file was edited. No production file was created or edited.

## Baseline (before writing any test)

`git status --short` at stage start (exit 0):

```
 D .claude/agents/backend-test-author.md
 M .claude/agents/endpoint-builder.md
 M .memory/project/MEMORY_INDEX.md
 M .memory/project/decisions/decision-004.md
 M backend/app/main.py
 M docs/rubric-endpoint-builder.md
 M docs/rubric-test-author.md
?? .claude/agents/backend-tester.md
?? .claude/agents/orchestrator.md
?? .claude/agents/planner.md
?? .claude/agents/reviewer.md
?? .claude/agents/verifier.md
?? .claude/skills/
?? .mcp.json
?? .memory/project/decisions/decision-008.md
?? .memory/project/decisions/decision-009.md
?? .memory/project/decisions/decision-010.md
?? docs/orchestration-diagram.md
?? docs/orchestrator-runs/
?? docs/routing-and-tool-grant-map.md
?? mcp/
```

Baseline `test_runner` (path `backend`, before `test_tactics.py` existed):
pytest **96 passed, 1 warning, exit 0**. Engine tests in
`tests/test_engine.py` ran and passed (not skipped). The baseline ruff check
**already failed (exit 1)** with one pre-existing error that has nothing to do
with this run:

```
== uv run ruff check . (exit 1) ==
EXE002 The file is executable but no shebang is present
--> app/main.py:1:1

Found 1 error.
```

`backend/app/main.py` was already modified in the baseline. The error is
about its file mode (see the archived decision-003 note on EXE002). The tester
does not own that file and must not change permissions.

## Red run: verbatim test_runner output

Call: `test_runner(path="backend", install=false)`. The output below is
verbatim except that ANSI colour escape sequences (`ESC[...m`) have been
removed. No other characters were changed, added or dropped.

```
Project: backend (python)
== uv run pytest (exit 2) ==
============================= test session starts ==============================
platform linux -- Python 3.13.18, pytest-9.1.1, pluggy-1.6.0
rootdir: /workspace/backend
configfile: pyproject.toml
testpaths: tests
plugins: cov-7.1.0, anyio-4.15.1
collected 96 items / 1 error

==================================== ERRORS ====================================
____________________ ERROR collecting tests/test_tactics.py ____________________
ImportError while importing test module '/workspace/backend/tests/test_tactics.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/local/lib/python3.13/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/test_tactics.py:12: in <module>
    from app.services.tactics import Pin, TacticsError, find_pins
E   ModuleNotFoundError: No module named 'app.services.tactics'
=============================== warnings summary ===============================
../../opt/venv/lib/python3.13/site-packages/starlette/testclient.py:53
  /opt/venv/lib/python3.13/site-packages/starlette/testclient.py:53: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = Callable[[], AbstractContextManager[anyio.abc.BlockingPortal]]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/test_tactics.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
========================= 1 warning, 1 error in 0.85s ==========================
warning: `VIRTUAL_ENV=/root/.cache/uv/builds-v0/.tmpwA89kA` does not match the project environment path `/opt/venv` and will be ignored; use `--active` to target the active environment instead

== uv run ruff check . (exit 1) ==
EXE002 The file is executable but no shebang is present
--> app/main.py:1:1

I001 [*] Import block is un-sorted or un-formatted
  --> tests/test_tactics.py:7:1
   |
 5 |   """
 6 |
 7 | / import dataclasses
 8 | |
 9 | | import chess
10 | | import pytest
11 | |
12 | | from app.services.tactics import Pin, TacticsError, find_pins
   | |_____________________________________________________________^
13 |
14 |   E1_START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
   |
help: Organize imports
   |
10 | import pytest
   -
11 | from app.services.tactics import Pin, TacticsError, find_pins
   |

Found 2 errors.
[*] 1 fixable with the `--fix` option.
warning: `VIRTUAL_ENV=/root/.cache/uv/builds-v0/.tmpwA89kA` does not match the project environment path `/opt/venv` and will be ignored; use `--active` to target the active environment instead

RESULT: FAIL (uv run pytest; uv run ruff check . exited non-zero)
```

## Why this is red for the right reason

- The only failure is `ModuleNotFoundError: No module named
  'app.services.tactics'` at `tests/test_tactics.py:12`. The production module
  that the spec says to create does not exist yet. The failure does not come
  from a typo, a fixture or a bad name in the test file.
- The module-level import fails, so pytest stops collection
  (`Interrupted: 1 error during collection`, exit 2). None of the 14 tests can
  run until `backend/app/services/tactics.py` exists, which makes all 14
  red for the same reason.
- **Pre-existing tests:** none failed. Because collection stopped, the 96
  pre-existing tests were collected (`collected 96 items / 1 error`) but did
  not run in this call. The baseline run just before this one shows them all
  passing (96 passed, exit 0). The only change since then is the new file.
  The green stage will run them again.
- **ruff:** `EXE002` on `app/main.py` was already there at baseline (see
  above). `I001` on `tests/test_tactics.py` is most likely caused by the
  missing module. The import layout is the same as in the existing
  `tests/test_moves.py` (stdlib, blank line, third-party, blank line,
  `from app.services... import ...`), and ruff accepts that file. While
  `app/services/tactics.py` is missing, ruff appears to classify
  `app.services.tactics` as non-first-party and wants it merged into the
  third-party block. This should clear once the module exists. The green
  stage will check it. The file was deliberately left unchanged so that it
  stays identical to the copy below for G2.

## Acceptance criteria to test mapping

| # | Test name | Spec examples |
|---|-----------|---------------|
| 1 | `test_starting_position_has_no_pins` | E1 |
| 2 | `test_absolute_pin_is_reported_with_pinned_pinning_and_king_squares` | E2-E8 (7 params) |
| 3 | `test_black_piece_pinned_against_black_king_is_reported` | E9 |
| 4 | `test_non_pin_lines_are_not_reported` | N1-N7 (7 params) |
| 5 | `test_multiple_pins_against_one_king_are_all_reported_in_square_order` | M1 |
| 6 | `test_pins_for_both_sides_are_reported` | B1 |
| 7 | `test_pins_are_ordered_white_king_first_then_by_pinned_square` | B2 |
| 8 | `test_pins_do_not_depend_on_side_to_move` | B1, S1 |
| 9 | `test_find_pins_returns_a_tuple` | E2, E1 (2 params) |
| 10 | `test_pin_is_frozen` | E2 |
| 11 | `test_invalid_fen_raises_tactics_error` | X1-X4 (4 params) |
| 12 | `test_tactics_error_is_a_value_error` | n/a |
| 13 | `test_pin_color_matches_pinned_kings_side` | E2 white, E9 black (2 params) |
| 14 | `test_pin_has_four_fields_in_order` | n/a |

14 test functions, 30 test items once parametrized. All FENs and expected
values are copied from the spec unchanged. I checked every example by hand
against chess rules and found no disagreement with the spec.

## Full content of `backend/tests/test_tactics.py` (byte-for-byte copy, reference for G2)

```python
"""Tests for app.services.tactics: absolute pin detection (find_pins).

Expected values come from spec.md of run pin-detection-2026-11-17
(examples E1-E9, N1-N7, M1, B1, B2, S1, X1-X4), not from an implementation.
"""

import dataclasses

import chess
import pytest

from app.services.tactics import Pin, TacticsError, find_pins

E1_START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
E2_BISHOP_DIAGONAL = "4k3/8/8/8/1b6/2N5/8/4K3 w - - 0 1"
E9_BLACK_PINNED = "4k3/8/2n5/1B6/8/8/8/4K3 b - - 0 1"
B1_MUTUAL = "4k3/4r3/8/8/8/8/4R3/4K3 w - - 0 1"
S1_MUTUAL_BLACK_TO_MOVE = "4k3/4r3/8/8/8/8/4R3/4K3 b - - 0 1"
B1_EXPECTED = (
    Pin(pinned_square="e2", pinning_square="e7", king_square="e1", color="white"),
    Pin(pinned_square="e7", pinning_square="e2", king_square="e8", color="black"),
)


def test_starting_position_has_no_pins():
    """E1: the starting position has no pins."""
    assert find_pins(E1_START) == ()


@pytest.mark.parametrize(
    ("fen", "expected"),
    [
        pytest.param(
            E2_BISHOP_DIAGONAL,
            Pin(pinned_square="c3", pinning_square="b4", king_square="e1", color="white"),
            id="E2-bishop-on-diagonal",
        ),
        pytest.param(
            "k7/8/8/8/4r3/8/4B3/4K3 w - - 0 1",
            Pin(pinned_square="e2", pinning_square="e4", king_square="e1", color="white"),
            id="E3-rook-on-file",
        ),
        pytest.param(
            "k7/8/8/8/8/8/8/r1N1K3 w - - 0 1",
            Pin(pinned_square="c1", pinning_square="a1", king_square="e1", color="white"),
            id="E4-rook-on-rank",
        ),
        pytest.param(
            "k7/8/8/8/8/8/8/K1R3q1 w - - 0 1",
            Pin(pinned_square="c1", pinning_square="g1", king_square="a1", color="white"),
            id="E5-queen-on-rank",
        ),
        pytest.param(
            "k7/8/8/8/7q/8/5P2/4K3 w - - 0 1",
            Pin(pinned_square="f2", pinning_square="h4", king_square="e1", color="white"),
            id="E6-queen-on-diagonal-pinned-pawn",
        ),
        pytest.param(
            "k7/8/8/8/4r3/8/4Q3/4K3 w - - 0 1",
            Pin(pinned_square="e2", pinning_square="e4", king_square="e1", color="white"),
            id="E7-pinned-queen",
        ),
        pytest.param(
            "k7/8/8/8/8/4r3/4R3/4K3 w - - 0 1",
            Pin(pinned_square="e2", pinning_square="e3", king_square="e1", color="white"),
            id="E8-adjacent-pinner",
        ),
    ],
)
def test_absolute_pin_is_reported_with_pinned_pinning_and_king_squares(fen, expected):
    """E2-E8: each single absolute pin is reported with its three squares and colour."""
    assert find_pins(fen) == (expected,)


def test_black_piece_pinned_against_black_king_is_reported():
    """E9: a black piece pinned against the black king is reported with color black."""
    expected = (
        Pin(pinned_square="c6", pinning_square="b5", king_square="e8", color="black"),
    )
    assert find_pins(E9_BLACK_PINNED) == expected


@pytest.mark.parametrize(
    "fen",
    [
        pytest.param("4k3/8/8/8/1b6/2N5/3P4/4K3 w - - 0 1", id="N1-two-own-pieces-between"),
        pytest.param("4k3/8/8/8/1b6/2n5/8/4K3 w - - 0 1", id="N2-piece-is-pinners-colour"),
        pytest.param("k7/8/8/8/4R3/8/4B3/4K3 w - - 0 1", id="N3-own-colour-slider-behind"),
        pytest.param("k7/8/8/8/4b3/8/4N3/4K3 w - - 0 1", id="N4-bishop-on-a-file"),
        pytest.param("k7/8/8/8/1r6/2N5/8/4K3 w - - 0 1", id="N5-rook-on-a-diagonal"),
        pytest.param("k7/8/8/8/8/4n3/4N3/4K3 w - - 0 1", id="N6-knight-behind"),
        pytest.param("4k3/8/8/8/1b6/8/8/4K3 w - - 0 1", id="N7-check-nothing-between"),
    ],
)
def test_non_pin_lines_are_not_reported(fen):
    """N1-N7: lines that are not absolute pins return an empty tuple."""
    assert find_pins(fen) == ()


def test_multiple_pins_against_one_king_are_all_reported_in_square_order():
    """M1: three pins on one king are all returned, ordered by pinned square."""
    expected = (
        Pin(pinned_square="d2", pinning_square="b4", king_square="e1", color="white"),
        Pin(pinned_square="e2", pinning_square="e7", king_square="e1", color="white"),
        Pin(pinned_square="f2", pinning_square="h4", king_square="e1", color="white"),
    )
    assert find_pins("k7/4r3/8/8/1b5q/8/3NBP2/4K3 w - - 0 1") == expected


def test_pins_for_both_sides_are_reported():
    """B1: mutual rook pins on one file are both reported, white first."""
    assert find_pins(B1_MUTUAL) == B1_EXPECTED


def test_pins_are_ordered_white_king_first_then_by_pinned_square():
    """B2: the white pin comes first even though black's pinned b2 has a lower index."""
    expected = (
        Pin(pinned_square="g7", pinning_square="f6", king_square="h8", color="white"),
        Pin(pinned_square="b2", pinning_square="c3", king_square="a1", color="black"),
    )
    assert find_pins("7K/6N1/5b2/8/8/2B5/1n6/k7 w - - 0 1") == expected


def test_pins_do_not_depend_on_side_to_move():
    """B1 and S1 differ only in side to move and return the same pins."""
    white_to_move = find_pins(B1_MUTUAL)
    black_to_move = find_pins(S1_MUTUAL_BLACK_TO_MOVE)
    assert black_to_move == white_to_move
    assert black_to_move == B1_EXPECTED


@pytest.mark.parametrize(
    "fen",
    [
        pytest.param(E2_BISHOP_DIAGONAL, id="E2-with-pins"),
        pytest.param(E1_START, id="E1-without-pins"),
    ],
)
def test_find_pins_returns_a_tuple(fen):
    """The result is a tuple whether or not there are pins."""
    assert type(find_pins(fen)) is tuple


def test_pin_is_frozen():
    """Assigning to a field of a returned Pin raises FrozenInstanceError."""
    pin = find_pins(E2_BISHOP_DIAGONAL)[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        pin.pinned_square = "d2"


@pytest.mark.parametrize(
    "fen",
    [
        pytest.param("not a fen", id="X1-malformed"),
        pytest.param("", id="X2-empty"),
        pytest.param("8/8/8/8/8/8/8/8 w - - 0 1", id="X3-no-kings"),
        pytest.param("4k3/8/8/8/8/8/8/4RK2 w - - 0 1", id="X4-side-not-to-move-in-check"),
    ],
)
def test_invalid_fen_raises_tactics_error(fen):
    """X1-X4: unparseable or illegal positions raise TacticsError naming the problem."""
    with pytest.raises(TacticsError, match="invalid FEN"):
        find_pins(fen)


def test_tactics_error_is_a_value_error():
    """TacticsError subclasses ValueError so a router can map it to 400."""
    assert issubclass(TacticsError, ValueError)


@pytest.mark.parametrize(
    ("fen", "expected_color"),
    [
        pytest.param(E2_BISHOP_DIAGONAL, "white", id="E2-white"),
        pytest.param(E9_BLACK_PINNED, "black", id="E9-black"),
    ],
)
def test_pin_color_matches_pinned_kings_side(fen, expected_color):
    """The color field equals the side of the king on king_square."""
    pins = find_pins(fen)
    assert len(pins) == 1
    pin = pins[0]
    assert pin.color == expected_color
    king = chess.Board(fen).piece_at(chess.parse_square(pin.king_square))
    assert king is not None
    assert king.piece_type == chess.KING
    king_side = "white" if king.color == chess.WHITE else "black"
    assert king_side == expected_color


def test_pin_has_four_fields_in_order():
    """Pin has exactly the four fields of spec Decision 1, in that order."""
    assert [f.name for f in dataclasses.fields(Pin)] == [
        "pinned_square",
        "pinning_square",
        "king_square",
        "color",
    ]
```

## Not run / pending

- Coverage: pending. `test_runner` runs without `--cov`.
- Pre-existing tests in the red call: collected but not run, because
  collection was interrupted (see above). Their pass status comes from the
  baseline run.
