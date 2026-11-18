"""Coach endpoints: the on-demand "Why?" explanation, built by the offline templated fallback only."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.services.coach import MoveNotFoundError, build_fallback_explanation, build_move_context, select_move
from app.services.game_store import GameNotFoundError, GameStore, get_game_store
from app.services.position_analysis import EngineUnavailableError, PositionAnalyser, get_position_analyser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/coach", tags=["coach"])

StoreDep = Annotated[GameStore, Depends(get_game_store)]
AnalyserDep = Annotated[PositionAnalyser, Depends(get_position_analyser)]

_OPERATION = "explain move"


class ExplainRequest(BaseModel):
    """Body of a "Why?" request: which game and which ply to explain."""

    game_id: str
    move_id: int = Field(ge=0)


class ExplainOut(BaseModel):
    """The coach card returned to the UI."""

    verdict: str
    praise: str
    concern: str
    tip: str


def _error(status_code: int, exc: Exception) -> HTTPException:
    """Build an HTTP error whose string detail names the operation and the service's message."""
    return HTTPException(status_code=status_code, detail=f"{_OPERATION} failed: {exc.args[0]}")


@router.post("/explain")
async def explain_move(body: ExplainRequest, store: StoreDep, analyser: AnalyserDep) -> ExplainOut:
    """Explain one recorded move with the templated coach card.

    Checks run in order: unknown game (404), unknown move (404), engine unavailable (503),
    so the engine is never started for a game or move that does not exist.
    """
    try:
        game = store.get(body.game_id)
    except GameNotFoundError as exc:
        logger.info("game %s: rejected explain for move %d (unknown game)", body.game_id, body.move_id)
        raise _error(status.HTTP_404_NOT_FOUND, exc) from exc
    try:
        move = select_move(game, body.move_id)
    except MoveNotFoundError as exc:
        logger.info("game %s: rejected explain for move %d (no such move)", body.game_id, body.move_id)
        raise _error(status.HTTP_404_NOT_FOUND, exc) from exc
    try:
        context = await build_move_context(move, analyser)
    except EngineUnavailableError as exc:
        logger.info("game %s: could not explain move %d (engine unavailable)", body.game_id, body.move_id)
        raise _error(status.HTTP_503_SERVICE_UNAVAILABLE, exc) from exc
    explanation = build_fallback_explanation(context)
    logger.info(
        "game %s: explained move %d (bucket %s, source fallback)", body.game_id, body.move_id, context.bucket
    )
    return ExplainOut(
        verdict=explanation.verdict,
        praise=explanation.praise,
        concern=explanation.concern,
        tip=explanation.tip,
    )
