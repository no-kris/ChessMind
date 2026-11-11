"""Unit tests for app.services.engine that mock the Stockfish boundary (no binary needed)."""

import asyncio

import chess
import chess.engine
import pytest

from app.services import engine as engine_module
from app.services.engine import analyse, open_engine

BLACK_TO_MOVE_FEN = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"


class FakeEngine:
    """Stand-in for a UCI engine that records its calls and returns canned infos."""

    def __init__(self, infos: list[dict] | None = None) -> None:
        """Store the infos to return and start with an empty call log."""
        self.infos = infos if infos is not None else []
        self.calls: list[dict] = []
        self.active = 0
        self.max_active = 0

    async def analyse(
        self, board: chess.Board, limit: chess.engine.Limit, multipv: int = 1
    ) -> list[dict]:
        """Record the request, yield to the event loop once, and return the canned infos."""
        self.calls.append({"board": board, "limit": limit, "multipv": multipv})
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        loop = asyncio.get_running_loop()
        tick = loop.create_future()
        loop.call_soon(tick.set_result, None)
        await tick
        self.active -= 1
        return self.infos


def _info(score: chess.engine.Score, turn: chess.Color, pv: list[str] | None) -> dict:
    """Build one engine info dict with a score relative to `turn` and an optional pv."""
    info: dict = {"score": chess.engine.PovScore(score, turn)}
    if pv is not None:
        info["pv"] = [chess.Move.from_uci(uci) for uci in pv]
    return info


@pytest.mark.parametrize("value", [None, ""])
@pytest.mark.anyio
async def test_open_engine_without_stockfish_path_raises_runtime_error(
    monkeypatch: pytest.MonkeyPatch, value: str | None
) -> None:
    if value is None:
        monkeypatch.delenv("STOCKFISH_PATH", raising=False)
    else:
        monkeypatch.setenv("STOCKFISH_PATH", value)

    async def _must_not_start(path: str) -> None:
        raise AssertionError("popen_uci must not be called without STOCKFISH_PATH")

    monkeypatch.setattr(chess.engine, "popen_uci", _must_not_start)

    with pytest.raises(RuntimeError, match="STOCKFISH_PATH"):
        await open_engine()


@pytest.mark.anyio
async def test_open_engine_starts_the_binary_at_stockfish_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("STOCKFISH_PATH", "/opt/fake/stockfish")
    started: list[str] = []
    sentinel_engine = object()

    async def _fake_popen_uci(path: str) -> tuple[object, object]:
        started.append(path)
        return object(), sentinel_engine

    monkeypatch.setattr(chess.engine, "popen_uci", _fake_popen_uci)

    result = await open_engine()

    assert started == ["/opt/fake/stockfish"]
    assert result is sentinel_engine


@pytest.mark.parametrize(
    ("requested_depth", "expected_depth"),
    [(1, 1), (15, 15), (18, 18), (19, 18), (40, 18)],
)
@pytest.mark.anyio
async def test_analyse_caps_search_depth_at_18(
    requested_depth: int, expected_depth: int
) -> None:
    fake = FakeEngine()

    await analyse(fake, chess.Board(), depth=requested_depth)

    assert fake.calls[0]["limit"].depth == expected_depth


@pytest.mark.anyio
async def test_analyse_defaults_to_depth_15_and_three_lines() -> None:
    fake = FakeEngine()

    await analyse(fake, chess.Board())

    assert fake.calls[0]["limit"].depth == 15
    assert fake.calls[0]["multipv"] == 3


@pytest.mark.anyio
async def test_analyse_passes_multipv_and_board_to_the_engine() -> None:
    fake = FakeEngine()
    board = chess.Board()

    await analyse(fake, board, multipv=5)

    assert fake.calls[0]["multipv"] == 5
    assert fake.calls[0]["board"] is board


@pytest.mark.parametrize(
    ("fen", "score", "expected_cp"),
    [
        (chess.STARTING_FEN, chess.engine.Cp(50), 50),
        (BLACK_TO_MOVE_FEN, chess.engine.Cp(50), -50),
        (chess.STARTING_FEN, chess.engine.Mate(1), 9999),
        (BLACK_TO_MOVE_FEN, chess.engine.Mate(1), -9999),
        (chess.STARTING_FEN, chess.engine.Mate(-2), -9998),
    ],
)
@pytest.mark.anyio
async def test_analyse_scores_from_the_side_to_move_view(
    fen: str, score: chess.engine.Score, expected_cp: int
) -> None:
    # The engine reports the score from White's view; analyse must flip it for Black.
    fake = FakeEngine([_info(score, chess.WHITE, ["e2e4"])])

    lines = await analyse(fake, chess.Board(fen))

    assert lines[0]["score_cp"] == expected_cp


@pytest.mark.anyio
async def test_analyse_returns_one_line_per_info_with_uci_pv() -> None:
    fake = FakeEngine(
        [
            _info(chess.engine.Cp(30), chess.WHITE, ["e2e4", "e7e5", "g1f3"]),
            _info(chess.engine.Cp(20), chess.WHITE, ["d2d4"]),
        ]
    )

    lines = await analyse(fake, chess.Board(), multipv=2)

    assert lines == [
        {"score_cp": 30, "pv": ["e2e4", "e7e5", "g1f3"]},
        {"score_cp": 20, "pv": ["d2d4"]},
    ]


@pytest.mark.anyio
async def test_analyse_returns_empty_pv_when_engine_omits_it() -> None:
    fake = FakeEngine([_info(chess.engine.Cp(0), chess.WHITE, None)])

    lines = await analyse(fake, chess.Board())

    assert lines == [{"score_cp": 0, "pv": []}]


@pytest.mark.anyio
async def test_analyse_returns_empty_list_when_engine_returns_no_lines() -> None:
    fake = FakeEngine([])

    lines = await analyse(fake, chess.Board())

    assert lines == []


@pytest.mark.anyio
async def test_concurrent_analyses_never_overlap_on_the_engine() -> None:
    fake = FakeEngine([_info(chess.engine.Cp(0), chess.WHITE, ["e2e4"])])

    await asyncio.gather(
        analyse(fake, chess.Board()),
        analyse(fake, chess.Board()),
        analyse(fake, chess.Board()),
    )

    assert len(fake.calls) == 3
    assert fake.max_active == 1


def test_module_constants_match_documented_limits() -> None:
    assert engine_module.MAX_DEPTH == 18
    assert engine_module.MATE_SCORE == 10000
