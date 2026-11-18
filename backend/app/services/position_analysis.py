"""Production engine boundary for the coach: analyse one position with Stockfish on demand."""

import logging
from collections.abc import Awaitable, Callable

import chess
import chess.engine

from app.services import engine as engine_service

logger = logging.getLogger(__name__)

PositionAnalyser = Callable[[str], Awaitable[list[dict]]]
"""Takes a canonical FEN and returns engine.analyse-shaped lines, best line first.

Each line is {"score_cp": int, "pv": [uci, ...]}, scored from the side to move's point of view.
"""

_EXPECTED = "expected a working Stockfish binary at STOCKFISH_PATH"


class EngineUnavailableError(RuntimeError):
    """Raised when the engine cannot be started or returns no analysis."""


def _unavailable(reason: str) -> EngineUnavailableError:
    """Build the error for an unusable engine; the reason is fixed text, never the env var's value."""
    return EngineUnavailableError(f"engine unavailable ({reason}); {_EXPECTED}")


async def _open_engine() -> chess.engine.UciProtocol:
    """Start Stockfish via engine.open_engine, turning every startup failure into EngineUnavailableError."""
    try:
        return await engine_service.open_engine()
    except OSError as exc:
        # The OSError text can include the binary path, so it is not copied into the message.
        raise _unavailable("could not start the engine process") from exc
    except chess.engine.EngineError as exc:
        raise _unavailable("the engine failed during startup") from exc
    except RuntimeError as exc:
        # open_engine raises a plain RuntimeError only when STOCKFISH_PATH is unset.
        raise _unavailable("STOCKFISH_PATH is not set") from exc


async def _quit_engine(uci_engine: chess.engine.UciProtocol) -> None:
    """Shut the engine down, logging instead of raising so a failed quit never hides the real result."""
    try:
        await uci_engine.quit()
    except (chess.engine.EngineError, OSError) as exc:
        logger.warning("engine did not quit cleanly (%s)", type(exc).__name__)


async def analyse_position(fen: str) -> list[dict]:
    """Open Stockfish, analyse one position (multipv=1), close it, and return the lines."""
    uci_engine = await _open_engine()
    try:
        return await engine_service.analyse(uci_engine, chess.Board(fen), multipv=1)
    except chess.engine.EngineError as exc:
        raise _unavailable("the engine failed during analysis") from exc
    except OSError as exc:
        raise _unavailable("lost contact with the engine process") from exc
    finally:
        await _quit_engine(uci_engine)


def get_position_analyser() -> PositionAnalyser:
    """Return analyse_position; a FastAPI dependency so tests can swap in a fake."""
    return analyse_position
