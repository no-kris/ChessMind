"""Coaching service: rebuild a played move's context and turn it into the offline templated coach card.

No FastAPI and no LLM here. The engine is reached only through the injected PositionAnalyser.
"""

import logging
from dataclasses import dataclass

import chess

from app.services import classify, tactics
from app.services.engine import MATE_SCORE
from app.services.game_store import Game
from app.services.moves import MoveResult
from app.services.position_analysis import EngineUnavailableError, PositionAnalyser

logger = logging.getLogger(__name__)

PROMPT_VERSION = 1
SCHEMA_VERSION = 1
OWN_PIECE_PINNED = "own_piece_pinned"
OPPONENT_PIECE_PINNED = "opponent_piece_pinned"

_LABELS = {"good": "Good", "inaccuracy": "Inaccuracy", "mistake": "Mistake", "blunder": "Blunder"}
_PRAISE = {
    "good": "Solid, engine-approved choice",
    "inaccuracy": "A reasonable idea",
    "mistake": "The idea is understandable",
    "blunder": "Still time to fight back",
}
_CONCERN = {
    "good": "Nothing major",
    "inaccuracy": "Slightly imprecise",
    "mistake": "Gives away a clear edge",
    "blunder": "Throws away the position",
}
_PRAISE_OPPONENT_PINNED = "Pins an enemy piece"
_CONCERN_OWN_PINNED = "Leaves your piece pinned"
_TIP_GOOD = "Keep checking captures, checks and threats."
_TIP_NO_BEST_LINE = "Check every capture and threat before moving."


class MoveNotFoundError(LookupError):
    """Raised when a move_id is not a valid ply index in the game's history."""


@dataclass(frozen=True)
class MoveContext:
    """Structured context for one played move (plan Phase 5), the input to the explanation templates."""

    fen: str
    move: str
    san: str
    delta_cp: int
    bucket: str
    tactical_alerts: tuple[str, ...]
    best_line: str
    prompt_version: int = PROMPT_VERSION
    schema_version: int = SCHEMA_VERSION


@dataclass(frozen=True)
class Explanation:
    """The coach card: verdict, praise, concern and tip."""

    verdict: str
    praise: str
    concern: str
    tip: str


def select_move(game: Game, move_id: int) -> MoveResult:
    """Return the move at this 0-based ply index, or raise MoveNotFoundError (negatives never wrap)."""
    history = game.history
    if 0 <= move_id < len(history):
        return history[move_id]
    if not history:
        expected = "expected a game with at least one recorded move"
    else:
        expected = f"expected a move_id from 0 to {len(history) - 1}"
    raise MoveNotFoundError(f"no move with id {move_id} in game {game.game_id!r}; {expected}")


async def _best_line_of(analyser: PositionAnalyser, fen: str) -> dict:
    """Run the analyser on one FEN and return its best line, or raise EngineUnavailableError if empty."""
    lines = await analyser(fen)
    if not lines:
        raise EngineUnavailableError(f"engine returned no analysis for FEN {fen!r}; expected at least one line")
    return lines[0]


async def _result_score(analyser: PositionAnalyser, fen_after: str) -> int:
    """Score the position after the move for the opponent; finished games skip the engine."""
    board_after = chess.Board(fen_after)
    if board_after.is_checkmate():
        return -MATE_SCORE
    if board_after.is_game_over(claim_draw=False):
        return 0
    return (await _best_line_of(analyser, fen_after))["score_cp"]


def _pin_alerts(move: MoveResult) -> tuple[str, ...]:
    """List pin alerts after the move: own-piece pin first, then opponent pin, each at most once."""
    mover = chess.COLOR_NAMES[chess.Board(move.fen_before).turn]
    pinned_colors = {pin.pinned_color for pin in tactics.find_pins(move.fen_after)}
    alerts: list[str] = []
    if mover in pinned_colors:
        alerts.append(OWN_PIECE_PINNED)
    if pinned_colors - {mover}:
        alerts.append(OPPONENT_PIECE_PINNED)
    return tuple(alerts)


async def build_move_context(move: MoveResult, analyser: PositionAnalyser) -> MoveContext:
    """Evaluate a recorded move with the analyser and the pin detector and bundle its context."""
    best = await _best_line_of(analyser, move.fen_before)
    best_cp = best["score_cp"]
    best_line = " ".join(best["pv"])
    result_cp = await _result_score(analyser, move.fen_after)
    delta_cp = classify.eval_loss(best_cp, result_cp)
    return MoveContext(
        fen=move.fen_before,
        move=move.move,
        san=move.san,
        delta_cp=delta_cp,
        bucket=classify.bucket(delta_cp),
        tactical_alerts=_pin_alerts(move),
        best_line=best_line,
    )


def _tip(context: MoveContext) -> str:
    """Pick the tip: general advice for a good move, otherwise the engine's best move if known."""
    if context.bucket == "good":
        return _TIP_GOOD
    best_moves = context.best_line.split()
    if best_moves:
        return f"Consider {best_moves[0]} instead."
    return _TIP_NO_BEST_LINE


def build_fallback_explanation(context: MoveContext) -> Explanation:
    """Build the templated coach card from bucket, centipawn loss, alerts and best line."""
    alerts = context.tactical_alerts
    praise = _PRAISE_OPPONENT_PINNED if OPPONENT_PIECE_PINNED in alerts else _PRAISE[context.bucket]
    concern = _CONCERN_OWN_PINNED if OWN_PIECE_PINNED in alerts else _CONCERN[context.bucket]
    return Explanation(
        verdict=f"{_LABELS[context.bucket]} — {context.delta_cp} CP lost.",
        praise=praise,
        concern=concern,
        tip=_tip(context),
    )
