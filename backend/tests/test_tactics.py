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
