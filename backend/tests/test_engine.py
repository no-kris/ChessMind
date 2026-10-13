import chess
import pytest

from app.services.engine import analyse, open_engine

# White to move: Qxf7# (Scholar's mate).
MATE_IN_ONE_FEN = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5Q2/PPPP1PPP/RNB1K1NR w KQkq - 4 4"


@pytest.mark.engine
@pytest.mark.anyio
async def test_starting_position_returns_three_balanced_lines():
    engine = await open_engine()
    try:
        lines = await analyse(engine, chess.Board())
    finally:
        await engine.quit()

    assert len(lines) == 3
    for line in lines:
        assert -100 <= line["score_cp"] <= 100
        assert len(line["pv"]) >= 1


@pytest.mark.engine
@pytest.mark.anyio
async def test_mate_in_one_scores_as_mate():
    board = chess.Board(MATE_IN_ONE_FEN)
    assert board.is_valid()
    mating_move = chess.Move.from_uci("f3f7")
    assert mating_move in board.legal_moves
    board.push(mating_move)
    assert board.is_checkmate()
    board.pop()

    engine = await open_engine()
    try:
        lines = await analyse(engine, board)
    finally:
        await engine.quit()

    assert lines[0]["score_cp"] >= 9000
    assert lines[0]["pv"][0] == "f3f7"
