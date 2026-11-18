"""API tests for POST /api/coach/explain, with the engine replaced by a fake analyser.

Spec: docs/orchestrator-runs/coach-explain-2026-11-17/spec.md, section 5.3. Uses TestClient(app)
and overrides the get_position_analyser dependency, so no test needs Stockfish.

The new production modules are imported at call time, never at module level. Until they exist
and main.py includes the coach router, /api/coach/explain is not routed, so every test here gets
a 404 "Not Found" and fails on its status or detail assertion rather than on an import error.
"""

import importlib

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

EXPLAIN = "/api/coach/explain"
POSITION_ANALYSIS = "app.services.position_analysis"

# Reachable positions from spec section 4 (UCI from the start position).
PIN_ON_OPPONENT = ["d2d4", "d7d5", "c2c4", "e7e6", "b1c3", "f8b4"]  # move 5: Black pins Nc3 to e1
PIN_ON_OWN = ["d2d4", "e7e6", "c2c4", "f8b4", "b1c3"]  # move 4: White blocks with Nc3, now pinned

CARD_KEYS = {"verdict", "praise", "concern", "tip"}


class FakeAnalyser:
    """Async stand-in for the position analyser: canned lines per FEN, and a log of every call."""

    def __init__(self) -> None:
        """Start with no canned lines, an empty call log and a working engine."""
        self.lines_by_fen: dict[str, list[dict]] = {}
        self.calls: list[str] = []
        self.unavailable = False

    def score(self, fen: str, score_cp: int, pv: list[str] | None = None) -> None:
        """Make the analyser return one line with this side-to-move score and pv for `fen`."""
        self.lines_by_fen[fen] = [{"score_cp": score_cp, "pv": list(pv or [])}]

    async def __call__(self, fen: str) -> list[dict]:
        """Record the FEN, then raise EngineUnavailableError if the engine is 'down', else return lines."""
        self.calls.append(fen)
        if self.unavailable:
            error = importlib.import_module(POSITION_ANALYSIS).EngineUnavailableError
            raise error("engine unavailable (fake engine is down); expected a working Stockfish binary at STOCKFISH_PATH")
        if fen not in self.lines_by_fen:
            raise AssertionError(f"analyser called with unexpected FEN {fen!r}")
        return self.lines_by_fen[fen]


def _analyser_dependency():
    """Return get_position_analyser, or None while app.services.position_analysis does not exist.

    Only the missing module itself is tolerated; any other import error propagates. Without the
    module the coach router cannot exist either, so skipping the override then cannot let a request
    reach a real engine.
    """
    try:
        module = importlib.import_module(POSITION_ANALYSIS)
    except ModuleNotFoundError as exc:
        if exc.name != POSITION_ANALYSIS:
            raise
        return None
    return module.get_position_analyser


@pytest.fixture(autouse=True)
def fake_analyser():
    """Install a fresh FakeAnalyser as the analyser dependency for every test, and remove it after."""
    fake = FakeAnalyser()
    dependency = _analyser_dependency()
    if dependency is not None:
        # FastAPI calls the override to get the dependency's value, so return the fake, don't be it.
        app.dependency_overrides[dependency] = lambda: fake
    yield fake
    if dependency is not None:
        app.dependency_overrides.pop(dependency, None)


def _new_game() -> dict:
    """Create a game through the API and return its body."""
    res = client.post("/api/games")
    assert res.status_code == 201, res.text
    return res.json()


def _play(ucis: list[str]) -> tuple[str, list[dict]]:
    """Create a game, post these UCI moves in order, and return the game id and each MoveOut body."""
    game = _new_game()
    fen = game["fen"]
    moves: list[dict] = []
    for uci in ucis:
        res = client.post(f"/api/games/{game['game_id']}/moves", json={"fen": fen, "move": uci})
        assert res.status_code == 201, res.text
        moves.append(res.json())
        fen = res.json()["fen_after"]
    return game["game_id"], moves


def _explain(game_id: str, move_id: int):
    """POST a "Why?" request for one move."""
    return client.post(EXPLAIN, json={"game_id": game_id, "move_id": move_id})


def _play_e4_scored_as_mistake(fake: FakeAnalyser) -> str:
    """Play 1.e4 and score it as a 150 CP loss (mistake) with best move d2d4; return the game id."""
    game_id, moves = _play(["e2e4"])
    fake.score(moves[0]["fen_before"], 50, ["d2d4"])
    fake.score(moves[0]["fen_after"], 100)
    return game_id


def test_explain_returns_200_with_exactly_four_string_keys(fake_analyser: FakeAnalyser) -> None:
    game_id = _play_e4_scored_as_mistake(fake_analyser)

    res = _explain(game_id, 0)

    assert res.status_code == 200
    body = res.json()
    assert set(body) == CARD_KEYS
    assert all(isinstance(value, str) for value in body.values())


def test_explain_mistake_returns_templated_card(fake_analyser: FakeAnalyser) -> None:
    game_id = _play_e4_scored_as_mistake(fake_analyser)

    res = _explain(game_id, 0)

    assert res.status_code == 200
    assert res.json() == {
        "verdict": "Mistake — 150 CP lost.",
        "praise": "The idea is understandable",
        "concern": "Gives away a clear edge",
        "tip": "Consider d2d4 instead.",
    }


