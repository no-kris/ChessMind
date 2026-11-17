"""Absolute pin detection: find pieces that cannot leave their line without exposing their own king."""

import logging
from dataclasses import dataclass

import chess

logger = logging.getLogger(__name__)

_ORTHOGONAL_SLIDERS = (chess.ROOK, chess.QUEEN)
_DIAGONAL_SLIDERS = (chess.BISHOP, chess.QUEEN)
_SLIDER_TYPES = (chess.BISHOP, chess.ROOK, chess.QUEEN)


class TacticsError(ValueError):
    """Raised when a tactics query gets input it cannot analyse, such as an invalid FEN."""


@dataclass(frozen=True)
class Pin:
    """One absolute pin: a piece that cannot leave its line without exposing its own king."""

    pinned_square: str
    pinner_square: str
    king_square: str
    pinned_color: str
    pinned_piece: str


def _status_names(board: chess.Board) -> str:
    """List the python-chess status flags that make a position invalid, e.g. 'NO_WHITE_KING, EMPTY'."""
    status = board.status()
    return ", ".join(flag.name for flag in chess.Status if flag and flag in status)


def _parse_board(fen: str) -> chess.Board:
    """Parse a FEN into a valid board, raising TacticsError so callers never see a bare ValueError."""
    try:
        board = chess.Board(fen)
    except ValueError as exc:
        raise TacticsError(
            f"invalid FEN {fen!r} ({exc}); expected a valid FEN string"
        ) from exc
    if not board.is_valid():
        raise TacticsError(
            f"invalid FEN {fen!r} (illegal position: {_status_names(board)}); "
            "expected a reachable chess position"
        )
    return board


def _slider_matches_line(piece_type: chess.PieceType, king: chess.Square, slider: chess.Square) -> bool:
    """Tell whether a slider of this type moves along the line joining it to the king."""
    file_gap = abs(chess.square_file(king) - chess.square_file(slider))
    rank_gap = abs(chess.square_rank(king) - chess.square_rank(slider))
    if file_gap == 0 or rank_gap == 0:
        return piece_type in _ORTHOGONAL_SLIDERS
    if file_gap == rank_gap:
        return piece_type in _DIAGONAL_SLIDERS
    return False


def _pins_against(board: chess.Board, color: chess.Color) -> list[Pin]:
    """Find every piece of one color absolutely pinned to its own king by an enemy slider."""
    king = board.king(color)
    if king is None:
        return []
    pins: list[Pin] = []
    for piece_type in _SLIDER_TYPES:
        for slider in board.pieces(piece_type, not color):
            if not _slider_matches_line(piece_type, king, slider):
                continue
            blockers = chess.between(king, slider) & board.occupied
            if chess.popcount(blockers) != 1:
                continue
            pinned = chess.lsb(blockers)
            piece = board.piece_at(pinned)
            if piece is None or piece.color != color:
                continue
            pins.append(
                Pin(
                    pinned_square=chess.square_name(pinned),
                    pinner_square=chess.square_name(slider),
                    king_square=chess.square_name(king),
                    pinned_color=chess.COLOR_NAMES[color],
                    pinned_piece=chess.PIECE_NAMES[piece.piece_type],
                )
            )
    return pins


def find_pins(fen: str) -> list[Pin]:
    """Return every absolute pin for both colors in the position, ordered by pinned square."""
    board = _parse_board(fen)
    pins = _pins_against(board, chess.WHITE) + _pins_against(board, chess.BLACK)
    pins.sort(key=lambda pin: chess.parse_square(pin.pinned_square))
    logger.debug("found %d absolute pins in %s", len(pins), board.fen())
    return pins
