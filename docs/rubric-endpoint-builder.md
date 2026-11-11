# Quality Rubric: endpoint-builder

Scores one run of the `endpoint-builder` agent, which builds a new API endpoint from `ai_chess_coach_project_plan.md`. It is a builder, not an auditor and not a tester: existing endpoints are out of scope for edits, and writing test files belongs to the `backend-test-author` agent.

## 1.1 Feature Correctness

Measures whether the new endpoint matches the plan's contract — request/response shape, status codes, and error behavior — as demonstrated by a smoke check quoted in the log (not by tests).

### Scoring Guide

1. Does not meet – Endpoint exists but its contract contradicts the plan, with no verification at all.

   - Level 1 example: `POST /api/coach/explain` returns free-form prose text instead of the schema-constrained JSON object `{verdict, praise, concern, tip}` mandated by plan line 73, and the log contains no run output of any kind.

2. Partially meets – Shape matches, but an error path is wrong or unverified.

   - Level 2 example: The success response is correct, but the log shows only the happy-path smoke run; the unknown-`game_id` path is asserted to "probably return 404" with no output proving it (and it actually returns 500).

3. Meets – Success and every documented error path were demonstrated with scratch-run output quoted in the log; each decision names the plan line that mandates it.

   - Level 3 example: "Smoke runs (inline `TestClient` script, not saved): unknown game → 404 with string detail, malformed body → 422, LLM unreachable → 200 with templated fallback — output pasted in the log, per plan lines 57 and 83. Response schema shown key-by-key against plan line 74."

4. Exceeds – Level 3 plus fallback and edge behavior are also pinned.

   - Level 4 example: Level 3, plus: "Client raising `TimeoutError` still yields a 200 with a valid four-key JSON body (output in log); a response missing `tip` was rejected by the schema; `prompt_version` handling noted as deferred per plan line 82."

## 1.2 Scope Discipline

Measures whether the agent stayed a builder and touched only new production files.

### Scoring Guide

1. Does not meet – Modified an existing `app/` file, an existing test, or wrote test files of its own.

   - Level 1 example: `tests/test_coach_explain.py` (new) is in the diff — the agent built the tests itself instead of handing the contract to `backend-test-author`. (Equivalent breach: editing `app/api/games.py` to "wire in" the new route.)

2. Partially meets – Modified existing code or wrote tests, then reverted them.

   - Level 2 example: Report admits "I added a `coach` field to `MoveOut` to carry the explanation, then backed it out." Final tree is clean, but the boundary was crossed during the run.

3. Meets – Only new files under `app/api/**`, new `app/services/` modules, and its log changed; existing endpoints, existing tests, and `backend/tests/**` byte-identical.

   - Level 3 example: "Diff: `app/api/coach.py` (new), `app/services/llm_client.py` (new), `docs/iteration-log-endpoint-builder.md`. `games.py`, `engine.py` and everything under `tests/` unchanged; existing suite still green."

4. Exceeds – Level 3 plus any needed change to shared code was reported as a follow-up instead of made.

   - Level 4 example: Level 3, plus: "The cache key should include `prompt_version` (plan line 82), which wants a small hook in `classify.py`; I did not touch it and logged it as a services-owned follow-up."

## 1.3 Handoff Quality

Measures whether the log leaves `backend-test-author` everything it needs to write the endpoint's tests without re-deriving the contract.

### Scoring Guide

1. Does not meet – The log is a status note, not a contract.

   - Level 1 example: Log reads: "Built the explain endpoint; it works." No paths, shapes, or error cases — the test-author would have to read the implementation and guess what was intended.

2. Partially meets – Endpoint and success shape listed, but error paths or status codes missing.

   - Level 2 example: Log records `POST /api/coach/explain` returning `{verdict, praise, concern, tip}`, but says nothing about unknown `game_id`, malformed bodies, or the fallback path.

3. Meets – Complete contract table plus deferrals: path | method | request | response | error cases (with status codes), which components are mocked and how, what was deferred and why.

   - Level 3 example: "Handoff table covers all 3 error cases (404 unknown game, 422 malformed body, 200 fallback on LLM failure) with status codes and string-detail text; notes the LLM client must be mocked via `app.services.llm_client`; defers the explanation cache (plan line 82) with a reason."

4. Exceeds – Level 3 plus candidate test cases the test-author can lift directly.

   - Level 4 example: Level 3, plus: "Candidate tests listed by name with assertions: `test_explain_unknown_game_returns_404_string_detail`, `test_fallback_on_llm_timeout_returns_200_valid_json`, `test_no_llm_call_on_move_path` (monkeypatch client to raise if called) — each mapped to the plan line it protects."

**Pass threshold:** A run passes if it scores 3 or higher on all three dimensions, and the gate is met: the existing `uv run pytest` suite and `uv run ruff check .` are green, with the diff confined to new production files and the agent's log — no test files written.

**Notes on threshold design:** Feature Correctness has a floor because a scope-perfect run that ships the wrong contract fails the roadmap regardless of how clean the diff is; with tests moved to another agent, the smoke check quoted in the log is the only in-run proof, so unverified paths cap the score. Scope Discipline now treats writing *any* test file as a Level 1 breach, because test ownership was moved to `backend-test-author` precisely to stop the two agents from colliding — a builder that writes tests re-creates that overlap. Handoff Quality has a floor because a correct endpoint with a thin log forces the test-author to re-derive the contract from code, which is exactly the ambiguity the split was meant to remove.