def test_explain_reports_pin_on_opponent_in_praise(fake_analyser: FakeAnalyser) -> None:
    game_id, moves = _play(PIN_ON_OPPONENT)
    fake_analyser.score(moves[5]["fen_before"], 20, ["f8b4"])
    fake_analyser.score(moves[5]["fen_after"], -20)  # delta 0: good

    res = _explain(game_id, 5)

    assert res.status_code == 200
    assert res.json() == {
        "verdict": "Good — 0 CP lost.",
        "praise": "Pins an enemy piece",
        "concern": "Nothing major",
        "tip": "Keep checking captures, checks and threats.",
    }


def test_explain_reports_own_pinned_piece_in_concern(fake_analyser: FakeAnalyser) -> None:
    game_id, moves = _play(PIN_ON_OWN)
    fake_analyser.score(moves[4]["fen_before"], 10, ["c1d2"])
    fake_analyser.score(moves[4]["fen_after"], 40)  # delta 50: inaccuracy

    res = _explain(game_id, 4)

    assert res.status_code == 200
    assert res.json() == {
        "verdict": "Inaccuracy — 50 CP lost.",
        "praise": "A reasonable idea",
        "concern": "Leaves your piece pinned",
        "tip": "Consider c1d2 instead.",
    }


def test_explain_uses_move_id_as_zero_based_ply_index(fake_analyser: FakeAnalyser) -> None:
    game_id, moves = _play(["e2e4", "e7e5"])
    fake_analyser.score(moves[0]["fen_before"], 30, ["d2d4"])
    fake_analyser.score(moves[0]["fen_after"], -30, ["c7c5"])  # move 0: 30 - 30 = 0, good
    fake_analyser.score(moves[1]["fen_after"], 230, ["g1f3"])  # move 1: -30 + 230 = 200, mistake

    first = _explain(game_id, 0)
    second = _explain(game_id, 1)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["verdict"] == "Good — 0 CP lost."
    assert second.json()["verdict"] == "Mistake — 200 CP lost."
    assert second.json()["tip"] == "Consider c7c5 instead."


def test_explain_unknown_game_returns_404() -> None:
    res = _explain("nope", 0)

    assert res.status_code == 404
    detail = res.json()["detail"]
    assert "explain move failed" in detail
    assert "no game with id" in detail


@pytest.mark.parametrize(
    ("ucis", "move_id"),
    [(["e2e4"], 1), ([], 0)],
    ids=["one_move_id_1", "no_moves_id_0"],
)
def test_explain_move_id_out_of_range_returns_404(ucis: list[str], move_id: int) -> None:
    game_id, _moves = _play(ucis)

    res = _explain(game_id, move_id)

    assert res.status_code == 404
    detail = res.json()["detail"]
    assert "explain move failed" in detail
    assert "no move with id" in detail


def test_explain_negative_move_id_returns_422_with_string_detail() -> None:
    game_id, _moves = _play(["e2e4"])

    res = _explain(game_id, -1)

    assert res.status_code == 422
    detail = res.json()["detail"]
    assert isinstance(detail, str)
    assert "invalid request" in detail
    assert "move_id" in detail


@pytest.mark.parametrize("missing", ["game_id", "move_id"])
def test_explain_missing_field_returns_422_with_string_detail(missing: str) -> None:
    game_id, _moves = _play(["e2e4"])
    body = {"game_id": game_id, "move_id": 0}
    del body[missing]

    res = client.post(EXPLAIN, json=body)

    assert res.status_code == 422
    detail = res.json()["detail"]
    assert isinstance(detail, str)
    assert "invalid request" in detail
    assert missing in detail


def test_explain_unknown_game_does_not_call_engine(fake_analyser: FakeAnalyser) -> None:
    res = _explain("nope", 0)

    assert res.status_code == 404
    assert "explain move failed" in res.json()["detail"]
    assert fake_analyser.calls == []


def test_explain_out_of_range_move_does_not_call_engine(fake_analyser: FakeAnalyser) -> None:
    game_id, _moves = _play(["e2e4"])

    res = _explain(game_id, 1)

    assert res.status_code == 404
    assert "no move with id" in res.json()["detail"]
    assert fake_analyser.calls == []


def test_explain_engine_unavailable_returns_503(fake_analyser: FakeAnalyser) -> None:
    game_id, _moves = _play(["e2e4"])
    fake_analyser.unavailable = True

    res = _explain(game_id, 0)

    assert res.status_code == 503
    detail = res.json()["detail"]
    assert "explain move failed" in detail
    assert "engine unavailable" in detail


def test_explain_does_not_change_game_history(fake_analyser: FakeAnalyser) -> None:
    game_id, moves = _play(["e2e4", "e7e5"])
    fake_analyser.score(moves[1]["fen_before"], -30, ["c7c5"])
    fake_analyser.score(moves[1]["fen_after"], 30)
    before = client.get(f"/api/games/{game_id}").json()

    res = _explain(game_id, 1)

    assert res.status_code == 200
    assert client.get(f"/api/games/{game_id}").json() == before


def test_explain_after_takeback_explains_the_replacement_move(fake_analyser: FakeAnalyser) -> None:
    # decision-006: move_id is reused after a takeback; this slice explains the move now at the index.
    game_id, moves = _play(["e2e4"])
    start = moves[0]["fen_before"]
    assert client.post(f"/api/games/{game_id}/takeback").status_code == 200
    replacement = client.post(f"/api/games/{game_id}/moves", json={"fen": start, "move": "d2d4"})
    assert replacement.status_code == 201
    fake_analyser.score(start, 20, ["e2e4"])
    fake_analyser.score(replacement.json()["fen_after"], -20)

    res = _explain(game_id, 0)

    assert res.status_code == 200
    assert fake_analyser.calls == [start, replacement.json()["fen_after"]]
