"""Stateless move application: compute the position after a move from FEN + UCI."""

from dataclasses import dataclass

import chess


class MoveError(ValueError):
    """Raised when a FEN or move sent by the client cannot be applied."""


@dataclass(frozen=True)
class MoveResult:
    """The outcome of applying one legal move to a position."""

    move: str
    san: str
    fen_before: str
    fen_after: str


def _status_names(board: chess.Board) -> str:
    """List the python-chess status flags that make a position invalid, e.g. 'NO_WHITE_KING, EMPTY'."""
    status = board.status()
    return ", ".join(flag.name for flag in chess.Status if flag and flag in status)


def apply_move(fen: str, move: str) -> MoveResult:
    """Apply a UCI move to a FEN and return both positions, without any stored state.

    fen_before is the canonical FEN that python-chess produces for the input,
    so later lookups (cache keys, the "Why?" endpoint) see one spelling per position.
    """
    try:
        board = chess.Board(fen)
    except ValueError as exc:
        raise MoveError(
            f"invalid FEN {fen!r} ({exc}); expected a valid FEN string"
        ) from exc
    if not board.is_valid():
        raise MoveError(
            f"invalid FEN {fen!r} (illegal position: {_status_names(board)}); "
            "expected a reachable chess position"
        )

    illegal = MoveError(
        f"illegal move {move!r} for FEN {board.fen()!r}; "
        "expected a legal move for the side to move"
    )
    # parse_uci also rewrites king-takes-rook castling (e1h1) to standard UCI (e1g1), so each move has one spelling in history and cache keys.
    try:
        parsed = board.parse_uci(move)
    except chess.InvalidMoveError as exc:
        raise MoveError(
            f"move {move!r} is not UCI notation; expected a UCI move such as 'e2e4'"
        ) from exc
    except chess.IllegalMoveError as exc:
        raise illegal from exc
    if not parsed:  # parse_uci returns the null move for "0000"
        raise illegal

    fen_before = board.fen()
    san = board.san(parsed)
    board.push(parsed)
    return MoveResult(move=parsed.uci(), san=san, fen_before=fen_before, fen_after=board.fen())
