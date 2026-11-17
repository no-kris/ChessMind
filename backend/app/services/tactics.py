"""Absolute pin detection: find every piece pinned against its own king in a FEN."""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Literal

import chess

PinColor = Literal["white", "black"]

# White before black on purpose (spec Decision 3); this is NOT alphabetical order.
_SIDES_IN_ORDER: tuple[chess.Color, ...] = (chess.WHITE, chess.BLACK)

_COLOR_NAMES: dict[chess.Color, PinColor] = {
    chess.WHITE: "white",
    chess.BLACK: "black",
}

# (file step, rank step) for each ray leaving a king.
_ORTHOGONAL_STEPS: tuple[tuple[int, int], ...] = ((1, 0), (-1, 0), (0, 1), (0, -1))
_DIAGONAL_STEPS: tuple[tuple[int, int], ...] = ((1, 1), (1, -1), (-1, 1), (-1, -1))

_ORTHOGONAL_SLIDERS: frozenset[chess.PieceType] = frozenset({chess.ROOK, chess.QUEEN})
_DIAGONAL_SLIDERS: frozenset[chess.PieceType] = frozenset({chess.BISHOP, chess.QUEEN})


class TacticsError(ValueError):
    """Raised when a FEN given to a tactics function cannot be analysed."""


@dataclass(frozen=True)
class Pin:
    """One absolute pin: a piece shielding its own king from an enemy slider."""

    pinned_square: str
    pinning_square: str
    king_square: str
    color: PinColor


def _status_names(board: chess.Board) -> str:
    """List the python-chess status flags that make a position invalid."""
    status = board.status()
    return ", ".join(flag.name for flag in chess.Status if flag and flag in status)


def _parse_fen(fen: str) -> chess.Board:
    """Parse and validate a FEN so callers only ever see TacticsError."""
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


def _ray(
    origin: chess.Square, file_step: int, rank_step: int
) -> Iterator[chess.Square]:
    """Yield squares outward from origin in one direction until the board edge."""
    file_index = chess.square_file(origin) + file_step
    rank_index = chess.square_rank(origin) + rank_step
    while 0 <= file_index < 8 and 0 <= rank_index < 8:
        yield chess.square(file_index, rank_index)
        file_index += file_step
        rank_index += rank_step


def _pin_on_ray(
    board: chess.Board,
    king_square: chess.Square,
    side: chess.Color,
    steps: tuple[int, int],
    sliders: frozenset[chess.PieceType],
) -> Pin | None:
    """Return the absolute pin on one ray from the king, or None if there is none."""
    shield_square: chess.Square | None = None
    for square in _ray(king_square, *steps):
        piece = board.piece_at(square)
        if piece is None:
            continue
        if shield_square is None:
            if piece.color != side:
                return None  # enemy piece first: a check or nothing, never a pin
            shield_square = square
            continue
        if piece.color != side and piece.piece_type in sliders:
            return Pin(
                pinned_square=chess.square_name(shield_square),
                pinning_square=chess.square_name(square),
                king_square=chess.square_name(king_square),
                color=_COLOR_NAMES[side],
            )
        return None  # second piece is own-colour, a non-slider or the wrong slider
    return None


def _pins_for_side(board: chess.Board, side: chess.Color) -> list[Pin]:
    """Return every absolute pin against one side's king, by pinned square index."""
    king_square = board.king(side)
    if king_square is None:  # unreachable after is_valid(); narrows the type
        return []
    rays = [(steps, _ORTHOGONAL_SLIDERS) for steps in _ORTHOGONAL_STEPS]
    rays += [(steps, _DIAGONAL_SLIDERS) for steps in _DIAGONAL_STEPS]
    pins: list[Pin] = []
    for steps, sliders in rays:
        pin = _pin_on_ray(board, king_square, side, steps, sliders)
        if pin is not None:
            pins.append(pin)
    return sorted(pins, key=lambda pin: chess.parse_square(pin.pinned_square))


def find_pins(fen: str) -> tuple[Pin, ...]:
    """Return all absolute pins for both sides, white's first, so callers can flag them.

    Pins are geometric and do not depend on the side to move. Raises
    TacticsError if the FEN does not parse or describes an illegal position.
    """
    board = _parse_fen(fen)
    pins: list[Pin] = []
    for side in _SIDES_IN_ORDER:
        pins.extend(_pins_for_side(board, side))
    return tuple(pins)
