**Workflow:** 
- From the repo root, the agent reads README.md to confirm the documented lint command, runs uv run ruff check in backend/, captures the output, and reports pass/fail plus every finding. It may recommend potential fixes but it does not run --fix, edit files, install anything, or change the repo.

**Trigger:**
- A developer gives a task prompt from the repository root to run the lint command in the backend.

**Branches:**
- If lint passes, report a clean result. If lint fails, list each finding (file:line: rule) and recommend no fixes be applied by the agent. If ruff is missing or errors on run, report the blocker and stop.

**Execution steps:**
1. Read the repository’s README.md to identify the documented lint command for the backend.

2. Run the lint command from backend/ and capture its output.

3. Collect the result or report the blocker if missing a dependency.

4. Evaluate the results and produce a final report with the results of running the lint command in the backend.

**Acceptance criteria:**
- Correctly reports whether ruff passed or failed (matches exit status).
- Reports every finding with file, line, and rule code; no omissions.
- Does not run --fix, edit files, or install anything.
- git status is unchanged after the run.
