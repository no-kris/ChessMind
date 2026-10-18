This workflow reviews the repositories backend test suite by running the documented test command, collecting per-module test coverage, and reporting the current coverage estimate and the weakest area.

Trigger: A developer invokes an AI agent by giving a task prompt from the repository root.

If the backend test suite runs successfully, the agent reports the measured test coverage for each backend source file and identifies the weakest area of coverage. If the output reports a failed import, or the testing tool is missing, or a required dependency such as STOCKFISH_PATH is missing, the agent reports the blocker and does NOT attempt to fix it.

1. Read the repository’s documentation (README.md) to identify the documented test command and available coverage tooling.

2. Run the backend suite from backend/ and capture its output.

3. Collect the coverage result for each backend source file.

4. Evaluate the results and classify each file as covered, partial, or uncovered.

5. Identify the weakest area — the file with the least coverage or no covering tests.

6. Produce a final report with the current coverage estimate, the weakest area, and a brief rationale.

The agent provides a report for the measured test coverage.

The agent correctly reports any failed module imports and does not attempt to fix it.

The agent records engine tests as skipped, not failed, when STOCKFISH_PATH is unset.

The agent does not attempt to fix any errors or add tests.

The agent did not commit, push, or change the repository.

Out of scope: frontend coverage is not measured by this standard; a separate standard will be added once a frontend test suite exists.
