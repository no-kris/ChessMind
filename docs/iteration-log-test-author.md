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
