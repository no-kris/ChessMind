import asyncio
import logging

import pytest

from app.services.game_store import (
    STARTING_FEN,
    GameNotFoundError,
    GameStore,
    NoMovesError,
    PositionMismatchError,
)
from app.services.moves import MoveResult

AFTER_E4 = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"

E4 = MoveResult(
    move="e2e4",
    san="e4",
    fen_before="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    fen_after=AFTER_E4,
)
D4 = MoveResult(
    move="d2d4",
    san="d4",
    fen_before="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    fen_after="rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1",
)
E5 = MoveResult(
    move="e7e5",
    san="e5",
    fen_before=AFTER_E4,
    fen_after="rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
)


def test_new_game_starts_at_start_position_with_empty_history():
    """A created game can be fetched and starts empty."""
    store = GameStore()
    game = store.create()
    assert store.get(game.game_id) is game
    assert game.fen == STARTING_FEN
    assert game.history == ()


def test_append_move_returns_ply_index_and_updates_fen():
    """Recorded moves get 0-based ids and move the game's latest FEN forward."""
    store = GameStore()
    game = store.create()
    assert store.append_move(game.game_id, E4) == 0
    assert store.append_move(game.game_id, E5) == 1
    assert game.fen == E5.fen_after


def test_append_move_not_from_current_position_raises_and_records_nothing():
    """A move whose fen_before is not the current position is rejected, leaving history unchanged."""
    store = GameStore()
    game = store.create()
    store.append_move(game.game_id, E4)
    with pytest.raises(PositionMismatchError, match="does not match"):
        store.append_move(game.game_id, D4)
    assert game.history == (E4,)


def test_history_cannot_be_changed_from_outside_the_store():
    """history is a read-only tuple, so callers cannot append around the continuity check."""
    store = GameStore()
    game = store.create()
    with pytest.raises(AttributeError):
        game.history.append(D4)
    assert game.history == ()


def test_two_requests_racing_from_the_same_position_record_only_one_move():
    """The check and the append are one step, so callers that await before appending cannot both win."""
    store = GameStore()
    game_id = store.create().game_id

    async def _post(move: MoveResult) -> str:
        """Mimic a handler that awaits (e.g. an engine call) and then records the move."""
        await asyncio.sleep(0)
        try:
            store.append_move(game_id, move)
        except PositionMismatchError:
            return "rejected"
        return "recorded"

    async def _race() -> list[str]:
        """Run two moves from the start position concurrently."""
        return await asyncio.gather(_post(E4), _post(D4))

    assert sorted(asyncio.run(_race())) == ["recorded", "rejected"]
    assert len(store.get(game_id).history) == 1


def test_pop_move_removes_and_returns_last_move():
    """pop_move returns the last move and rolls the game's FEN back."""
    store = GameStore()
    game = store.create()
    store.append_move(game.game_id, E4)
    assert store.pop_move(game.game_id) == E4
    assert game.history == ()
    assert game.fen == STARTING_FEN


def test_pop_move_on_empty_history_raises():
    """pop_move on a game with no moves raises NoMovesError."""
    store = GameStore()
    game = store.create()
    with pytest.raises(NoMovesError, match="no moves"):
        store.pop_move(game.game_id)


def test_delete_removes_game():
    """A deleted game can no longer be fetched."""
    store = GameStore()
    game = store.create()
    store.delete(game.game_id)
    with pytest.raises(GameNotFoundError):
        store.get(game.game_id)


@pytest.mark.parametrize("operation", ["get", "delete", "append_move", "pop_move"])
def test_unknown_id_raises_not_found(operation):
    """Every lookup by an unknown id raises GameNotFoundError naming the id."""
    store = GameStore()
    args = ("missing", E4) if operation == "append_move" else ("missing",)
    with pytest.raises(GameNotFoundError, match="missing"):
        getattr(store, operation)(*args)


def test_create_move_takeback_and_delete_are_logged_with_the_game_id(caplog):
    """Every change to a game is logged at INFO with its id (coding standards)."""
    caplog.set_level(logging.INFO, logger="app.services.game_store")
    store = GameStore()
    game_id = store.create().game_id
    store.append_move(game_id, E4)
    store.pop_move(game_id)
    store.delete(game_id)
    messages = [record.getMessage() for record in caplog.records]
    assert [m.split(game_id)[0] for m in messages] == ["created game ", "game ", "game ", "deleted game "]
    assert "recorded move 0" in messages[1]
    assert "took back move 0" in messages[2]
