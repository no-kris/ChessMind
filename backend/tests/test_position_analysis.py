"""Tests for app.services.position_analysis, the production engine boundary, with no Stockfish binary.

Spec: docs/orchestrator-runs/coach-explain-2026-11-17/spec.md, section 5.2. Mocks
chess.engine.popen_uci and STOCKFISH_PATH the same way test_engine_unit.py does.

The module under test is imported at call time (see _position_analysis) so that, while it does
not exist yet, each test fails on its own instead of aborting the pytest session at collection.
"""

import importlib
from types import ModuleType

import chess
import chess.engine
import pytest

FAKE_PATH = "/opt/missing/stockfish"


def _position_analysis() -> ModuleType:
    """Import app.services.position_analysis at call time so a missing module fails each test."""
    return importlib.import_module("app.services.position_analysis")


class FakeEngine:
    """Stand-in for a UCI engine: canned infos or a canned error, and counts of its calls."""

    def __init__(self, infos: list[dict] | None = None, error: Exception | None = None) -> None:
        """Store what analyse returns or raises, and start with empty call logs."""
        self.infos = infos if infos is not None else []
        self.error = error
        self.analyse_calls: list[dict] = []
        self.quit_calls = 0

    async def analyse(self, board: chess.Board, limit: chess.engine.Limit, multipv: int = 1) -> list[dict]:
        """Record the request, then raise the canned error or return the canned infos."""
        self.analyse_calls.append({"board": board, "limit": limit, "multipv": multipv})
        if self.error is not None:
            raise self.error
        return self.infos

    async def quit(self) -> None:
        """Count how many times the engine was shut down."""
        self.quit_calls += 1


def _install_fake_engine(monkeypatch: pytest.MonkeyPatch, engine: FakeEngine) -> list[str]:
    """Point STOCKFISH_PATH at a fake path and make popen_uci return `engine`; return started paths."""
    monkeypatch.setenv("STOCKFISH_PATH", FAKE_PATH)
    started: list[str] = []

    async def _fake_popen_uci(path: str) -> tuple[object, FakeEngine]:
        started.append(path)
        return object(), engine

    monkeypatch.setattr(chess.engine, "popen_uci", _fake_popen_uci)
    return started


@pytest.mark.anyio
async def test_analyse_position_without_stockfish_path_raises_engine_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    position_analysis = _position_analysis()
    monkeypatch.delenv("STOCKFISH_PATH", raising=False)
    started: list[str] = []

    async def _recording_popen_uci(path: str) -> None:
        started.append(path)
        raise AssertionError("popen_uci must not be called without STOCKFISH_PATH")

    monkeypatch.setattr(chess.engine, "popen_uci", _recording_popen_uci)

    with pytest.raises(position_analysis.EngineUnavailableError) as excinfo:
        await position_analysis.analyse_position(chess.STARTING_FEN)

    assert "engine unavailable" in str(excinfo.value)
    assert started == []


@pytest.mark.anyio
async def test_analyse_position_wraps_os_error_as_engine_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    position_analysis = _position_analysis()
    monkeypatch.setenv("STOCKFISH_PATH", FAKE_PATH)
    missing = FileNotFoundError(2, "No such file or directory", FAKE_PATH)

    async def _missing_binary(path: str) -> None:
        raise missing

    monkeypatch.setattr(chess.engine, "popen_uci", _missing_binary)

    with pytest.raises(position_analysis.EngineUnavailableError) as excinfo:
        await position_analysis.analyse_position(chess.STARTING_FEN)

    message = str(excinfo.value)
    assert "engine unavailable" in message
    assert FAKE_PATH not in message  # spec 2.1: the message never includes the env var's value
    assert excinfo.value.__cause__ is missing


@pytest.mark.anyio
async def test_analyse_position_returns_lines_and_quits_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    position_analysis = _position_analysis()
    engine = FakeEngine(
        [
            {
                "score": chess.engine.PovScore(chess.engine.Cp(35), chess.WHITE),
                "pv": [chess.Move.from_uci("e2e4"), chess.Move.from_uci("e7e5")],
            }
        ]
    )
    started = _install_fake_engine(monkeypatch, engine)

    lines = await position_analysis.analyse_position(chess.STARTING_FEN)

    assert lines == [{"score_cp": 35, "pv": ["e2e4", "e7e5"]}]
    assert started == [FAKE_PATH]
    assert engine.analyse_calls[0]["board"].fen() == chess.STARTING_FEN
    assert engine.analyse_calls[0]["multipv"] == 1
    assert engine.quit_calls == 1


@pytest.mark.parametrize(
    "error",
    [chess.engine.EngineError("engine crashed"), chess.engine.EngineTerminatedError("engine died")],
    ids=["engine_error", "engine_terminated_error"],
)
@pytest.mark.anyio
async def test_analyse_position_quits_engine_when_analysis_fails(
    monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    position_analysis = _position_analysis()
    engine = FakeEngine(error=error)
    _install_fake_engine(monkeypatch, engine)

    with pytest.raises(position_analysis.EngineUnavailableError) as excinfo:
        await position_analysis.analyse_position(chess.STARTING_FEN)

    assert "engine unavailable" in str(excinfo.value)
    assert engine.quit_calls == 1


def test_get_position_analyser_returns_analyse_position() -> None:
    position_analysis = _position_analysis()

    assert position_analysis.get_position_analyser() is position_analysis.analyse_position


def test_engine_unavailable_error_is_a_runtime_error() -> None:
    position_analysis = _position_analysis()

    assert issubclass(position_analysis.EngineUnavailableError, RuntimeError)
