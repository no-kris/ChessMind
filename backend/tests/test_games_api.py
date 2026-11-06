import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
AFTER_E4 = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"


def _new_game_id() -> str:
    """Create a game through the API and return its id."""
    return client.post("/api/games").json()["game_id"]


def test_create_game_returns_201_with_start_position():
    """Creating a game returns its id, the start FEN and no history."""
    res = client.post("/api/games")
    assert res.status_code == 201
    body = res.json()
    assert body["game_id"]
    assert body["fen"] == START
    assert body["history"] == []


def test_get_game_returns_created_game():
    """A created game can be fetched by id."""
    game_id = _new_game_id()
    res = client.get(f"/api/games/{game_id}")
    assert res.status_code == 200
    assert res.json() == {"game_id": game_id, "fen": START, "history": []}


@pytest.mark.parametrize(
    ("method", "path", "operation"),
    [
        ("get", "/api/games/nope", "get game"),
        ("delete", "/api/games/nope", "delete game"),
        ("post", "/api/games/nope/moves", "post move"),
        ("post", "/api/games/nope/takeback", "take back move"),
    ],
)
def test_unknown_game_returns_404(method, path, operation):
    """Every game route answers 404 for an unknown id and names the operation."""
    kwargs = {"json": {"fen": START, "move": "e2e4"}} if path.endswith("/moves") else {}
    res = client.request(method.upper(), path, **kwargs)
    assert res.status_code == 404
    assert operation in res.json()["detail"]
    assert "nope" in res.json()["detail"]


def test_legal_move_returns_201_and_is_recorded():
    """A legal move returns the computed position and appears in the game history."""
    game_id = _new_game_id()
    res = client.post(f"/api/games/{game_id}/moves", json={"fen": START, "move": "e2e4"})
    assert res.status_code == 201
    expected = {"move_id": 0, "move": "e2e4", "san": "e4", "fen_before": START, "fen_after": AFTER_E4}
    assert res.json() == expected
    game = client.get(f"/api/games/{game_id}").json()
    assert game["history"] == [expected]
    assert game["fen"] == AFTER_E4


def test_consecutive_moves_chain_without_gaps():
    """A second move sent from the first move's result is accepted and gets move_id 1."""
    game_id = _new_game_id()
    client.post(f"/api/games/{game_id}/moves", json={"fen": START, "move": "e2e4"})
    res = client.post(f"/api/games/{game_id}/moves", json={"fen": AFTER_E4, "move": "e7e5"})
    assert res.status_code == 201
    assert res.json()["move_id"] == 1
    assert res.json()["fen_before"] == AFTER_E4


@pytest.mark.parametrize(
    "fen",
    [
        "4k3/8/8/8/8/8/8/4K2R w K - 0 1",  # a different, legal position
        START,  # the start position, after a move has already been played (a stale client)
    ],
)
def test_move_from_a_position_that_is_not_current_returns_409(fen):
    """A legal move from any position other than the game's current one is rejected and not recorded."""
    game_id = _new_game_id()
    client.post(f"/api/games/{game_id}/moves", json={"fen": START, "move": "e2e4"})
    move = "e1g1" if fen != START else "d2d4"
    res = client.post(f"/api/games/{game_id}/moves", json={"fen": fen, "move": move})
    assert res.status_code == 409
    assert "does not match" in res.json()["detail"]
    assert len(client.get(f"/api/games/{game_id}").json()["history"]) == 1


def test_fen_with_irrelevant_ep_square_still_matches_current_position():
    """FENs are compared in canonical form, so an uncapturable en-passant square is not a mismatch."""
    game_id = _new_game_id()
    client.post(f"/api/games/{game_id}/moves", json={"fen": START, "move": "e2e4"})
    fen_with_ep = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    res = client.post(f"/api/games/{game_id}/moves", json={"fen": fen_with_ep, "move": "e7e5"})
    assert res.status_code == 201


def test_bad_move_from_wrong_position_returns_400_not_409():
    """Bad input is reported before a position mismatch."""
    game_id = _new_game_id()
    res = client.post(f"/api/games/{game_id}/moves", json={"fen": AFTER_E4, "move": "e2e5"})
    assert res.status_code == 400


def test_takeback_removes_last_move_and_returns_previous_position():
    """Taking back returns the game at the position before the last move."""
    game_id = _new_game_id()
    client.post(f"/api/games/{game_id}/moves", json={"fen": START, "move": "e2e4"})
    res = client.post(f"/api/games/{game_id}/takeback")
    assert res.status_code == 200
    assert res.json() == {"game_id": game_id, "fen": START, "history": []}


def test_takeback_then_different_move_is_accepted():
    """After a takeback the client can play a different move from the restored position."""
    game_id = _new_game_id()
    client.post(f"/api/games/{game_id}/moves", json={"fen": START, "move": "e2e4"})
    client.post(f"/api/games/{game_id}/takeback")
    res = client.post(f"/api/games/{game_id}/moves", json={"fen": START, "move": "d2d4"})
    assert res.status_code == 201
    assert res.json()["move_id"] == 0
    assert [m["move"] for m in client.get(f"/api/games/{game_id}").json()["history"]] == ["d2d4"]


def test_takeback_with_no_moves_returns_409():
    """Taking back on an empty history is rejected."""
    game_id = _new_game_id()
    res = client.post(f"/api/games/{game_id}/takeback")
    assert res.status_code == 409
    assert "no moves to take back" in res.json()["detail"]


@pytest.mark.parametrize(
    ("fen", "move", "phrase"),
    [
        (START, "e2e5", "illegal move"),
        ("garbage", "e2e4", "invalid FEN"),
        (START, "Nf3", "not UCI"),
    ],
)
def test_bad_move_returns_400_and_leaves_history_unchanged(fen, move, phrase):
    """Illegal moves and invalid FENs are rejected with 400 and nothing is recorded."""
    game_id = _new_game_id()
    res = client.post(f"/api/games/{game_id}/moves", json={"fen": fen, "move": move})
    assert res.status_code == 400
    assert res.json()["detail"].startswith("post move failed: ")
    assert phrase in res.json()["detail"]
    assert client.get(f"/api/games/{game_id}").json()["history"] == []


def test_delete_game_returns_204_then_get_is_404():
    """A deleted game is gone."""
    game_id = _new_game_id()
    assert client.delete(f"/api/games/{game_id}").status_code == 204
    assert client.get(f"/api/games/{game_id}").status_code == 404


def test_move_path_never_calls_the_engine(monkeypatch):
    """Posting a move succeeds even when every engine entry point raises."""

    def _engine_called(*args, **kwargs):
        """Fail loudly if anything reaches the engine."""
        raise AssertionError("engine must not be called on the move path")

    monkeypatch.setattr("app.services.engine.open_engine", _engine_called)
    monkeypatch.setattr("app.services.engine.analyse", _engine_called)
    game_id = _new_game_id()
    res = client.post(f"/api/games/{game_id}/moves", json={"fen": START, "move": "e2e4"})
    assert res.status_code == 201
