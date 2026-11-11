# Quality Rubric: backend-test-author

Scores one run of the `backend-test-author` agent, which adds pytest tests for a named backend module without changing production code.

## 1.1 Coverage Impact

Measures whether measured coverage of the target module actually rose.

### Scoring Guide

1. Does not meet – No new tests, or tests don't exercise the target module.

   - Level 1 example: Report says "added 4 tests for `game_store.py`," but the new file only imports `GameStore` and asserts `1 + 1 == 2`. Coverage for `game_store.py` is unchanged at 41%.

2. Partially meets – Tests added, but only the happy path; coverage barely moves.

   - Level 2 example: `test_create_and_get_game` passes and coverage goes from 41% to 55%, but `append_move`, `pop_move`, and the mismatch error paths are still untested. Report claims "coverage improved."

3. Meets – Target goes from partial to covered; new tests fail if the module is broken.

   - Level 3 example: "Coverage for `game_store.py`: 41% → 89%. Spot-check: renaming the `PositionMismatchError` raise makes 3 of the new tests fail."

4. Exceeds – Level 3 plus edge cases and error paths covered, with before/after numbers.

   - Level 4 example: "41% → 93%. Added boundary tests for takeback on empty history, append after delete, and FEN canonicalization; each shown failing when the corresponding line is removed. Before/after coverage table in the report."

## 1.2 Suite Integrity

Measures whether the run left the test suite better off.

### Scoring Guide

1. Does not meet – Existing tests broke, or were edited to pass.

   - Level 1 example: `test_games_api.py` fails after the run; the agent deleted the failing assertion in `test_takeback_with_no_moves_returns_409` and reported "suite green."

2. Partially meets – Green only because a failing test was deleted or skipped.

   - Level 2 example: Full suite passes, but the report shows `6 passed, 1 deselected` — the previously passing `test_move_path_never_calls_the_engine` was deselected "to save time."

3. Meets – Full `uv run pytest` green, `ruff check .` clean, no existing test file edited.

   - Level 3 example: "Suite: 97 passed, 2 skipped (engine marker, `STOCKFISH_PATH` unset). `ruff check .`: no issues. Diff touches only `tests/test_game_store_new.py`; no existing test files modified."

4. Exceeds – Level 3 plus correct handling of the engine-marker rule.

   - Level 4 example: Level 3 report plus: "Engine tests reported as *skipped*, not failed, per the testing standard — `STOCKFISH_PATH` was unset during the run, and I did not attempt to install or locate Stockfish."

## 1.3 Scope Discipline

Measures whether the agent stayed inside its lane.

### Scoring Guide

1. Does not meet – Edited production code or docs outside its log.

   - Level 1 example: The run also "fixed" `game_store.append_move` to make a test pass; `git diff --stat` shows `app/services/game_store.py` modified.

2. Partially meets – Touched production code but reverted it.

   - Level 2 example: Report admits "I briefly edited `app/services/moves.py` to see if a test would pass, then reverted it." Final diff is clean, but the boundary was crossed during the run.

3. Meets – Only `backend/tests/**` + its iteration log changed relative to the run's baseline.

   - Level 3 example: "Baseline recorded at run start (working tree had 12 dirty files). Diff attributable to this run: `tests/test_game_store.py` (new) and `docs/iteration-log-test-author.md`. Nothing else."

4. Exceeds – Level 3 plus the diff is provably attributable.

   - Level 4 example: Level 3, and the log includes the baseline `git status --short` snapshot, so every changed line in the report maps to a named file.

**Pass threshold:** A run passes if it scores 3 or higher on all three dimensions, and the gate is met: the full suite is green with no production-code changes relative to the run's baseline.

**Notes on threshold design:** Each dimension has a floor because a high coverage number bought with scope violations (editing `app/`) or a weakened suite (deleting a failing test) would make the module *less* trustworthy, not more. The gate is stated separately so a run that scores well on the rubric but leaves a red suite still fails.
