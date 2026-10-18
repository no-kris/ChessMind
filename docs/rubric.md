# 1. Quality Rubric

## 1.1 Dimensions

### 1.1.1 Coverage Reporting Accuracy

This dimension measure whether the agent produces a report on the test coverage for the backend source files. A high score requires the stated coverage to match what the result of the test suite produced.

## Scoring Guide

1. Does not meet - The agent does not report coverage, or the report is misleading.

Level 1 example: Agent output reads: “The backend tests pass and coverage looks good.” No evidence is given, and no files are referenced.

2. Partially meets - The agent reports coverage but combines the per-module test coverage into one number. The agent does not state which files are unmeasured.

Level 2 example: Agent output reads: “Backend coverage is 85%.” The four backend files are collapsed into one number.

3. Meets – The agent reports coverage for each backend source file, or explicitly states which files are unmeasured.

Level 3 example: Agent output reads: “classify.py ~100%, routes.py ~100%, main.py ~85%, engine.py ~70%.

4. Exceeds – The agent reports per-file figures and separates what was measured from what could not be, including the reason.

Level 4 example: Agent output reads: “classify.py 100% line, routes.py 100%, main.py 85%; engine.py unmeasured — its tests require STOCKFISH_PATH but is unset.”

### 1.1.2 Weakest-Area Identification

This dimension measures whether the agent identifies the least-covered backend area for testing. A high score requires the named area to match the evidence and be supported by detail.

## Scoring Guide

1. Does not meet – The agent does not identify a weakest area, or names one contradicted by its own data.

Level 1 example: Agent output reads: “The weakest area is classify.py.” Its own report shows classify.py at ~100% and engine.py far lower.

2. Partially meets – The agent names a possible weakest area but gives no rationale or evidence.

Level 2 example: Agent output reads: “The weakest area is the engine service.” No reason is offered.

3. Meets – The agent correctly identifies the weakest area with a brief rationale.

Level 3 example: Agent output reads: “The weakest area is app/services/engine.py, which has the least coverage.”

4. Exceeds – The agent identifies the weakest area and explains why, citing the specific untested behavior.

Level 4 example: Agent output reads: “app/services/engine.py is weakest — it is covered only by @pytest.mark.engine integration tests that need a Stockfish binary, leaving the open_engine missing-env RuntimeError, the depth cap, and the asyncio.Lock untested.”

### 1.1.3 Blocker and Test-Status Reporting

This dimension measures whether the agent correctly classifies environment blockers such as collection/import errors, rather than misreporting them as test results.

## Scoring Guide

1. Does not meet – The agent reports a blocked or skipped test as a failure, or reports a collection error as if the suite ran.

Level 1 example: Agent output reads: “test_engine.py failed.” The tests were in fact skipped because STOCKFISH_PATH was unset.

2. Partially meets – The agent notices tests did not run but does not classify the reason.

Level 2 example: Agent output reads: “Some tests didn’t run.” It does not say whether they skipped, failed, or errored on import.

3. Meets – The agent correctly reports engine tests as skipped when STOCKFISH_PATH is unset, and reports a failed import or collection error as a blocker.

Level 3 example: Agent output reads: “test_engine.py was skipped: STOCKFISH_PATH is not set.”

4. Exceeds – The agent classifies blockers correctly and distinguishes environment blockers from genuine test failures.

Level 4 example: Agent output reads: “test_engine.py skipped (2 tests) — STOCKFISH_PATH unset; no tests failed. test_classify.py and test_api.py collected cleanly.”

## Pass Threshold

A run passes if it scores 3 or higher on every graded dimension (1.1.1–1.1.3).


Reasoning: All three dimensions must be right for the report to be trustworthy. A run that scores 4 on blocker detail but 2 on coverage accuracy produces a well-documented wrong answer. A dimension floor prevents strong performance on one from masking a failure on another.

## Notes on Threshold Design

Considered an aggregate minimum of 9/12 instead of a dimension floor. Ruled out because it would allow a run scoring 1 on Coverage Reporting Accuracy to pass if it scored 3–4 on the other two. An agent that reports coverage it never measured is not acceptable, regardless of how well it identifies the weakest area.
