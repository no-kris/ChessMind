# Red proof: coach-explain-2026-11-17 (stage 3)

Author: tester (backend test author). Spec: `spec.md` revision 1 (H1 passed; Q2-Q6 as stated).

## Baseline (before any test was written)

`git_status` at stage start (exit 0):

```
?? docs/orchestrator-runs/coach-explain-2026-11-17/
```

Baseline suite, `test_runner` path `backend` (`uv run pytest`), last line verbatim (ANSI colour codes removed):

```
======================== 123 passed, 1 warning in 5.15s ========================
RESULT: PASS (uv run pytest exit code 0)
```

`tests/test_engine.py` (2 tests, `@pytest.mark.engine`) ran and passed, so STOCKFISH_PATH is set in
this environment. None of the new tests needs it or carries the `engine`/`llm` mark.

`backend/app/main.py` is unchanged (human constraint for this run). No file under `backend/app/` was
written.

## New test files

| File | Cases | Spec section |
|---|---|---|
| `backend/tests/test_coach.py` | 77 | 5.1 (all 23 names) |
| `backend/tests/test_position_analysis.py` | 7 | 5.2 (all 6 names) |
| `backend/tests/test_coach_api.py` | 16 | 5.3 (all 14 names) |

## Red run

`test_runner` path `backend`, install false (`uv run pytest`), exit 1.

**Summary: 100 failed, 123 passed.** The 100 failures are exactly the 100 new cases. The 123
passes are the whole pre-existing suite, the same count as at baseline, so the new files do not
break it. There are no collection errors and no setup errors.

### Why each file is red

- `test_coach.py` (77 failed): each test fails at its first line, `_coach()` →
  `importlib.import_module("app.services.coach")` → `ModuleNotFoundError: No module named
  'app.services.coach'`. The production module does not exist yet. That is the reason spec
  section 7 expects.
- `test_position_analysis.py` (7 failed): each fails at `_position_analysis()` →
  `ModuleNotFoundError: No module named 'app.services.position_analysis'`. Same reason.
- `test_coach_api.py` (16 failed): fails on HTTP 404 / assertions, NOT on an import error.
  `main.py` is unwired and `app.api.coach` doesn't exist, so `POST /api/coach/explain` returns
  FastAPI's `404 Not Found`. Tests that expect 200/422/503 fail on `assert 404 == <code>`. Tests
  that expect a 404 pass the status check and then fail on the key phrase
  (`assert 'explain move failed' in 'Not Found'`, or `'no move with id'`). The autouse
  fixture tolerates only the missing `app.services.position_analysis` module (checked via
  `exc.name`), so it does not error at setup.
- No test is red for any other reason (no typo, no fixture error, no test-side NameError).

