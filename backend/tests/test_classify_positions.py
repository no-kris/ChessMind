"""Checks the agent-built positions in fixtures/positions.json.

Quick checks run every time. The Stockfish check (marked `engine`)
re-grades every position from scratch, so nothing the agent reported
is taken on trust.
"""

import json
from pathlib import Path

import chess
import pytest

from app.services.classify import bucket, eval_loss
from app.services.engine import analyse, open_engine

FIXTURES = Path(__file__).parent / "fixtures"
DEPTH = 15

# Safe target range for each label (inclusive). None means no upper limit.
SAFE_RANGES = {
    "good": (0, 10),
    "inaccuracy": (50, 79),
    "mistake": (120, 279),
    "blunder": (320, None),
}

REQUIRED_FIELDS = {"id", "fen", "move", "expected_bucket", "loss_cp"}

SCENARIOS = json.loads((FIXTURES / "scenarios.json").read_text())
SCENARIOS_BY_ID = {s["id"]: s for s in SCENARIOS}

_positions_file = FIXTURES / "positions.json"
POSITIONS = json.loads(_positions_file.read_text()) if _positions_file.exists() else []


def in_safe_range(loss: int, label: str) -> bool:
    low, high = SAFE_RANGES[label]
    return loss >= low and (high is None or loss <= high)


# ---------- Quick checks (no engine) ----------


def test_positions_match_scenarios():
    ids = [p["id"] for p in POSITIONS]
    assert len(ids) == len(set(ids)), "positions.json has duplicate ids"

    missing = [s for s in SCENARIOS_BY_ID if s not in ids]
    extra = [i for i in ids if i not in SCENARIOS_BY_ID]
    assert not missing, f"No verified position for: {missing}"
    assert not extra, f"Positions with no matching scenario: {extra}"


@pytest.mark.parametrize("pos", POSITIONS, ids=lambda p: p["id"])
def test_position_is_valid(pos):
    assert set(pos) == REQUIRED_FIELDS, f"Wrong fields: {sorted(pos)}"

    scenario = SCENARIOS_BY_ID.get(pos["id"])
    assert scenario, f"No scenario named {pos['id']}"
    assert pos["expected_bucket"] == scenario["expected_bucket"], "Label was changed"

    board = chess.Board(pos["fen"])
    assert board.is_valid(), "FEN is not a legal position"

    expected_turn = chess.WHITE if scenario["side_to_move"] == "white" else chess.BLACK
    assert board.turn == expected_turn, "Wrong side to move"

    assert chess.Move.from_uci(pos["move"]) in board.legal_moves, "Move is not legal"


# ---------- Stockfish check ----------


@pytest.mark.engine
@pytest.mark.anyio
@pytest.mark.parametrize("pos", POSITIONS, ids=lambda p: p["id"])
async def test_stockfish_confirms_label(pos):
    board = chess.Board(pos["fen"])
    move = chess.Move.from_uci(pos["move"])

    engine = await open_engine()
    try:
        before = await analyse(engine, board, depth=DEPTH, multipv=1)
        board.push(move)
        after = await analyse(engine, board, depth=DEPTH, multipv=1)
    finally:
        await engine.quit()

    loss = eval_loss(before[0]["score_cp"], after[0]["score_cp"])
    label = pos["expected_bucket"]

    assert bucket(loss) == label, f"Loss {loss} grades as '{bucket(loss)}', expected '{label}'"
    assert in_safe_range(loss, label), f"Loss {loss} is too close to a cutoff for '{label}'"
