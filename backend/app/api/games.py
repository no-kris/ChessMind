"""Game and move endpoints backed by the in-memory session store. No engine calls."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel

from app.services.game_store import (
    Game,
    GameNotFoundError,
    GameStore,
    NoMovesError,
    PositionMismatchError,
    get_game_store,
)
from app.services.moves import MoveError, MoveResult, apply_move

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/games", tags=["games"])

StoreDep = Annotated[GameStore, Depends(get_game_store)]


class MoveRequest(BaseModel):
    """Body of a move request: the position the client holds and a UCI move."""

    fen: str
    move: str


class MoveOut(BaseModel):
    """One recorded move and the positions before and after it."""

    move_id: int
    move: str
    san: str
    fen_before: str
    fen_after: str


class GameOut(BaseModel):
    """A game's id, latest position and move history."""

    game_id: str
    fen: str
    history: list[MoveOut]


def _move_out(move_id: int, result: MoveResult) -> MoveOut:
    """Convert a stored move into its response shape."""
    return MoveOut(
        move_id=move_id,
        move=result.move,
        san=result.san,
        fen_before=result.fen_before,
        fen_after=result.fen_after,
    )


def _game_out(game: Game) -> GameOut:
    """Convert a stored game into its response shape."""
    return GameOut(
        game_id=game.game_id,
        fen=game.fen,
        history=[_move_out(i, result) for i, result in enumerate(game.history)],
    )


def _not_found(operation: str, exc: GameNotFoundError) -> HTTPException:
    """Build a 404 that names the failed operation and the missing id."""
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{operation} failed: {exc.args[0]}")


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_game(store: StoreDep) -> GameOut:
    """Start a new session game at the standard starting position."""
    return _game_out(store.create())


@router.get("/{game_id}")
async def get_game(game_id: str, store: StoreDep) -> GameOut:
    """Return a game's latest position and history."""
    try:
        return _game_out(store.get(game_id))
    except GameNotFoundError as exc:
        raise _not_found("get game", exc) from exc


@router.post("/{game_id}/moves", status_code=status.HTTP_201_CREATED)
async def post_move(game_id: str, body: MoveRequest, store: StoreDep) -> MoveOut:
    """Compute the position after the client's FEN + move and record it in the game's history.

    The result is computed from the request alone; the store records it only if it
    starts from the game's current position, so history never has gaps.
    Checks run in order: unknown game (404), bad FEN or move (400), FEN mismatch (409).
    """
    try:
        store.get(game_id)
    except GameNotFoundError as exc:
        raise _not_found("post move", exc) from exc
    try:
        result = apply_move(body.fen, body.move)
    except MoveError as exc:
        logger.info("game %s: rejected move %r", game_id, body.move)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"post move failed: {exc}") from exc
    try:
        move_id = store.append_move(game_id, result)
    except PositionMismatchError as exc:
        logger.info("game %s: rejected move %r from a position that is not the current one", game_id, body.move)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"post move failed: {exc}") from exc
    return _move_out(move_id, result)


@router.post("/{game_id}/takeback")
async def take_back_move(game_id: str, store: StoreDep) -> GameOut:
    """Remove the game's last move and return the game at the position before it."""
    try:
        store.pop_move(game_id)
        return _game_out(store.get(game_id))
    except GameNotFoundError as exc:
        raise _not_found("take back move", exc) from exc
    except NoMovesError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"take back move failed: {exc.args[0]}"
        ) from exc


@router.delete("/{game_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_game(game_id: str, store: StoreDep) -> Response:
    """Delete a game and its history."""
    try:
        store.delete(game_id)
    except GameNotFoundError as exc:
        raise _not_found("delete game", exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
