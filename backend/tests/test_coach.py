"""Tests for app.services.coach: the templated coach card, move lookup and move-context building.

Spec: docs/orchestrator-runs/coach-explain-2026-11-17/spec.md, section 5.1. No HTTP and no
Stockfish: the analyser is a fake async callable that returns canned engine lines per FEN.

The production modules are imported at call time (see _coach). A module-level import of a
module that does not exist yet aborts the whole pytest session at collection, which would hide
every other test's result during the red stage. Importing inside each test makes each test
fail on its own with ModuleNotFoundError until the module is built.
"""

import importlib
from types import ModuleType

import pytest

from app.services.game_store import Game, GameStore
from app.services.moves import MoveResult, apply_move

START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
AFTER_E4 = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"

# Reachable positions from spec section 4 (UCI from the start position).
PIN_ON_OPPONENT = ["d2d4", "d7d5", "c2c4", "e7e6", "b1c3", "f8b4"]  # move 5: Black pins Nc3 to e1
PIN_ON_OWN = ["d2d4", "e7e6", "c2c4", "f8b4", "b1c3"]  # move 4: White blocks with Nc3, now pinned
FOOLS_MATE = ["f2f3", "e7e5", "g2g4", "d8h4"]  # move 3 is checkmate
STALEMATE_BEFORE = "k7/8/8/1Q6/8/8/8/K7 w - - 0 1"  # b5b6 stalemates Black

OWN = "own_piece_pinned"
OPPONENT = "opponent_piece_pinned"
ALERT_SETS = [(), (OWN,), (OPPONENT,), (OWN, OPPONENT)]

# Bucket -> (default praise, default concern), written out from the spec 2.3 table.
BUCKET_TEXT = {
    "good": ("Solid, engine-approved choice", "Nothing major"),
    "inaccuracy": ("A reasonable idea", "Slightly imprecise"),
    "mistake": ("The idea is understandable", "Gives away a clear edge"),
    "blunder": ("Still time to fight back", "Throws away the position"),
}
BUCKET_DELTA = {"good": 0, "inaccuracy": 45, "mistake": 150, "blunder": 420}
NON_GOOD_BUCKETS = ["inaccuracy", "mistake", "blunder"]


def _coach() -> ModuleType:
    """Import app.services.coach at call time so a missing module fails each test, not collection."""
    return importlib.import_module("app.services.coach")


def _engine_unavailable_error() -> type[Exception]:
    """Return EngineUnavailableError, imported at call time for the same reason as _coach."""
    return importlib.import_module("app.services.position_analysis").EngineUnavailableError


def _context(
    bucket: str,
    delta_cp: int | None = None,
    alerts: tuple[str, ...] = (),
    best_line: str = "g1f3 b8c6",
):
    """Build a MoveContext for the template tests; delta defaults to a value inside the bucket."""
    return _coach().MoveContext(
        fen=START,
        move="e2e4",
        san="e4",
        delta_cp=BUCKET_DELTA[bucket] if delta_cp is None else delta_cp,
        bucket=bucket,
        tactical_alerts=alerts,
        best_line=best_line,
    )


def _played(ucis: list[str], start: str = START) -> list[MoveResult]:
    """Apply UCI moves one after another from `start` and return every MoveResult."""
    results: list[MoveResult] = []
    fen = start
    for uci in ucis:
        result = apply_move(fen, uci)
        results.append(result)
        fen = result.fen_after
    return results


def _game_with(ucis: list[str]) -> Game:
    """Create a game in a fresh store (not the process-wide one) and record these moves."""
    store = GameStore()
    game = store.create()
    for result in _played(ucis):
        store.append_move(game.game_id, result)
    return game


def _lines(score_cp: int, pv: list[str] | None = None) -> list[dict]:
    """One engine.analyse-shaped line: a side-to-move score and a UCI pv."""
    return [{"score_cp": score_cp, "pv": list(pv or [])}]


class FakeAnalyser:
    """Async stand-in for the position analyser: canned lines per FEN, and a log of every call."""

    def __init__(self, lines_by_fen: dict[str, list[dict]]) -> None:
        """Store the canned lines and start with an empty call log."""
        self.lines_by_fen = lines_by_fen
        self.calls: list[str] = []

    async def __call__(self, fen: str) -> list[dict]:
        """Record the FEN and return its lines; fail loudly for a FEN the test did not expect."""
        self.calls.append(fen)
        if fen not in self.lines_by_fen:
            raise AssertionError(f"analyser called with unexpected FEN {fen!r}")
        return self.lines_by_fen[fen]


# --- Templates -------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("bucket", "delta_cp", "expected"),
    [
        ("good", 0, "Good — 0 CP lost."),
        ("inaccuracy", 45, "Inaccuracy — 45 CP lost."),
        ("mistake", 150, "Mistake — 150 CP lost."),
        ("blunder", 420, "Blunder — 420 CP lost."),
    ],
)
def test_verdict_names_bucket_and_centipawns_lost(bucket: str, delta_cp: int, expected: str) -> None:
    coach = _coach()

    explanation = coach.build_fallback_explanation(_context(bucket, delta_cp))

    assert explanation.verdict == expected


