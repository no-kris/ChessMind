# Drift Report: position-builder agent, PRD and rubric

**Targets:** `.claude/agents/position-builder.md`, `docs/prd-positions.md`, `docs/rubric-positions.md`
**Checked against:** `backend/tests/fixtures/scenarios.json`, `backend/tests/fixtures/positions.json`, `backend/tests/test_classify_positions.py`, `backend/app/services/classify.py`, `backend/app/services/engine.py`, `backend/pyproject.toml` (pytest config only)
**Note on scope:** the drift PRD (`docs/prd-drift-investigation.md:24`) caps a task at 5 files. The caller asked for the three docs and named the code and fixtures to check them against, so this run read 3 targets plus the files they mention by path. No files other than this report were changed. The network was not used, so the Lichess origin of the positions could not be checked.

Classifications: **Contradiction** (the sources disagree), **Gap** (one source requires or grades something the others don't cover), **Unverifiable** (the code can't check what the doc claims).

---

## Findings

### D1. The run cannot pass when any scenario is left unverified (HIGH, Contradiction)
- `docs/prd-positions.md:17` says: "If it still fails, report it as unverified and move on."
- `docs/prd-positions.md:18` says to write only the *passing* positions.
- `docs/prd-positions.md:28` makes `uv run pytest tests/test_classify_positions.py` passing a Done-when gate.
- `backend/tests/test_classify_positions.py:45-51` (`test_positions_match_scenarios`) fails when any scenario in `scenarios.json` has no entry in `positions.json`: "No verified position for: ...".
- `docs/rubric-positions.md:57-59` gives "Meets" to a run with an unverified scenario, but `docs/rubric-positions.md:66` also requires the test to pass.
- **Result:** if one scenario ends up unverified, the run fails the gate. That makes the PRD's "unverified" path and the rubric's Level 3 Report Completeness example impossible in a passing run.
- **Recommendation:** decide which outcome you want. (a) If an unverified scenario should fail the run, say so in PRD step 4 and in the rubric pass threshold. (b) If partial success is allowed, the test needs a way to accept known-unverified scenarios, such as an xfail list. The code is the stricter and clearer side, so (a) is the smaller change. Either way, this is your decision.

### D2. Only the agent requires positions from real Lichess games (HIGH, Contradiction/Gap)
- `.claude/agents/position-builder.md:3,8,12` require positions "from real Lichess games" and say: "Never invent or edit a position."
- `.claude/agents/position-builder.md:13` says: "The graded move must be the move actually played in that game."
- `docs/prd-positions.md:11` says only to "choose a position (FEN) and a move that fit the description". It doesn't mention where the position comes from.
- `docs/prd-positions.md:17` says: "try a different position **or move**." Under the agent's rule, changing only the move isn't allowed, because the move must be the one played in the game.
- `docs/rubric-positions.md` doesn't grade where positions come from. The nearest point is Level 4 Scenario Fidelity, "reached from normal play" (`:41-43`), which is weaker.
- `docs/prd-positions.md` doesn't mention the agent's link to the PRD (`.claude/agents/position-builder.md:9`, "Follow docs/prd-positions.md exactly"). Following the PRD exactly would allow positions the agent definition forbids.
- **Unverifiable as written:** `backend/tests/test_classify_positions.py:28,57` requires the field set to be exactly `{id, fen, move, expected_bucket, loss_cp}`. So `positions.json` has no room for a game URL or ID, and nobody can check after the run that a position came from Lichess.
- **Recommendation:** if real-game sourcing is a requirement, add it to PRD step 2. Change step 4 to "try a different game". Add a provenance check to the rubric, for example under Scenario Fidelity or as a gate. Record the source somewhere the grader can see it: in the report, or by allowing an optional `source` field in the test, which is a code change for you to decide on. If sourcing isn't a requirement, remove it from the agent.

### D3. Only the agent allows network use and adds Lichess as a stop condition (MEDIUM, Gap)
- `.claude/agents/position-builder.md:4` grants `WebFetch`, and `:16` says: "Use the network only for lichess.org."
- `.claude/agents/position-builder.md:17` says to stop if "Stockfish, **Lichess** or the scenarios file isn't working".
- `docs/prd-positions.md:21-24` has no network rule, and its stop condition (`:24`) covers only Stockfish and the scenarios file.
- `docs/rubric-positions.md` doesn't mention network use or stopping because Lichess is unavailable.
- **Recommendation:** if D2 is resolved in favor of Lichess, add the network rule and the Lichess stop condition to the PRD Rules section. Otherwise, remove `WebFetch` and the Lichess clauses from the agent.

### D4. The agent and PRD disagree on scratch files (MEDIUM, Contradiction)
- `.claude/agents/position-builder.md:14` says: "Write only backend/tests/fixtures/positions.json."
- `docs/prd-positions.md:22` says: "Write only `positions.json`. Scratch scripts may go in `/tmp`."
- The agent has `Bash` and `Write` (`:4`), and in practice it needs a script to run `analyse` and `eval_loss`. Read strictly, the agent definition forbids those scripts.
- **Recommendation:** add the `/tmp` scratch allowance to the agent. The PRD is the more practical side here.

### D5. The rubric grades loss accuracy that the test never checks (MEDIUM, Unverifiable)
- `docs/rubric-positions.md:6` asks for "losses close to what the test measures", and `:21-23` (Level 4) asks for "losses match the test's measurements ... The test measures the same 165."
- `backend/tests/test_classify_positions.py:90-94` computes the loss itself and checks only the label and the safe range. It never compares the result with `pos["loss_cp"]`. `loss_cp` is checked only as a required key (`:28,57`).
- A passing test doesn't print the measured loss, so the grader can't see it.
- `docs/prd-positions.md:18` requires `loss_cp` but doesn't say how close it must be to what the test measures.
- **Recommendation:** pick a tolerance, for example plus or minus 20 cp. Then either add an assertion to the test, which is a code change for you to decide on, or tell the grader in the rubric how to get the measured loss (for example, a print or `-rA` output). Add the tolerance to PRD step 5.

