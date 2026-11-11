# Quality Rubric: endpoint-builder

Scores one run of the `endpoint-builder` agent, which builds a new API endpoint from `ai_chess_coach_project_plan.md`. It is a builder, not an auditor: existing endpoints and existing tests are out of scope for edits.

## 1.1 Feature Correctness

Measures whether the new endpoint matches the plan's contract — request/response shape, status codes, and error behavior.

### Scoring Guide

1. Does not meet – Endpoint exists but its contract contradicts the plan.

   - Level 1 example: `POST /api/coach/explain` returns free-form prose text instead of the schema-constrained JSON object `{verdict, praise, concern, tip}` mandated by plan line 73.

2. Partially meets – Shape matches, but an error path is wrong.

   - Level 2 example: The success response is correct, but an unknown `game_id` returns a 500 with a stack trace instead of a 404 with string `detail`.

3. Meets – Success and every documented error path match the plan; assertions name the plan line that mandates them.

   - Level 3 example: "Unknown game → 404, malformed body → 422, LLM unreachable → 200 with templated fallback — all asserted in `test_coach_explain.py`, per plan lines 57 and 83. Response schema asserted key-by-key against plan line 74."

4. Exceeds – Level 3 plus fallback and edge behavior are also pinned.

   - Level 4 example: Level 3, plus: "Mocked client raising `TimeoutError` still yields a 200 with a valid four-key JSON body; a response missing `tip` fails validation; `prompt_version` appears in the cache key per plan line 82 (or is logged as deferred)."

## 1.2 Test Evidence

Measures whether the run's claims are proven by tests that need no credentials and no network.

### Scoring Guide

1. Does not meet – "Should work" with no new tests, or tests that silently require a real API key.

   - Level 1 example: Report says "endpoint built and working"; no new test file exists, and the only way to exercise it is a manual curl with `GROQ_API_KEY` set.

2. Partially meets – Happy path only; error paths untested.

   - Level 2 example: `test_explain_returns_json` passes, but the 404-for-unknown-game and fallback-on-failure paths have no tests.

3. Meets – A new test file covers success plus each error path; full suite green with `llm`-marked tests correctly skipped when no key is set.

   - Level 3 example: "New `tests/test_coach_explain.py`: 8 passed. Suite: 105 passed, 3 skipped (engine + llm markers; `STOCKFISH_PATH` and no key set). `ruff check .`: no issues."

4. Exceeds – Level 3 plus a test proves the offline fallback fires and nothing reached the network.

   - Level 4 example: Level 3, plus: "`test_fallback_on_llm_failure` mocks the client to raise and asserts a 200 templated response; the run's report shows no WebFetch/Bash network calls, and no test reads `.env`."

## 1.3 Scope Discipline

Measures whether the agent stayed a builder and touched only new files.

### Scoring Guide

1. Does not meet – Modified an existing `app/` file or an existing test.

   - Level 1 example: `app/api/games.py` is in the diff because the agent "wired the explain route into the games router" by editing it.

2. Partially meets – Modified existing code and reverted it.

   - Level 2 example: Report admits "I added a `coach` field to `MoveOut` to carry the explanation, then backed it out." Final tree is clean, but the boundary was crossed during the run.

3. Meets – Only new files under `app/api/**`, new `app/services/` modules, new test files, and its log changed; existing endpoints and tests byte-identical.

   - Level 3 example: "Diff: `app/api/coach.py` (new), `app/services/llm_client.py` (new), `tests/test_coach_explain.py` (new), `docs/iteration-log-endpoint-builder.md`. `games.py`, `engine.py` and all existing tests unchanged; full suite green."

4. Exceeds – Level 3 plus any needed change to shared code was reported as a follow-up instead of made.

   - Level 4 example: Level 3, plus: "The cache key should include `prompt_version` (plan line 82), which wants a small hook in `classify.py`; I did not touch it and logged it as a services-owned follow-up."

**Pass threshold:** A run passes if it scores 3 or higher on all three dimensions, and the gate is met: `uv run pytest` and `uv run ruff check .` are green, with the diff confined to new files and the agent's log.

**Notes on threshold design:** Feature Correctness has a floor because a scope-perfect run that ships the wrong contract fails the roadmap regardless of how clean the diff is. Test Evidence has a fallback-heavy feature like `coach/explain` would otherwise pass on manual curls alone — tests must carry the claim. Scope Discipline has a floor because a builder that edits shared files collides with every other agent, which is exactly the overlap this rubric exists to prevent.