@pytest.mark.parametrize(("bucket", "praise", "concern"), [(b, p, c) for b, (p, c) in BUCKET_TEXT.items()])
def test_praise_and_concern_follow_bucket_without_alerts(bucket: str, praise: str, concern: str) -> None:
    coach = _coach()

    explanation = coach.build_fallback_explanation(_context(bucket))

    assert explanation.praise == praise
    assert explanation.concern == concern


@pytest.mark.parametrize("bucket", list(BUCKET_TEXT))
def test_opponent_pin_alert_sets_praise(bucket: str) -> None:
    coach = _coach()

    explanation = coach.build_fallback_explanation(_context(bucket, alerts=(OPPONENT,)))

    assert explanation.praise == "Pins an enemy piece"
    assert explanation.concern == BUCKET_TEXT[bucket][1]


@pytest.mark.parametrize("bucket", list(BUCKET_TEXT))
def test_own_pin_alert_sets_concern(bucket: str) -> None:
    coach = _coach()

    explanation = coach.build_fallback_explanation(_context(bucket, alerts=(OWN,)))

    assert explanation.concern == "Leaves your piece pinned"
    assert explanation.praise == BUCKET_TEXT[bucket][0]


@pytest.mark.parametrize("bucket", list(BUCKET_TEXT))
def test_both_pin_alerts_set_praise_and_concern(bucket: str) -> None:
    coach = _coach()

    explanation = coach.build_fallback_explanation(_context(bucket, alerts=(OWN, OPPONENT)))

    assert explanation.praise == "Pins an enemy piece"
    assert explanation.concern == "Leaves your piece pinned"


def test_tip_for_good_move_is_general_advice() -> None:
    coach = _coach()

    explanation = coach.build_fallback_explanation(_context("good", best_line="e2e4 e7e5"))

    assert explanation.tip == "Keep checking captures, checks and threats."


@pytest.mark.parametrize("bucket", NON_GOOD_BUCKETS)
def test_tip_for_non_good_move_names_best_move_from_best_line(bucket: str) -> None:
    coach = _coach()

    explanation = coach.build_fallback_explanation(_context(bucket, best_line="e2e4 e7e5"))

    assert explanation.tip == "Consider e2e4 instead."


@pytest.mark.parametrize("bucket", NON_GOOD_BUCKETS)
def test_tip_without_best_line_falls_back_to_general_check(bucket: str) -> None:
    coach = _coach()

    explanation = coach.build_fallback_explanation(_context(bucket, best_line=""))

    assert explanation.tip == "Check every capture and threat before moving."


def _assert_one_sentence(text: str) -> None:
    """Plan line 81: one short sentence ending in '.', with exactly one terminator."""
    assert text.endswith(".")
    assert sum(text.count(mark) for mark in ".!?") == 1


def _assert_short_phrase(text: str) -> None:
    """Plan line 81: at most a phrase, so no sentence terminator and at most 6 words."""
    assert not any(mark in text for mark in ".!?")
    assert len(text.split()) <= 6


@pytest.mark.parametrize("best_line", ["g1f3 b8c6", ""])
@pytest.mark.parametrize("alerts", ALERT_SETS)
@pytest.mark.parametrize("bucket", list(BUCKET_TEXT))
def test_explanation_respects_plan_length_rules(bucket: str, alerts: tuple[str, ...], best_line: str) -> None:
    coach = _coach()

    explanation = coach.build_fallback_explanation(_context(bucket, alerts=alerts, best_line=best_line))

    _assert_one_sentence(explanation.verdict)
    _assert_one_sentence(explanation.tip)
    _assert_short_phrase(explanation.praise)
    _assert_short_phrase(explanation.concern)
    for text in (explanation.verdict, explanation.praise, explanation.concern, explanation.tip):
        assert text
        assert "\n" not in text
        assert "\r" not in text


# --- Move lookup -----------------------------------------------------------------------------


@pytest.mark.parametrize(("move_id", "expected_uci"), [(0, "e2e4"), (1, "e7e5")])
def test_select_move_returns_move_at_ply_index(move_id: int, expected_uci: str) -> None:
    coach = _coach()
    game = _game_with(["e2e4", "e7e5"])

    move = coach.select_move(game, move_id)

    assert move.move == expected_uci
    assert move == game.history[move_id]


@pytest.mark.parametrize("move_id", [2, 7], ids=["len_history", "len_history_plus_5"])
def test_select_move_out_of_range_raises_move_not_found(move_id: int) -> None:
    coach = _coach()
    game = _game_with(["e2e4", "e7e5"])

    with pytest.raises(coach.MoveNotFoundError) as excinfo:
        coach.select_move(game, move_id)

    message = excinfo.value.args[0]
    assert "no move with id" in message
    assert "expected" in message