Design note: the production imports are made at call time, not at module level. A module-level
import of a missing module aborts the whole pytest session at collection ("Interrupted: 1 error
during collection"). That would hide both the API tests' 404 failures and the pre-existing
suite's result in this run. The red reason for the two service files is still the
ModuleNotFoundError the spec names.

### Verbatim pytest output

`test_runner` truncated the head of the output itself (it returns `...[truncated]...`). Everything
below is the returned text verbatim except that ANSI colour escape sequences (`ESC[...m`) were
removed for readability. No other characters were changed, added or removed.

```
== uv run pytest (exit 1) ==
...[truncated]...
:1333: ModuleNotFoundError
_______________ test_engine_unavailable_error_is_a_runtime_error _______________

    def test_engine_unavailable_error_is_a_runtime_error() -> None:
>       position_analysis = _position_analysis()
                            ^^^^^^^^^^^^^^^^^^^^

tests/test_position_analysis.py:150: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/test_position_analysis.py:22: in _position_analysis
    return importlib.import_module("app.services.position_analysis")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.13/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
<frozen importlib._bootstrap>:1404: in _gcd_import
    ???
<frozen importlib._bootstrap>:1369: in _find_and_load
    ???
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

name = 'app.services.position_analysis'
import_ = <function _gcd_import at 0x755228d0c4a0>

>   ???
E   ModuleNotFoundError: No module named 'app.services.position_analysis'

<frozen importlib._bootstrap>:1333: ModuleNotFoundError
=============================== warnings summary ===============================
../../opt/venv/lib/python3.13/site-packages/starlette/testclient.py:53
  /opt/venv/lib/python3.13/site-packages/starlette/testclient.py:53: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = Callable[[], AbstractContextManager[anyio.abc.BlockingPortal]]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/test_coach.py::test_verdict_names_bucket_and_centipawns_lost[good-0-Good — 0 CP lost.] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_verdict_names_bucket_and_centipawns_lost[inaccuracy-45-Inaccuracy — 45 CP lost.] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_verdict_names_bucket_and_centipawns_lost[mistake-150-Mistake — 150 CP lost.] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_verdict_names_bucket_and_centipawns_lost[blunder-420-Blunder — 420 CP lost.] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_praise_and_concern_follow_bucket_without_alerts[good-Solid, engine-approved choice-Nothing major] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_praise_and_concern_follow_bucket_without_alerts[inaccuracy-A reasonable idea-Slightly imprecise] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_praise_and_concern_follow_bucket_without_alerts[mistake-The idea is understandable-Gives away a clear edge] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_praise_and_concern_follow_bucket_without_alerts[blunder-Still time to fight back-Throws away the position] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_opponent_pin_alert_sets_praise[good] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_opponent_pin_alert_sets_praise[inaccuracy] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_opponent_pin_alert_sets_praise[mistake] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_opponent_pin_alert_sets_praise[blunder] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_own_pin_alert_sets_concern[good] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_own_pin_alert_sets_concern[inaccuracy] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_own_pin_alert_sets_concern[mistake] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_own_pin_alert_sets_concern[blunder] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_both_pin_alerts_set_praise_and_concern[good] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_both_pin_alerts_set_praise_and_concern[inaccuracy] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_both_pin_alerts_set_praise_and_concern[mistake] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_both_pin_alerts_set_praise_and_concern[blunder] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_tip_for_good_move_is_general_advice - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_tip_for_non_good_move_names_best_move_from_best_line[inaccuracy] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_tip_for_non_good_move_names_best_move_from_best_line[mistake] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_tip_for_non_good_move_names_best_move_from_best_line[blunder] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_tip_without_best_line_falls_back_to_general_check[inaccuracy] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_tip_without_best_line_falls_back_to_general_check[mistake] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_tip_without_best_line_falls_back_to_general_check[blunder] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[good-alerts0-g1f3 b8c6] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[good-alerts0-] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[good-alerts1-g1f3 b8c6] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[good-alerts1-] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[good-alerts2-g1f3 b8c6] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[good-alerts2-] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[good-alerts3-g1f3 b8c6] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[good-alerts3-] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[inaccuracy-alerts0-g1f3 b8c6] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[inaccuracy-alerts0-] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[inaccuracy-alerts1-g1f3 b8c6] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[inaccuracy-alerts1-] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[inaccuracy-alerts2-g1f3 b8c6] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[inaccuracy-alerts2-] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[inaccuracy-alerts3-g1f3 b8c6] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[inaccuracy-alerts3-] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[mistake-alerts0-g1f3 b8c6] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[mistake-alerts0-] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[mistake-alerts1-g1f3 b8c6] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[mistake-alerts1-] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[mistake-alerts2-g1f3 b8c6] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[mistake-alerts2-] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[mistake-alerts3-g1f3 b8c6] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[mistake-alerts3-] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[blunder-alerts0-g1f3 b8c6] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[blunder-alerts0-] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[blunder-alerts1-g1f3 b8c6] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[blunder-alerts1-] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[blunder-alerts2-g1f3 b8c6] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[blunder-alerts2-] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[blunder-alerts3-g1f3 b8c6] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_explanation_respects_plan_length_rules[blunder-alerts3-] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_select_move_returns_move_at_ply_index[0-e2e4] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_select_move_returns_move_at_ply_index[1-e7e5] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_select_move_out_of_range_raises_move_not_found[len_history] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_select_move_out_of_range_raises_move_not_found[len_history_plus_5] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_select_move_negative_id_raises_instead_of_wrapping[-1] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_select_move_negative_id_raises_instead_of_wrapping[-2] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_select_move_on_empty_game_raises_move_not_found - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_move_not_found_error_is_a_lookup_error - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_context_computes_delta_and_bucket_from_both_positions[asyncio] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_context_calls_analyser_with_fen_before_then_fen_after[asyncio] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_context_reports_opponent_pin_alert[asyncio] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_context_reports_own_pin_alert[asyncio] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_context_without_pins_has_no_alerts[asyncio] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_checkmating_move_scores_result_as_mate_without_second_engine_call[asyncio] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_stalemating_move_scores_result_as_zero_without_second_engine_call[asyncio] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_context_carries_move_fields_and_versions[asyncio] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_empty_analysis_raises_engine_unavailable[asyncio-before] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach.py::test_empty_analysis_raises_engine_unavailable[asyncio-after] - ModuleNotFoundError: No module named 'app.services.coach'
FAILED tests/test_coach_api.py::test_explain_returns_200_with_exactly_four_string_keys - assert 404 == 200
 +  where 404 = <Response [404 Not Found]>.status_code
FAILED tests/test_coach_api.py::test_explain_mistake_returns_templated_card - assert 404 == 200
 +  where 404 = <Response [404 Not Found]>.status_code
FAILED tests/test_coach_api.py::test_explain_reports_pin_on_opponent_in_praise - assert 404 == 200
 +  where 404 = <Response [404 Not Found]>.status_code
FAILED tests/test_coach_api.py::test_explain_reports_own_pinned_piece_in_concern - assert 404 == 200
 +  where 404 = <Response [404 Not Found]>.status_code
FAILED tests/test_coach_api.py::test_explain_uses_move_id_as_zero_based_ply_index - assert 404 == 200
 +  where 404 = <Response [404 Not Found]>.status_code
FAILED tests/test_coach_api.py::test_explain_unknown_game_returns_404 - AssertionError: assert 'explain move failed' in 'Not Found'
FAILED tests/test_coach_api.py::test_explain_move_id_out_of_range_returns_404[one_move_id_1] - AssertionError: assert 'explain move failed' in 'Not Found'
FAILED tests/test_coach_api.py::test_explain_move_id_out_of_range_returns_404[no_moves_id_0] - AssertionError: assert 'explain move failed' in 'Not Found'
FAILED tests/test_coach_api.py::test_explain_negative_move_id_returns_422_with_string_detail - assert 404 == 422
 +  where 404 = <Response [404 Not Found]>.status_code
FAILED tests/test_coach_api.py::test_explain_missing_field_returns_422_with_string_detail[game_id] - assert 404 == 422
 +  where 404 = <Response [404 Not Found]>.status_code
FAILED tests/test_coach_api.py::test_explain_missing_field_returns_422_with_string_detail[move_id] - assert 404 == 422
 +  where 404 = <Response [404 Not Found]>.status_code
FAILED tests/test_coach_api.py::test_explain_unknown_game_does_not_call_engine - AssertionError: assert 'explain move failed' in 'Not Found'
FAILED tests/test_coach_api.py::test_explain_out_of_range_move_does_not_call_engine - AssertionError: assert 'no move with id' in 'Not Found'
FAILED tests/test_coach_api.py::test_explain_engine_unavailable_returns_503 - assert 404 == 503
 +  where 404 = <Response [404 Not Found]>.status_code
FAILED tests/test_coach_api.py::test_explain_does_not_change_game_history - assert 404 == 200
 +  where 404 = <Response [404 Not Found]>.status_code
FAILED tests/test_coach_api.py::test_explain_after_takeback_explains_the_replacement_move - assert 404 == 200
 +  where 404 = <Response [404 Not Found]>.status_code
FAILED tests/test_position_analysis.py::test_analyse_position_without_stockfish_path_raises_engine_unavailable[asyncio] - ModuleNotFoundError: No module named 'app.services.position_analysis'
FAILED tests/test_position_analysis.py::test_analyse_position_wraps_os_error_as_engine_unavailable[asyncio] - ModuleNotFoundError: No module named 'app.services.position_analysis'
FAILED tests/test_position_analysis.py::test_analyse_position_returns_lines_and_quits_engine[asyncio] - ModuleNotFoundError: No module named 'app.services.position_analysis'
FAILED tests/test_position_analysis.py::test_analyse_position_quits_engine_when_analysis_fails[asyncio-engine_error] - ModuleNotFoundError: No module named 'app.services.position_analysis'
FAILED tests/test_position_analysis.py::test_analyse_position_quits_engine_when_analysis_fails[asyncio-engine_terminated_error] - ModuleNotFoundError: No module named 'app.services.position_analysis'
FAILED tests/test_position_analysis.py::test_get_position_analyser_returns_analyse_position - ModuleNotFoundError: No module named 'app.services.position_analysis'
FAILED tests/test_position_analysis.py::test_engine_unavailable_error_is_a_runtime_error - ModuleNotFoundError: No module named 'app.services.position_analysis'
================== 100 failed, 123 passed, 1 warning in 8.88s ==================
warning: `VIRTUAL_ENV=/root/.cache/uv/builds-v0/.tmpLEom9C` does not match the project environment path `/opt/venv` and will be ignored; use `--active` to target the active environment instead

RESULT: FAIL (uv run pytest exit code 1)
```

## Notes for the implementer and green stage

- `test_coach_api.py` installs the fake with `app.dependency_overrides[get_position_analyser] = lambda: fake`,
  not `= fake` as spec section 4 literally writes it. FastAPI calls the override to produce the dependency
  value. If the fake itself were the override, FastAPI would read its `fen` parameter as a query parameter.
- `test_analyse_position_wraps_os_error_as_engine_unavailable` raises a realistic
  `FileNotFoundError(2, "No such file or directory", "/opt/missing/stockfish")` and asserts that the path is
  not in the message (spec 2.1, "never includes the env var's value"). `str(exc)` of that error contains
  the path, so `{reason}` must not be `str(exc)` verbatim (for example, use the exception type name or `strerror`).
- The API tests go green only after the coordinator adds the two `main.py` lines (H1 Q1 answer (b)).
- Edge cases added beyond the spec's listed cases, traced to their criterion: the pin-alert template tests
  are parametrized over all 4 buckets (2.3 "concern unchanged from bucket default"); the non-good tip tests
  are parametrized over inaccuracy/mistake/blunder (2.3); the length-rule test adds best_line present/empty
  (2.3 shape rules); negative ids -1 and -2 (2.2 "must never wrap"); `EngineTerminatedError` alongside
  `EngineError` (2.1 wrapped failures); the OSError test checks `__cause__` (2.1 "raise ... from exc")
  and that the path does not leak; the happy path checks `multipv == 1` and that the FEN was passed through
  (2.1).

## File copies (reference for G2)

### `backend/tests/test_coach.py`

```python
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
```

### `backend/tests/test_position_analysis.py`

```python
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
```

### `backend/tests/test_coach_api.py`

```python
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
```
