import pytest

from app.services.moves import MoveError, apply_move

START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def test_legal_move_returns_both_positions_and_san():
    """A legal UCI move yields SAN plus the before and after FENs."""
    result = apply_move(START, "e2e4")
    assert result.move == "e2e4"
    assert result.san == "e4"
    assert result.fen_before == START
    assert result.fen_after == "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"


def test_promotion_move_is_applied():
    """A UCI promotion suffix is honoured."""
    result = apply_move("8/4P3/8/8/8/8/k7/4K3 w - - 0 1", "e7e8q")
    assert result.san == "e8=Q"
    assert result.fen_after == "4Q3/8/8/8/8/8/k7/4K3 b - - 0 1"


@pytest.mark.parametrize("move", ["e1g1", "e1h1"])
def test_castling_is_recorded_in_standard_uci(move):
    """King-to-castle-square and king-takes-rook spellings both record as e1g1."""
    result = apply_move("4k3/8/8/8/8/8/8/4K2R w K - 0 1", move)
    assert result.move == "e1g1"
    assert result.san == "O-O"
    assert result.fen_after == "4k3/8/8/8/8/8/8/5RK1 b - - 1 1"


@pytest.mark.parametrize(
    ("fen", "move", "phrase"),
    [
        ("not a fen", "e2e4", "invalid FEN"),
        ("8/8/8/8/8/8/8/8 w - - 0 1", "e2e4", "invalid FEN"),
        (START, "e2e5", "illegal move"),
        (START, "e7e5", "illegal move"),
        (START, "0000", "illegal move"),
        (START, "Nf3", "not UCI"),
    ],
)
def test_bad_input_raises_move_error_naming_the_problem(fen, move, phrase):
    """Bad FENs, illegal moves and non-UCI moves raise MoveError with a clear phrase."""
    with pytest.raises(MoveError, match=phrase):
        apply_move(fen, move)


def test_invalid_position_error_lists_status_flag_names():
    """An impossible position's error names the problems, not a raw bitmask."""
    with pytest.raises(MoveError, match="NO_WHITE_KING, NO_BLACK_KING, EMPTY"):
        apply_move("8/8/8/8/8/8/8/8 w - - 0 1", "e2e4")