### D6. The rubric's "Meets" level asks for more than the PRD's report step (MEDIUM, Gap)
- `docs/prd-positions.md:19` says: "Report which scenarios passed, and for each unverified one, the best attempt and its loss." It doesn't ask for the loss or label of scenarios that passed.
- `docs/rubric-positions.md:17` (Verification Accuracy Level 3, "Meets") requires the report to give "each one's measured loss and label". A run that follows the PRD exactly scores only Level 2 (`:13`), which is below the pass threshold of 3 (`:66`).
- `docs/rubric-positions.md:61` (Report Completeness Level 4) also asks for attempt counts and failure reasons. That's acceptable as an "Exceeds" level.
- **Recommendation:** change PRD step 6 to "report each scenario's loss and label". The rubric's expectation is reasonable, and the PRD should state it so a run that follows the PRD can pass.

### D7. The PRD doesn't specify `multipv`, and the defaults differ from the test (LOW-MEDIUM, Gap)
- `docs/prd-positions.md:12` says to use `analyse` at depth 15.
- `backend/app/services/engine.py:22-26` defaults to `multipv=3`. `backend/tests/test_classify_positions.py:84,86` calls it with `multipv=1`.
- Stockfish can give slightly different scores at the same depth with different `multipv` settings. An agent that uses the defaults could report losses that differ from the test, which affects D5.
- Depth matches: PRD `:12` = 15, test `:18` = 15, engine default = 15, with a cap of `MAX_DEPTH = 18`.
- **Recommendation:** add "with `multipv=1`, matching the test" to PRD step 3. The test is the right side here.

### D8. The agent's description names the wrong target file (LOW, Wording)
- `.claude/agents/position-builder.md:3` says to use it "when asked to build positions for backend/tests/fixtures/scenarios.json". The output file is `positions.json` (`:14`, PRD `:18`), and `scenarios.json` must not be edited (PRD `:23`).
- **Recommendation:** change it to "build positions for the scenarios in `scenarios.json` (output: `positions.json`)".

### D9. Gaps in how the Done-when gates are worded (LOW, Gap)
- `docs/prd-positions.md:28` and `docs/rubric-positions.md:66` say the engine tests must run "not skipped". `backend/pyproject.toml` only registers the `engine` marker, and there is no conftest skip logic. Without `STOCKFISH_PATH`, `open_engine` raises `RuntimeError` (`backend/app/services/engine.py:15-17`), so the tests *error* rather than skip. The gate holds, but the wording describes a failure mode that doesn't exist.
- The command at `docs/prd-positions.md:28` uses a path relative to `backend/`, and the working directory isn't stated.
- `docs/prd-positions.md:27` says "`positions.json` is the only changed file". The working tree already has many modified files, so the gate needs a baseline (for example, a diff against the commit at the start of the run).
- **Recommendation:** in the PRD, say "run from `backend/` with `STOCKFISH_PATH` set". Define "changed" relative to the starting commit.

### D10. The rubric refers to "Phase 4", which the PRD doesn't define (LOW, Gap)
- `docs/rubric-positions.md:67,70` refer to "Phase 4". `docs/prd-positions.md` doesn't mention it, though `:31` refers to future tactics work.
- **Recommendation:** link or define Phase 4 in the PRD, or reword the rubric.

---

## Checked and consistent (no drift)
- **Scenario schema:** PRD `:10` (`id`, `side_to_move`, `description`, `expected_bucket`) matches `backend/tests/fixtures/scenarios.json:1-38`.
- **Output schema:** PRD `:18` (`id`, `fen`, `move` UCI, `expected_bucket`, `loss_cp`) matches `test_classify_positions.py:28,57,69`.
- **Safe ranges:** PRD `:13-16` match `test_classify_positions.py:21-26`. Each range falls inside its `bucket()` band in `backend/app/services/classify.py:14-22` (good <30, inaccuracy <100, mistake <300, blunder 300 or more).
- **Function names:** `analyse` (`engine.py:22`), `eval_loss` and `bucket` (`classify.py:4,14`) exist as the PRD `:12` names them.
- **Never change the label:** agent `:15`, PRD `:17` and rubric `:49` agree, and the test enforces it (`test_classify_positions.py:61`).
- **Scenario count and IDs:** there are 6 scenarios. Every ID the rubric uses in its examples exists in `scenarios.json`, and every loss and label pair in the examples (845/blunder, 4/good, 165/mistake, 140/mistake, 112/mistake) agrees with `bucket()`.
- **Output path:** `backend/tests/fixtures/positions.json` is the same in the agent (`:14`), the PRD (`:18`) and the test (`:33`).

## Summary
| ID | Severity | Type | Likely side to change |
|----|----------|------|-----------------------|
| D1 | High | Contradiction | PRD and rubric (or the test, if partial success is allowed) |
| D2 | High | Contradiction/Gap | PRD and rubric (if Lichess is required) |
| D3 | Medium | Gap | PRD (follows D2) |
| D4 | Medium | Contradiction | Agent |
| D5 | Medium | Unverifiable | Test or rubric, plus PRD |
| D6 | Medium | Gap | PRD |
| D7 | Low-Medium | Gap | PRD |
| D8 | Low | Wording | Agent |
| D9 | Low | Gap | PRD |
| D10 | Low | Gap | Rubric or PRD |

These are recommendations. The final decision on each is yours.
