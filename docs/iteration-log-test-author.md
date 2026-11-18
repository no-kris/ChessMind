# Iteration Log: backend-test-author

## Run 2026-11-11: app/services/engine.py

**Baseline** (branch `docs/memory-audit-run-001`, HEAD `7f9d135`)

`git status --short` at run start: empty (clean working tree).

STOCKFISH_PATH was set (`/usr/games/stockfish`). Baseline suite: 76 passed, 0 skipped, 0 failed.

Baseline coverage (`uv run pytest --cov=app --cov-report=term-missing`):

| Module | Stmts | Miss | Cover |
|---|---|---|---|
| app/api/games.py | 70 | 0 | 100% |
| app/api/routes.py | 5 | 0 | 100% |
| app/main.py | 34 | 0 | 100% |
| app/services/classify.py | 10 | 0 | 100% |
| app/services/engine.py | 18 | 1 | 94% (line 17) |
| app/services/game_store.py | 57 | 0 | 100% |
| app/services/moves.py | 32 | 0 | 100% |
| TOTAL | 226 | 1 | 99% |

**Target:** `app/services/engine.py`. It is the only module below 100%. Before this run, its only tests were the two `@pytest.mark.engine` integration tests. The missing-path error (line 17), the depth cap, the side-to-move score flip and the analysis lock had no direct test.

**Added:** `backend/tests/test_engine_unit.py` (20 test cases, no engine marker). They mock the boundary (`chess.engine.popen_uci` and a fake engine object), so they run without Stockfish.

**After:** 96 passed, 0 skipped. `ruff check .`: all checks passed. Coverage: engine.py 94% -> 100%, total 99% -> 100%.

**Spot-check:** a pytest plugin in the session scratchpad (outside the repo) replaced functions in `app.services.engine` in memory only. `app/` was never edited.

| Mutant | Failing new tests |
|---|---|
| `open_engine` without the STOCKFISH_PATH guard | 2 |
| `analyse` without `min(depth, MAX_DEPTH)` | 2 |
| `analyse` scoring from White's view instead of side to move | 2 |
| `analyse` without `_analysis_lock` | 1 |

**Findings (not fixed; reported):**
- `tests/test_engine.py`: the `@pytest.mark.engine` tests are not skipped when STOCKFISH_PATH is unset. Nothing in conftest or pyproject skips them, so they would fail with RuntimeError. This conflicts with the testing standard "Tests must pass without optional env vars unless they carry one of those marks" only if marked tests are expected to auto-skip. Proposed: a conftest hook that skips `engine` tests when STOCKFISH_PATH is unset. Left to a human because it changes an existing test file.
- `app/services/engine.py` has no module docstring and no logger. Its `RuntimeError` message names the variable but not what was expected. Coding standards ask for that. This was not changed because the file is production code.
- The new file is `test_engine_unit.py`, not an edit to `test_engine.py`. This breaks the "one test file per module" standard because existing test files may not be edited.

**Final `git status --short`:** 
- ?? backend/tests/test_engine_unit.py
- ?? docs/iteration-log-test-author.md

## Run 2026-11-17: orchestrator red stage, pin-detection-2026-11-17

**Baseline** (branch `main`, HEAD `c760f59`). `git status --short` at stage start (exit 0):

```
 M backend/app/main.py
?? docs/orchestrator-runs/
```

`main.py` change is pre-existing and human-owned (line endings); not touched. Baseline suite (`uv run pytest` via test_runner): 96 passed, exit 0. The two `test_engine.py` tests ran and passed (not skipped).

**Added:** `backend/tests/test_tactics.py`. It has 11 test functions and 27 cases, covering spec v3 sections 5.1 to 5.8 with the spec's names, ids and expected values. The 5.7 test name was kept as accepted at H1 #3.

**Red run:** exit 2, `ModuleNotFoundError: No module named 'app.services.tactics'` at collection, "Interrupted: 1 error during collection". This is the reason spec section 7 expects. Evidence and the full file copy are in `docs/orchestrator-runs/pin-detection-2026-11-17/red-proof.md`.

**Observation (not changed):** a module-level import error interrupts the whole pytest session. So the red run collects the other 96 tests but does not run them, and their status rests on the baseline run. The rubric's "not an import error" wording targets test-side typos. Here the spec names a missing production module as the expected red reason.

**Files written:** `backend/tests/test_tactics.py` (new), `docs/orchestrator-runs/pin-detection-2026-11-17/red-proof.md` (new), this log entry. No refused tool calls.

## Run 2026-11-17/18: orchestrator red stage, coach-explain-2026-11-17

**Baseline** (branch `feat/pin-detection`, HEAD `8fb58d1`). `git status --short` at stage start (exit 0):

```
?? docs/orchestrator-runs/coach-explain-2026-11-17/
```

Baseline suite (test_runner, `uv run pytest`): 123 passed, exit 0. The two `test_engine.py` tests ran and passed, so STOCKFISH_PATH is set. `backend/app/main.py` was left unchanged, per the human's constraint.

**Added:** `backend/tests/test_coach.py` (77 cases), `backend/tests/test_position_analysis.py` (7), `backend/tests/test_coach_api.py` (16). They cover every test name in spec sections 5.1 to 5.3. None needs Stockfish, and none carries the engine or llm mark.

**Design choice:** the new production modules are imported at call time (`importlib.import_module`), not at module level. The previous run showed that one module-level ModuleNotFoundError interrupts the whole session. That would hide the API tests' 404 failures and the existing suite's result. With lazy imports, the red run collects and runs everything. The `test_coach_api.py` autouse fixture installs the dependency override only once `app.services.position_analysis` exists, and it tolerates only that exact missing module.

**Red run:** exit 1, 100 failed, 123 passed. The service tests fail with `ModuleNotFoundError` for `app.services.coach` and `app.services.position_analysis`. The API tests fail on `assert 404 == ...` or on `'explain move failed' in 'Not Found'`. Evidence and full file copies are in `docs/orchestrator-runs/coach-explain-2026-11-17/red-proof.md`.

**Spec deviations reported (not hidden):**
- Spec section 4 writes the override as `= fake`. The tests use `= lambda: fake` because FastAPI calls the override to get the value.
- The OSError test uses a realistic FileNotFoundError that carries the path. It asserts that the path is absent from the message (spec 2.1), so the implementer cannot use `str(exc)` as `{reason}`.

**Files written:** the three test files above (new), `red-proof.md` (new), this log entry. No refused tool calls.
