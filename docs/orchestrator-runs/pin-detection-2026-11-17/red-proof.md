# Red proof: pin-detection-2026-11-17

Stage: 3 (tester red). Spec: `docs/orchestrator-runs/pin-detection-2026-11-17/spec.md` (v3, approved at H1 #3, relayed).
Date: 2026-11-17.

## Baseline (before any write by this stage)

`git_status` (`git status --short`, exit 0):

```
 M backend/app/main.py
?? docs/orchestrator-runs/
```

`test_runner` with path `backend` (`uv run pytest`) before `test_tactics.py` existed: exit 0, summary line
`96 passed, 1 warning in 5.24s` (test_api 7, test_classify 10, test_classify_positions 13, test_engine 2,
test_engine_unit 20, test_game_store 13, test_games_api 20, test_moves 11). `backend/tests/test_tactics.py` did not exist
(file_read failed on it).

## Red run

Command: `test_runner` with path `backend` -> `uv run pytest`. Exit code: **2**.
Output below is verbatim except that ANSI colour escape sequences were removed.

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
tests/test_tactics.py:6: in <module>
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
========================= 1 warning, 1 error in 1.11s ==========================
warning: `VIRTUAL_ENV=/root/.cache/uv/builds-v0/.tmpzqhCr1` does not match the project environment path `/opt/venv` and will be ignored; use `--active` to target the active environment instead

RESULT: FAIL (uv run pytest exit code 2)
```

Summary line: `1 warning, 1 error in 1.11s` after `Interrupted: 1 error during collection`. Exit code 2.

## Why it is red, and the case count

- Reason: `ModuleNotFoundError: No module named 'app.services.tactics'` at the module-level import on line 6 of the
  test file. This is the red reason spec section 7 expects: the production module does not exist yet. The
  imported names (`Pin`, `TacticsError`, `find_pins`) are exactly the public interface in spec section 2. It is not a
  typo or fixture error in the test.
- Because the import fails at collection, pytest collects 0 cases from `test_tactics.py` and interrupts the session.
  The other 96 existing tests were collected (`collected 96 items / 1 error`) but not run in this session. Their
  result is the baseline above: 96 passed, exit 0.
- Cases in `backend/tests/test_tactics.py` (counted from the file; pytest could not collect them): **11 test functions,
  27 test cases**:
  - 5.1 `test_absolute_pin_is_reported_with_squares_color_and_piece_type`: 4 (`rook-on-rank`,
    `rook-on-rank-black-bishop`, `rook-on-file`, `bishop-on-diagonal`)
  - 5.2 `test_queen_is_a_pinner_on_files_and_diagonals`: 2 (`queen-on-file`, `queen-on-diagonal`)
  - 5.3 `test_pinned_piece_that_can_move_along_the_line_is_still_a_pin`: 3 (`rook-pinned-on-file`,
    `pawn-pinned-on-file`, `queen-pinned-on-diagonal`); each also asserts test-side, with python-chess, that the
    along-line move (`e4e5`, `e2e3`, `e5d4`) is legal
  - 5.4 `test_line_without_absolute_pin_returns_no_pins`: 7
  - 5.5 `test_position_without_pins_returns_empty_list`: 2
  - 5.6 `test_pins_for_both_sides_are_reported_in_one_position`, `test_pins_are_ordered_by_pinned_square_not_by_color`,
    `test_result_does_not_depend_on_side_to_move`: 3
  - 5.7 `test_pin_is_frozen_dataclass_with_square_name_fields`: 1 (name kept as accepted at H1 #3)
  - 5.8 `test_invalid_fen_raises_tactics_error`: 4 (`garbage`, `empty`, `no-kings`, `opposite-side-in-check`);
    `test_tactics_error_is_a_value_error`: 1
- Stale `backend/.pytest_cache` node ids for `test_tactics.py` were ignored, as spec section 7 says.

## New test files

### `backend/tests/test_tactics.py`

Full content, copied exactly as written (6925 bytes, LF line endings, ends with one newline):

```python
import dataclasses

import chess
import pytest

from app.services.tactics import Pin, TacticsError, find_pins

ROOK_ON_FILE_FEN = "k3r3/8/8/8/8/8/4B3/4K3 w - - 0 1"
ORDERING_FEN_WHITE_TO_MOVE = "7K/7N/5B2/8/8/8/1n6/k6r w - - 0 1"
ORDERING_FEN_BLACK_TO_MOVE = "7K/7N/5B2/8/8/8/1n6/k6r b - - 0 1"
ORDERING_EXPECTED = [
    Pin("b2", "f6", "a1", "black", "knight"),
    Pin("h7", "h1", "h8", "white", "knight"),
]


@pytest.mark.parametrize(
    ("fen", "expected"),
    [
        pytest.param(
            "4k3/8/8/8/K1N4r/8/8/8 w - - 0 1",
            [Pin("c4", "h4", "a4", "white", "knight")],
            id="rook-on-rank",
        ),
        pytest.param(
            "8/8/R2b3k/8/8/8/8/4K3 w - - 0 1",
            [Pin("d6", "a6", "h6", "black", "bishop")],
            id="rook-on-rank-black-bishop",
        ),
        pytest.param(
            ROOK_ON_FILE_FEN,
            [Pin("e2", "e8", "e1", "white", "bishop")],
            id="rook-on-file",
        ),
        pytest.param(
            "6k1/5n2/8/8/8/1B6/8/4K3 w - - 0 1",
            [Pin("f7", "b3", "g8", "black", "knight")],
            id="bishop-on-diagonal",
        ),
    ],
)
def test_absolute_pin_is_reported_with_squares_color_and_piece_type(fen, expected):
    """A single absolute pin is reported with its three squares, color and piece type."""
    result = find_pins(fen)

    assert result == expected


@pytest.mark.parametrize(
    ("fen", "expected"),
    [
        pytest.param(
            "4k3/8/8/4n3/8/8/4Q3/K7 w - - 0 1",
            [Pin("e5", "e2", "e8", "black", "knight")],
            id="queen-on-file",
        ),
        pytest.param(
            "q3k3/8/8/8/8/8/6R1/7K w - - 0 1",
            [Pin("g2", "a8", "h1", "white", "rook")],
            id="queen-on-diagonal",
        ),
    ],
)
def test_queen_is_a_pinner_on_files_and_diagonals(fen, expected):
    """A queen pins along a file and along a diagonal."""
    result = find_pins(fen)

    assert result == expected


@pytest.mark.parametrize(
    ("fen", "along_line_move", "expected"),
    [
        pytest.param(
            "k3r3/8/8/8/4R3/8/8/4K3 w - - 0 1",
            "e4e5",
            [Pin("e4", "e8", "e1", "white", "rook")],
            id="rook-pinned-on-file",
        ),
        pytest.param(
            "k3r3/8/8/8/8/8/4P3/4K3 w - - 0 1",
            "e2e3",
            [Pin("e2", "e8", "e1", "white", "pawn")],
            id="pawn-pinned-on-file",
        ),
        pytest.param(
            "7k/8/8/4q3/8/8/KB6/8 b - - 0 1",
            "e5d4",
            [Pin("e5", "b2", "h8", "black", "queen")],
            id="queen-pinned-on-diagonal",
        ),
    ],
)
def test_pinned_piece_that_can_move_along_the_line_is_still_a_pin(
    fen, along_line_move, expected
):
    """A pinned piece with a legal move along the pin line is still reported."""
    board = chess.Board(fen)
    assert chess.Move.from_uci(along_line_move) in board.legal_moves

    result = find_pins(fen)

    assert result == expected


@pytest.mark.parametrize(
    "fen",
    [
        pytest.param(
            "k3r3/8/8/8/4p3/8/8/4K3 w - - 0 1",
            id="blocker-same-color-as-pinner-file",
        ),
        pytest.param(
            "6k1/8/8/3N4/8/1B6/8/4K3 w - - 0 1",
            id="blocker-same-color-as-pinner-diagonal",
        ),
        pytest.param(
            "k3r3/8/8/8/8/4B3/4N3/4K3 w - - 0 1",
            id="two-own-pieces-between",
        ),
        pytest.param(
            "k3r3/8/8/8/4p3/8/4N3/4K3 w - - 0 1",
            id="two-mixed-pieces-between",
        ),
        pytest.param(
            "k3b3/8/8/8/8/8/4N3/4K3 w - - 0 1",
            id="bishop-on-file",
        ),
        pytest.param(
            "6k1/5n2/8/8/8/1R6/8/4K3 w - - 0 1",
            id="rook-on-diagonal",
        ),
        pytest.param(
            "4R3/8/k7/8/8/8/4N3/4K3 w - - 0 1",
            id="own-slider-behind",
        ),
    ],
)
def test_line_without_absolute_pin_returns_no_pins(fen):
    """Lines that look like pins but are not absolute pins give no result."""
    result = find_pins(fen)

    assert result == []


@pytest.mark.parametrize(
    "fen",
    [
        pytest.param(
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            id="start-position",
        ),
        pytest.param(
            "4k3/8/8/8/8/8/8/4K3 w - - 0 1",
            id="bare-kings",
        ),
    ],
)
def test_position_without_pins_returns_empty_list(fen):
    """A position with no pins returns an empty list, not None."""
    result = find_pins(fen)

    assert isinstance(result, list)
    assert result == []


def test_pins_for_both_sides_are_reported_in_one_position():
    """White and Black pins in the same position are both reported."""
    result = find_pins("4r1k1/5n2/8/8/8/1B6/4B3/4K3 w - - 0 1")

    assert result == [
        Pin("e2", "e8", "e1", "white", "bishop"),
        Pin("f7", "b3", "g8", "black", "knight"),
    ]


def test_pins_are_ordered_by_pinned_square_not_by_color():
    """Pins are ordered by pinned square index, so a black b2 pin precedes a white h7 pin."""
    result = find_pins(ORDERING_FEN_WHITE_TO_MOVE)

    assert result == ORDERING_EXPECTED


def test_result_does_not_depend_on_side_to_move():
    """The same position with Black to move gives the same pins."""
    result = find_pins(ORDERING_FEN_BLACK_TO_MOVE)

    assert result == ORDERING_EXPECTED


def test_pin_is_frozen_dataclass_with_square_name_fields():
    """Pin is a frozen dataclass with the five fields in the documented order."""
    result = find_pins(ROOK_ON_FILE_FEN)

    assert [f.name for f in dataclasses.fields(Pin)] == [
        "pinned_square",
        "pinner_square",
        "king_square",
        "pinned_color",
        "pinned_piece",
    ]
    assert result[0].pinned_square == "e2"
    assert result[0].pinner_square == "e8"
    assert result[0].king_square == "e1"
    assert result[0].pinned_color == "white"
    assert result[0].pinned_piece == "bishop"
    with pytest.raises(dataclasses.FrozenInstanceError):
        result[0].pinned_square = "e3"


@pytest.mark.parametrize(
    "fen",
    [
        pytest.param("not a fen", id="garbage"),
        pytest.param("", id="empty"),
        pytest.param("8/8/8/8/8/8/8/8 w - - 0 1", id="no-kings"),
        pytest.param("4k3/8/8/8/8/8/8/4R1K1 w - - 0 1", id="opposite-side-in-check"),
    ],
)
def test_invalid_fen_raises_tactics_error(fen):
    """Unparseable FENs and invalid positions raise TacticsError naming the input."""
    with pytest.raises(TacticsError) as exc_info:
        find_pins(fen)

    message = str(exc_info.value)
    assert "invalid FEN" in message
    assert repr(fen) in message
    assert "expected" in message
    assert not str(exc_info.value).startswith("find pins failed")


def test_tactics_error_is_a_value_error():
    """TacticsError is a ValueError subclass."""
    assert issubclass(TacticsError, ValueError)
```

## Notes

- No mocks, no `engine` or `llm` marks, no env vars (spec section 4).
- The FENs and expected values were taken from spec section 5 and checked by hand against the board, not taken from
  an implementation. They have not been run through python-chess in this stage; the green run will exercise them.
- Files written by this stage: `backend/tests/test_tactics.py` (new), this file, and an entry appended to
  `docs/iteration-log-test-author.md`. No production code, existing test, conftest or `.memory/` file touched.
