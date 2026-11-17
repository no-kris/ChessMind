# Quality Rubric: endpoint-builder

Scores one run of the `endpoint-builder` agent (the implementer). In an orchestrator run it starts after the red-proof gate (G1) and makes the smallest production change that turns the tests in `red-proof.md` green. It is a builder, not an auditor and not a tester: existing endpoints are out of scope for edits, tests belong to the `backend-tester` agent, and the agent has no shell or test runner.

Its log is `docs/orchestrator-runs/<run-id>/implementer-log.md`, overwritten on every build. A standalone build with no run-id uses `docs/iteration-log-endpoint-builder.md` instead. Where a standalone build is scored differently, the dimension says so.

Evidence comes from the run directory: `red-proof.md`, `green-report-round-<N>.md` for the build being scored, `review.md`, and the implementer's log. The agent's own claims about test results don't count as evidence.

## 1.1 Feature Correctness

Measures whether the build makes the red tests pass and matches `spec.md` and the plan's contract (request/response shape, status codes, error behavior), as shown by the tester's green report and the reviewer's verdict.

### Scoring Guide

1. Does not meet – The contract contradicts the spec or plan, most red tests are still red, or the log claims test results the agent couldn't have run.

   - Level 1 example: `POST /api/coach/explain` returns free-form prose instead of the schema-constrained JSON object `{verdict, praise, concern, tip}` mandated by plan line 73; `green-report-round-1.md` shows 4 of 5 red tests still failing. The log says "all tests pass".

2. Partially meets – The success path works, but a red test is still red, or the reviewer rejects because a spec error path is wrong.

   - Level 2 example: `green-report-round-1.md` is green except `test_unknown_game_returns_404_string_detail`, which gets a 500. Or: all tests are green, but `review.md` rejects because the 409 `detail` is a dict, not the string `spec.md` requires.

3. Meets – Every test in `red-proof.md` passes in the green report for this build, with the test files identical to their copies in `red-proof.md`. The reviewer finds no violation in this build, and each contract decision in the log names its `spec.md` criterion and plan line.

   - Level 3 example: "`green-report-round-2.md`: 7/7 red-proof tests pass, test files identical. `review.md`: pass. Log traces 404 unknown game, 422 malformed body and 200 fallback on LLM failure to spec criteria 2–4 and plan lines 57 and 83."

4. Exceeds – Level 3 on the first build: no still-red green run and no reviewer reject used a round.

   - Level 4 example: Level 3, reached in round 1. The run's `log.md` shows one implementer build, G2 pass and review pass.

Standalone build (no red tests exist): score on whether the code matches the plan section, judged by a reviewer reading the code against the log's contract. Mark results pending until the backend-tester's tests run.

## 1.2 Scope Discipline

Measures whether the agent stayed a builder and touched only new production files and its own log.

### Scoring Guide

1. Does not meet – Modified an existing `app/` file, wrote or edited any test file, edited `red-proof.md` or a green report, or wrote to the run's `log.md`.

   - Level 1 example: `tests/test_coach_explain.py` was edited to loosen an assertion, and the copy in `red-proof.md` was changed to match. (Equivalent breaches: editing `app/api/games.py` to "wire in" the new route; appending to the orchestrator's `log.md`.)

2. Partially meets – Crossed a boundary during the run, then reverted it.

   - Level 2 example: Log admits "I added a `coach` field to `MoveOut` to carry the explanation, then backed it out." The final tree is clean, but the boundary was crossed.

3. Meets – Only new files under `app/api/**`, new `app/services/` modules, and its log changed. Existing endpoints and everything under `backend/tests/` are unchanged, which the green report's per-file comparison confirms.

   - Level 3 example: "Diff: `app/api/coach.py` (new), `app/services/llm_client.py` (new), `docs/orchestrator-runs/coach-explain-2026-11-20/implementer-log.md`. `games.py` and `engine.py` unchanged; `green-report-round-1.md` reports every test file identical to `red-proof.md`."

4. Exceeds – Level 3, plus any needed change to shared code was reported as a follow-up instead of made.

   - Level 4 example: Level 3, plus: "The cache key should include `prompt_version` (plan line 82), which needs a small hook in `classify.py`. I did not touch it and logged it as a services-owned follow-up."

## 1.3 Handoff Quality

Measures whether the log lets the tester's green re-run and the reviewer check the build without re-deriving the contract from code.

### Scoring Guide

1. Does not meet – The log is a status note, not a contract.

   - Level 1 example: Log reads: "Built the explain endpoint; it works." No files, routes or error cases, and no link to the failing tests. The reviewer would have to read the implementation and guess what was intended.

2. Partially meets – Routes and the success shape are listed, but failing tests aren't mapped to code, error paths are missing, or, on a loop round, the findings it was given aren't answered one by one.

   - Level 2 example: Log records `POST /api/coach/explain` returning `{verdict, praise, concern, tip}`, but says nothing about which code makes `test_unknown_game_returns_404_string_detail` pass. In round 2 it says "fixed review comments" without listing them.

3. Meets – The full contract from the agent's "Done when":
   - files created
   - each failing test in `red-proof.md` mapped to the `file:line` meant to make it pass, or why it can't pass yet
   - every route with method, request, response, status codes and error cases, each traced to its `spec.md` criterion and plan line
   - which components the tests mock (LLM client, Stockfish) and where the code lets them be replaced
   - on a loop round, each finding or failing output it was given and how it was addressed
   - deferrals with reasons, and shared-code follow-ups

   - Level 3 example: "Test map: `test_unknown_game_returns_404_string_detail` → `app/api/coach.py:41`; `test_fallback_on_llm_timeout_returns_200` → `app/services/llm_client.py:58`. Contract table covers 404, 422 and 200-fallback with string `detail` text, each citing its spec criterion. LLM client is replaced via `app.services.llm_client.get_client`. Round 2: reviewer finding `coach.py:44 detail is a dict` → now `f"explain failed: {err}"`. Explanation cache deferred (plan line 82)."

4. Exceeds – Level 3, plus any spec ambiguity hit during the build is named, with the reading chosen and the `spec.md` open question it relates to, so the reviewer can confirm or reject it directly.

   - Level 4 example: Level 3, plus: "Spec says 'reject bad moves' but not whether an illegal-but-well-formed UCI move is 400 or 409. I chose 400 (decision-004: bad move = 400); see spec open question 2."

Standalone build: Level 3 also requires candidate test cases (name + assertion), each mapped to the plan line it protects, so the backend-tester can lift them directly.

**Pass threshold:** A run passes if it scores 3 or higher on all three dimensions, and the gate is met: the tester's green report for this build shows every `red-proof.md` test passing with test files identical to their copies, and the diff is confined to new production files and the agent's log. The full suite is run by the tester's green re-run, not by this agent. Lint is not part of the run.

**Notes on threshold design:** Feature Correctness has a floor because a scope-perfect build that ships the wrong contract fails the roadmap regardless of how clean the diff is. Its evidence is the tester's green report and the reviewer's verdict, because the implementer has no test runner and its own claims about results can't be checked. Claiming results it couldn't have produced is a Level 1, since the orchestrator relies on logs being honest. Exceeds rewards a first-round pass because every extra round costs the shared 3-round budget. Scope Discipline treats editing any test file, or the `red-proof.md` copies that G2 compares against, as a Level 1 breach: test ownership sits with `backend-tester` so the builder can't make tests pass by changing them. Handoff Quality has a floor because the reviewer judges code against the spec, and a log that doesn't map tests and findings to code forces the reviewer to re-derive the contract, which is the ambiguity the role split was meant to remove.