@pytest.mark.parametrize("move_id", [-1, -2])
def test_select_move_negative_id_raises_instead_of_wrapping(move_id: int) -> None:
    coach = _coach()
    game = _game_with(["e2e4", "e7e5"])

    with pytest.raises(coach.MoveNotFoundError):
        coach.select_move(game, move_id)


def test_select_move_on_empty_game_raises_move_not_found() -> None:
    coach = _coach()
    game = _game_with([])

    with pytest.raises(coach.MoveNotFoundError) as excinfo:
        coach.select_move(game, 0)

    message = excinfo.value.args[0]
    assert "no move with id" in message
    assert "at least one recorded move" in message


def test_move_not_found_error_is_a_lookup_error() -> None:
    coach = _coach()

    assert issubclass(coach.MoveNotFoundError, LookupError)


# --- Context building ------------------------------------------------------------------------


@pytest.mark.anyio
async def test_context_computes_delta_and_bucket_from_both_positions() -> None:
    coach = _coach()
    move = apply_move(START, "e2e4")
    analyser = FakeAnalyser({START: _lines(50, ["g1f3", "b8c6"]), AFTER_E4: _lines(100)})

    context = await coach.build_move_context(move, analyser)

    assert context.delta_cp == 150
    assert context.bucket == "mistake"
    assert context.best_line == "g1f3 b8c6"


@pytest.mark.anyio
async def test_context_calls_analyser_with_fen_before_then_fen_after() -> None:
    coach = _coach()
    move = apply_move(START, "e2e4")
    analyser = FakeAnalyser({START: _lines(20, ["e2e4"]), AFTER_E4: _lines(-20, ["e7e5"])})

    await coach.build_move_context(move, analyser)

    assert analyser.calls == [START, AFTER_E4]


@pytest.mark.anyio
async def test_context_reports_opponent_pin_alert() -> None:
    coach = _coach()
    move = _played(PIN_ON_OPPONENT)[5]
    analyser = FakeAnalyser({move.fen_before: _lines(0, ["f8b4"]), move.fen_after: _lines(0)})

    context = await coach.build_move_context(move, analyser)

    assert context.tactical_alerts == ("opponent_piece_pinned",)


@pytest.mark.anyio
async def test_context_reports_own_pin_alert() -> None:
    coach = _coach()
    move = _played(PIN_ON_OWN)[4]
    analyser = FakeAnalyser({move.fen_before: _lines(0, ["b1c3"]), move.fen_after: _lines(0)})

    context = await coach.build_move_context(move, analyser)

    assert context.tactical_alerts == ("own_piece_pinned",)


@pytest.mark.anyio
async def test_context_without_pins_has_no_alerts() -> None:
    coach = _coach()
    move = apply_move(START, "e2e4")
    analyser = FakeAnalyser({START: _lines(20, ["e2e4"]), AFTER_E4: _lines(-20)})

    context = await coach.build_move_context(move, analyser)

    assert context.tactical_alerts == ()


@pytest.mark.anyio
async def test_checkmating_move_scores_result_as_mate_without_second_engine_call() -> None:
    coach = _coach()
    move = _played(FOOLS_MATE)[3]
    analyser = FakeAnalyser({move.fen_before: _lines(9999, ["d8h4"])})

    context = await coach.build_move_context(move, analyser)

    assert analyser.calls == [move.fen_before]
    assert context.delta_cp == 0
    assert context.bucket == "good"


@pytest.mark.anyio
async def test_stalemating_move_scores_result_as_zero_without_second_engine_call() -> None:
    coach = _coach()
    move = apply_move(STALEMATE_BEFORE, "b5b6")
    analyser = FakeAnalyser({move.fen_before: _lines(0, ["b5b6"])})

    context = await coach.build_move_context(move, analyser)

    assert analyser.calls == [move.fen_before]
    assert context.delta_cp == 0
    assert context.bucket == "good"


@pytest.mark.anyio
async def test_context_carries_move_fields_and_versions() -> None:
    coach = _coach()
    move = apply_move(START, "e2e4")
    analyser = FakeAnalyser({START: _lines(20, ["e2e4"]), AFTER_E4: _lines(-20)})

    context = await coach.build_move_context(move, analyser)

    assert context.fen == START
    assert context.move == "e2e4"
    assert context.san == "e4"
    assert context.prompt_version == 1
    assert context.schema_version == 1


@pytest.mark.parametrize("empty_side", ["before", "after"])
@pytest.mark.anyio
async def test_empty_analysis_raises_engine_unavailable(empty_side: str) -> None:
    coach = _coach()
    engine_unavailable_error = _engine_unavailable_error()
    move = apply_move(START, "e2e4")
    analyser = FakeAnalyser(
        {
            START: [] if empty_side == "before" else _lines(20, ["e2e4"]),
            AFTER_E4: [] if empty_side == "after" else _lines(-20),
        }
    )

    with pytest.raises(engine_unavailable_error) as excinfo:
        await coach.build_move_context(move, analyser)

    assert "no analysis" in str(excinfo.value)
