# Quality Rubric: backend-tester

Scores one run of the `backend-tester` agent (the tester), which writes new pytest tests and never changes production code or existing tests. It runs in two modes:

- **Orchestrator run.** Stage 3 (red) writes tests for the acceptance criteria in `spec.md` and proves them failing in `red-proof.md`. Stage 6 (green) re-runs them after each implementer build and writes `green-report-round-<N>.md`. Both stages are scored here; a green stage is scored per round.
- **Standalone coverage run.** A human names a backend module, and the agent adds tests to raise its coverage.

The agent's tools are `file_read`, `file_write`, `git_status` and `test_runner`. `test_runner` runs the fixed `uv run pytest` (no lint, no coverage flags; `npm run build` with `suite: "build"` for the frontend), so coverage percentages need a real session; in the pipeline they are reported as pending. Tests follow `.memory/knowledge/testing-standards.md`.

## 1.1 Test Coverage

Orchestrator run: measures whether every acceptance criterion in `spec.md` has a real test. Standalone run: measures whether the target module's coverage actually rose.

### Scoring Guide

1. Does not meet – Criteria have no test, or the tests don't exercise the behavior they are named for.

   - Level 1 example: `spec.md` lists 5 acceptance criteria; the new file has 3 tests, and `test_unknown_game_returns_404` only asserts `response is not None`. (Standalone: "added 4 tests for `game_store.py`", but the file only asserts `1 + 1 == 2`; coverage unchanged at 41%.)

2. Partially meets – Every criterion has a test, but error paths are thin: assertions are vague, or only the happy path is meaningfully checked.

   - Level 2 example: All 5 criteria have tests named after them, but the 404 and 409 tests check only the status code and not the key phrase of the string `detail`, which `spec.md` specifies. (Standalone: coverage 41% → 55%, with `append_move` and `pop_move` error paths untested.)

3. Meets – Every acceptance criterion has a test whose name matches the spec's test name, with explicit expected values and the status code plus the key error phrase on each error path. Mocks are at the boundaries `spec.md` names (LLM client, Stockfish).

   - Level 3 example: "5/5 criteria covered: `test_create_game_returns_201`, `test_unknown_game_returns_404`, `test_bad_fen_returns_400`, `test_fen_mismatch_returns_409`, `test_takeback_on_empty_history_returns_409`. Each error test asserts the status and the phrase from the spec." (Standalone: "`game_store.py` 41% → 89% (real session)", with the newly covered lines listed.)

4. Exceeds – Level 3 plus edge cases the spec implies but doesn't list, each traced to the criterion it protects, using `parametrize` instead of copy-paste.

   - Level 4 example: Level 3, plus a parametrized `test_bad_fen_returns_400` over empty, truncated and illegal-piece FENs, and a boundary test for takeback right after the first move, both traced to criteria 3 and 5.

## 1.2 Red and Green Evidence

Measures whether the red proof and green reports are real, complete and trustworthy as gate evidence.

### Scoring Guide

1. Does not meet – Results are claimed without quoted `test_runner` output, or the tests are red for the wrong reason.

   - Level 1 example: `red-proof.md` says "all 5 tests fail" with no output. Or: the output shows `NameError: name 'clinet' is not defined` in the test file, so the tests would stay red after any build.

2. Partially meets – Output is quoted, but evidence the gates rely on is missing.

   - Level 2 example: `red-proof.md` quotes the failures but not the test files' content, so G2 has nothing to compare against. Or: `green-report-round-2.md` says "test files unchanged" without a per-file comparison.

3. Meets – Both stages give complete gate evidence:
   - `red-proof.md`: verbatim `test_runner` output where each new test fails because the behavior is missing (an assertion or a missing route, not a typo, import error or fixture error in the test), plus the full content of each new test file.
   - Each `green-report-round-<N>.md`: verbatim output, green or still red, and for each test file "identical to red-proof.md" or the lines that differ, plus any unlisted new file under `backend/tests/`.
   - Pre-existing tests still pass.

   - Level 3 example: "`red-proof.md`: 5 failed (4 × `assert 404 == 201`, 1 × `assert 404 == 409`), 92 passed, 2 skipped; full copy of `tests/test_games_api_new.py`. `green-report-round-1.md`: 97 passed, 2 skipped; `tests/test_games_api_new.py` identical to red-proof.md; no unlisted test files."

4. Exceeds – Level 3 plus correct handling of environment limits.

   - Level 4 example: Level 3, plus: "Engine tests reported as *skipped*, not failed, per the testing standard. `STOCKFISH_PATH` was unset and I did not try to install or locate Stockfish. Coverage numbers marked pending: `test_runner` runs without `--cov`."

## 1.3 Scope Discipline

Measures whether the agent stayed inside its lane.

### Scoring Guide

1. Does not meet – Edited production code or an existing test, changed `red-proof.md` after G1, overwrote an earlier green report, or wrote docs outside its own files.

   - Level 1 example: The green stage "fixed" a still-red test by loosening its assertion and updating the copy in `red-proof.md` to match. (Equivalent breaches: editing `app/services/game_store.py` to make a test pass; overwriting `green-report-round-1.md` in round 2.)

2. Partially meets – Crossed a boundary during the run, then reverted it.

   - Level 2 example: Report admits "I briefly edited `app/services/moves.py` to see if a test would pass, then reverted it." The final diff is clean, but the boundary was crossed.

3. Meets – Relative to the run's baseline, only these changed: new files under `backend/tests/`, `red-proof.md`, `green-report-round-<N>.md` files, and its log.

   - Level 3 example: "Baseline from `git_status` at stage start. Diff from this run: `backend/tests/test_games_api_new.py` (new), `docs/orchestrator-runs/games-takeback-2026-11-20/red-proof.md`. Nothing else."

4. Exceeds – Level 3 plus the diff is provably attributable.

   - Level 4 example: Level 3, and the report includes the baseline `git status --short` snapshot, so every changed file maps to a named stage.

**Pass threshold:** A run passes if it scores 3 or higher on all three dimensions, and the gate is met:
- **Red stage:** G1 can pass on `red-proof.md` alone, with no production-code changes relative to the baseline.
- **Green stage:** the report gives G2 everything it needs (verbatim output and a per-file comparison), whatever the suite result. A still-red suite is the implementer's problem, not a tester failure.
- **Standalone run:** the full suite is green with no production-code changes.

**Notes on threshold design:** Each dimension has a floor because tests that look complete but are red for the wrong reason, or a green result reached by changing tests, would make the build *less* trustworthy, not more. Red for the wrong reason is a Level 1 because the red proof exists to show the tests detect the missing behavior; a test broken by its own typo proves nothing and stays red after any build. Editing `red-proof.md` after G1 is a Level 1 because G2 compares against it, so changing it hides exactly what G2 is meant to catch. The green stage is scored on evidence, not on the suite result, because the tester reports the build and doesn't own it. There is no separate spot-check: in an orchestrator run, the red proof already shows each test fails without the behavior. Standalone runs have no equivalent, so their tests are judged on coverage and assertion quality alone.
