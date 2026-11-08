"""In-memory session game store: one dict in the server process, nothing persisted."""

import logging
import uuid
from dataclasses import dataclass, field

import chess

from app.services.moves import MoveResult

logger = logging.getLogger(__name__)

STARTING_FEN = chess.STARTING_FEN


class GameNotFoundError(KeyError):
    """Raised when a game id is not in the store."""


class NoMovesError(LookupError):
    """Raised when taking back a move from a game with an empty history."""


class PositionMismatchError(ValueError):
    """Raised when a move does not start from the game's current position (it would leave a gap)."""


@dataclass
class Game:
    """One session game: a gapless move history, changed only through GameStore."""

    game_id: str
    _history: list[MoveResult] = field(default_factory=list, repr=False)

    @property
    def history(self) -> tuple[MoveResult, ...]:
        """Return the moves as a read-only tuple so callers cannot bypass GameStore."""
        return tuple(self._history)

    @property
    def fen(self) -> str:
        """Return the latest position: the last move's result, or the start position."""
        return self._history[-1].fen_after if self._history else STARTING_FEN


class GameStore:
    """Hold session games in a process-local dict so they vanish on restart.

    Methods are synchronous with no awaits, so calls from async handlers on one
    event loop cannot interleave. Requires a single server worker process.
    """

    def __init__(self) -> None:
        """Start with no games."""
        self._games: dict[str, Game] = {}

    def create(self) -> Game:
        """Create a new game with a random id and empty history."""
        game = Game(game_id=uuid.uuid4().hex)
        self._games[game.game_id] = game
        logger.info("created game %s", game.game_id)
        return game

    def get(self, game_id: str) -> Game:
        """Return the game with this id, or raise GameNotFoundError."""
        try:
            return self._games[game_id]
        except KeyError:
            raise GameNotFoundError(
                f"no game with id {game_id!r}; expected an id returned by POST /api/games"
            ) from None

    def append_move(self, game_id: str, result: MoveResult) -> int:
        """Append a move that starts from the game's current position; return its move id.

        The continuity check and the append run in one synchronous call, so no other
        request can slip a move in between, even if the caller awaits beforehand.
        The move id is the 0-based ply index.
        """
        game = self.get(game_id)
        if result.fen_before != game.fen:
            raise PositionMismatchError(
                f"move {result.move!r} starts from {result.fen_before!r}, which does not match "
                f"game {game_id!r}'s current position {game.fen!r}; expected a move from the "
                f"current position (undo with POST /api/games/{game_id}/takeback)"
            )
        game._history.append(result)
        move_id = len(game._history) - 1
        logger.info("game %s: recorded move %d (%s)", game_id, move_id, result.move)
        return move_id

    def pop_move(self, game_id: str) -> MoveResult:
        """Remove and return a game's last move, or raise NoMovesError if it has none."""
        game = self.get(game_id)
        if not game._history:
            raise NoMovesError(
                f"game {game_id!r} has no moves to take back; expected at least one recorded move"
            )
        result = game._history.pop()
        logger.info("game %s: took back move %d (%s)", game_id, len(game._history), result.move)
        return result

    def delete(self, game_id: str) -> None:
        """Remove a game, or raise GameNotFoundError if it does not exist."""
        self.get(game_id)
        del self._games[game_id]
        logger.info("deleted game %s", game_id)

    def clear(self) -> None:
        """Drop every game; used to reset state between tests."""
        self._games.clear()


game_store = GameStore()


def get_game_store() -> GameStore:
    """Return the process-wide store; a FastAPI dependency so tests can override it."""
    return game_store
