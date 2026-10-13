import asyncio
import os

import chess
import chess.engine

MAX_DEPTH = 18
MATE_SCORE = 10000

_analysis_lock = asyncio.Lock()


async def open_engine() -> chess.engine.UciProtocol:
    """Start Stockfish from STOCKFISH_PATH and return the UCI engine."""
    path = os.environ.get("STOCKFISH_PATH")
    if not path:
        raise RuntimeError("STOCKFISH_PATH environment variable is not set")
    _transport, engine = await chess.engine.popen_uci(path)
    return engine


async def analyse(
    engine: chess.engine.UciProtocol,
    board: chess.Board,
    depth: int = 15,
    multipv: int = 3,
) -> list[dict]:
    """Return the engine's top lines, scored from the side to move's view."""
    limit = chess.engine.Limit(depth=min(depth, MAX_DEPTH))
    async with _analysis_lock:
        infos = await engine.analyse(board, limit, multipv=multipv)

    return [
        {
            "score_cp": info["score"].pov(board.turn).score(mate_score=MATE_SCORE),
            "pv": [move.uci() for move in info.get("pv", [])],
        }
        for info in infos
    ]
