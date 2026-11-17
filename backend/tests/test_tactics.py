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
