<<<<<<< HEAD
# Drift Report: position-builder agent vs PRD vs rubric

**Date:** 2026-11-01
**Targets (working tree, uncommitted):**
- `.claude/agents/position-builder.md` (AGENT)
- `docs/prd-positions.md` (PRD)
- `docs/rubric-positions.md` (RUBRIC)

**Code/fixtures checked:** `backend/tests/fixtures/scenarios.json`, `backend/tests/fixtures/positions.json`, `backend/tests/test_classify_positions.py`, `backend/app/services/classify.py`, `backend/app/services/engine.py`, `backend/pyproject.toml` (pytest config only).

**Scope note:** The drift PRD caps a task at 5 files (`prd-drift-investigation.md:24`). This run read 3 targets and 6 supporting files. The cap was waived in the Phase 1 prompt ("operating under the waived 5-file cap rule", `iteration-log-drift.md:21`), so the extra reads were authorized.

**Revision (Phase 2, 2026-11-01):**
- **Verification.** Every file:line citation in D1–D12 and in the consistency table was re-checked against the current working tree and holds. The Stockfish check was then run (`STOCKFISH_PATH=/usr/games/stockfish`, from `backend/`): `uv run pytest tests/test_classify_positions.py` gave 13 passed, 0 skipped, so the current `positions.json` passes every gate the test enforces.
- **Requirement change.** Positions no longer have to come from real Lichess games. They may come from real games or be constructed, as long as they fit the scenario description. The PRD (L11) and the rubric (realism is an optional Level 4 trait, L41-43) already say this, so they are now authoritative and need no change. D2 is rewritten below: it is no longer an open decision, only stale text in the agent and its permissions. No other finding depended on Lichess sourcing.
- No target file, code, fixture or config was edited in Phase 2. Only this report (and its handoff) changed.

**Classification key:** Contradiction = the sources disagree. Omission = one source requires something another drops. Grading gap = the PRD requires something the rubric does not grade, or the reverse. Stale/Defect = a wrong reference or a typo.

---

## Verified consistent (no drift)

| Claim | AGENT | PRD | RUBRIC | Code |
|---|---|---|---|---|
| Scenario fields `id, side_to_move, description, expected_bucket` | L17 | L10 | n/a | scenarios.json L3-6 (all 6 entries) |
| Depth 15, `multipv=1` | L19 | L12 | n/a | test L18, L87, L89 (`engine.analyse` default is `multipv=3` at engine.py L26, so callers must pass 1 explicitly, as the docs say) |
| Safe ranges good <=10, inaccuracy 50-79, mistake 120-279, blunder >=320 | L20-23 | L13-16 | L23 (example 120-279) | test L24-29; all inside the `bucket()` cutoffs in classify.py L14-22 |
| Position fields `id, fen, move, expected_bucket, loss_cp` | L25 | L18 | n/a | test L31, L60 (exact set match); positions.json has all 6 with exactly these fields |
| 20 cp tolerance | L25 | L18 | L6, L21 | test L21, L98 |
| 3 attempts, never change `expected_bucket`, report unverified | L24 | L17 | L49, L59 | test L64 ("Label was changed") |
| Allowed/forbidden writes | L29-30 | L22-23 | L66 | n/a |
| 6 scenarios | n/a | n/a | L11, L15 | scenarios.json has 6 |

The current `positions.json` has the right field set, ids, side to move (checked against the FEN turn field), and stored `loss_cp` values inside the safe ranges (0, 0, 813, 9537, 55, 220). Phase 2 ran the Stockfish check: all 6 `test_stockfish_confirms_label` cases pass, so each stored `loss_cp` is within 20 cp of the measured loss and inside its safe range.
=======
# Drift Report: position-builder agent, PRD and rubric

**Targets:** `.claude/agents/position-builder.md`, `docs/prd-positions.md`, `docs/rubric-positions.md`
**Checked against:** `backend/tests/fixtures/scenarios.json`, `backend/tests/fixtures/positions.json`, `backend/tests/test_classify_positions.py`, `backend/app/services/classify.py`, `backend/app/services/engine.py`, `backend/pyproject.toml` (pytest config only)
**Note on scope:** the drift PRD (`docs/prd-drift-investigation.md:24`) caps a task at 5 files. The caller asked for the three docs and named the code and fixtures to check them against, so this run read 3 targets plus the files they mention by path. No files other than this report were changed. The network was not used, so the Lichess origin of the positions could not be checked.

Classifications: **Contradiction** (the sources disagree), **Gap** (one source requires or grades something the others don't cover), **Unverifiable** (the code can't check what the doc claims).
>>>>>>> 18bf59635310a08ab2c036c3af20484d63c22ccf

---

## Findings

<<<<<<< HEAD
### D1. The PRD's "Done when" test gate cannot be met when any scenario is unverified, yet the PRD and rubric both expect that outcome (HIGH, Contradiction)
- **PRD L17:** "If it still fails, report it as unverified and move on."
- **PRD L18:** "Write the passing positions to `backend/tests/fixtures/positions.json`"
- **PRD L28:** "`uv run pytest tests/test_classify_positions.py` passes"
- **Test L52-54:** `missing = [s for s in SCENARIOS_BY_ID if s not in ids]` ... `assert not missing, f"No verified position for: {missing}"`
- **RUBRIC L57-63:** Report Completeness Level 3/4 reward a run with unverified scenarios ("white_passive_move: unverified after 3 attempts").
- **RUBRIC L66:** "A run passes if ... `test_classify_positions.py` passes".
- **AGENT L24/L26:** follows the PRD unverified flow.

If even one scenario stays unverified, `positions.json` is missing it and `test_positions_match_scenarios` fails. That makes the run a fail under the rubric threshold, even though the rubric's own Level 3/4 examples describe that same run as good. As written, the honest-unverified path can never pass.
- **Authoritative:** The test reflects the current enforced behaviour. The PRD and rubric are where the intent has to be decided.
- **Suggested fix (user decides):** One option is to state in the PRD "Done when" and the rubric pass threshold that a run with unverified scenarios is an honest *fail*. Reports are still graded on completeness, and the run never passes. The other option is to change the test so that missing scenarios xfail or are listed. The first option needs only doc changes.

### D2. The agent still requires real Lichess games and network access after the requirement was dropped (MEDIUM, Stale) — *revised in Phase 2*
*Phase 1 rated this HIGH and left it as a choice between adding the rule to the PRD and rubric or removing it from the agent. The requirement change settles that choice: the rule is dropped, so the PRD and rubric are correct and the agent is out of date. Severity is lowered because the intent is no longer in dispute. What is left is cleanup, and until it is done the agent spends network calls and attempts on a rule nobody requires.*

Stale text in the agent:
- **AGENT L3:** "Finds and verifies chess test positions from real Lichess games"
- **AGENT L4:** `tools: ... WebFetch`. Nothing else in the PRD workflow needs network access.
- **AGENT L11:** justifies the agent by its ability to "search unstructured game databases".
- **AGENT L14:** "ensure they can be derived from real matches rather than synthetic/puzzle-like games"
- **AGENT L18:** "Choose a valid FEN and legal move from real games on lichess.org ... Never invent or edit positions." "Never invent" now forbids constructed positions, which the requirement allows.
- **AGENT L36:** "Web fetch / browsing capabilities to access real game archives ... from lichess.org."

Already correct (no change needed):
- **PRD L11:** "choose a position (FEN) and a move that fit the description." There is no sourcing rule.
- **RUBRIC L41-43:** realism ("reached from normal play") is an optional Level 4 trait, so real-game positions still earn credit without being required.
- **Test L60:** has no provenance field. That was a gap only while sourcing was mandatory and is no longer one.

Other files that state the old rule (outside this report's three targets, listed so the cleanup is complete):
- **`settings.json` L7:** `"allow": ["WebFetch(domain:lichess.org)"]`. This permission exists only for the dropped rule.
- **`agent-summary.md` L46, L52:** describe the agent as using "real Lichess games" and the WebFetch allow.
- `docs/iteration-log-positions.md` L64-84 records the v0.2.0 run that added the rule. It is a historical log, so it should stay as it is.

- **Authoritative:** PRD and rubric (unchanged), as updated by the requirement change.
- **Suggested fix:** In the agent, remove "from real Lichess games" from L3 and `WebFetch` from L4, and delete L36. Reword L11 and L14 so they do not depend on game databases. Replace L18 with the PRD's wording ("choose a position (FEN) and a move that fit the description; the FEN must be valid with the right side to move and the move legal"), which also fixes the side-to-move part of D5, and drop "Never invent or edit positions." Optionally keep "prefer positions reachable from normal play" as guidance that matches RUBRIC L41. Then remove the `lichess.org` WebFetch allow from `settings.json` and update `agent-summary.md`. Bump the agent version (L5), since its behaviour changes.

### D3. The agent leaves out the PRD's "Done when" gates and never tells the agent to run the test (MEDIUM, Omission)
- **PRD L26-28:** "`positions.json` is the only changed file." / "`uv run pytest tests/test_classify_positions.py` passes, with the engine tests actually running, not skipped."
- **RUBRIC L66:** makes both of these hard gates for the pass threshold.
- **AGENT:** has no completion criteria. The pytest command appears only as an available tool (L35), not as a required final step.

The agent can finish without running the test that the rubric uses as a gate.
- **Authoritative:** PRD and rubric (they agree).
- **Suggested fix:** Add a "Done when" step to the agent that copies PRD L27-28.

### D4. The agent claims test-file write access, contradicting its own rules and the PRD (MEDIUM, Contradiction)
- **AGENT L34:** "Read/Write access to project files (positions.json, test scripts/fixtures)."
- **AGENT L29-30:** "Write *only* positions.json." / "Never edit scenarios.json, test files (test_classify_positions.py)..."
- **PRD L22-23:** "Write only `positions.json`." / "Don't edit `scenarios.json`, the test file..."
- **Authoritative:** PRD.
- **Suggested fix:** Change AGENT L34 to "Read access to project files; write access to `backend/tests/fixtures/positions.json` only."

### D5. The agent drops details from PRD steps 2, 3 and 5 that the test enforces (LOW-MEDIUM, Omission)
- **Side to move:** PRD L11 says "with the right side to move". AGENT L18 says only "valid FEN and legal move". Test L69-70 asserts "Wrong side to move".
- **Move format:** PRD L18 says "`move` (UCI)". AGENT L25 lists `move` with no format. Test L72 uses `chess.Move.from_uci`, so SAN would fail.
- **Meaning of `loss_cp`:** PRD L18 says "`loss_cp` is the loss measured in step 3". AGENT L25 does not define it.
- **Function name:** PRD L12 names `analyse` from engine.py. AGENT L19 names only the module.
- **Authoritative:** PRD (matches test L69-72, L87-98).
- **Suggested fix:** Copy these details into AGENT L18, L19 and L25. The L18 part overlaps with D2: the PRD wording suggested there covers side to move.

### D6. The "not skipped" gate describes a skip mechanism that does not exist (LOW, Stale)
- **PRD L28:** "with the engine tests actually running, not skipped."
- **RUBRIC L66:** "with the engine tests actually running."
- **Code:** There is no conftest.py and no skip logic. `pyproject.toml` L24-25 only registers the `engine` marker. If `STOCKFISH_PATH` is unset, `open_engine` raises RuntimeError (engine.py L16-17), so the engine tests *error* instead of skipping. They could only be skipped by deselecting them on purpose, for example with `-m "not engine"`.
- **Authoritative:** Code.
- **Suggested fix:** Reword to "run without deselecting the `engine` marker (`STOCKFISH_PATH` set)", or add the intended skip logic. The doc change is the smaller one.

### D7. The "only changed file" gate has no baseline (LOW-MEDIUM, Grading gap)
- **PRD L27 / RUBRIC L66:** "`positions.json` is the only changed file."
- **Context:** The working tree already has many uncommitted changes (`git status`), including both fixtures, the test file and all three target files. The gate cannot be checked until a baseline is given.
- **Suggested fix:** State the baseline in the PRD, for example "relative to the commit/working tree at the start of the run; check with `git status`/`git diff --stat`".

### D8. Rubric Verification Accuracy levels overlap with what the test already enforces (LOW, Grading ambiguity)
- **RUBRIC L6:** "A high score requires ... losses within 20 cp of what the test measures."
- **RUBRIC L21:** Level 4 adds "losses match the test's measurements (within 20 cp), and the report shows each loss is inside its safe range."
- **Code:** Passing the test (already needed for Level 3) enforces the safe range (test L97) and a 20 cp gap between the *stored* `loss_cp` and the measured loss (test L98).

The real difference at Level 4 is whether the *reported* loss in the agent's message matches the measured loss and whether the safe range is shown. The rubric does not say this, so Level 3 and Level 4 are hard to tell apart.
- **Suggested fix:** Reword Level 4 as "the losses in the report (not just `loss_cp`) are within 20 cp of the test's measurements, and each is shown next to its safe range."

### D9. The PRD's 3-attempt limit is not graded, and the rubric's Level 4 asks for attempt counts that the PRD never requires (LOW, Grading gap)
- **PRD L17 / AGENT L24:** "up to 3 attempts".
- **RUBRIC L61:** Level 4 requires "attempt counts for every scenario" and "a specific reason for each failure". PRD L19 and AGENT L26 ask only for "the best attempt and its loss".
- **RUBRIC:** No dimension penalises going over 3 attempts.
- **Suggested fix:** Either add attempt counts to the PRD and agent reporting step, or accept that they are Level 4 only. Consider adding a Level 1 condition for going over the attempt limit.

### D10. The rubric refers to "Phase 4", which neither the PRD nor the agent defines (LOW, Undefined reference)
- **RUBRIC L67, L70:** "trusted for Phase 4", "the Phase 4 cases".
- **PRD L31:** says only "once tactics detection exists". It never mentions phases.
- **Suggested fix:** Define Phase 4 in the PRD's Out of scope section, or link to the plan document that defines it.

### D11. Mixed path roots and an unstated working directory (LOW, Ambiguity)
- **PRD L4/L18 and AGENT L14/L17/L25** use repo-root paths (`backend/tests/fixtures/...`).
- **PRD L12 and AGENT L19** use `app/services/...`, and **PRD L28 / AGENT L35** use `tests/test_classify_positions.py`. Both are relative to `backend/`.
- The command `uv run pytest tests/test_classify_positions.py` works only from `backend/` (pyproject.toml L21-23 lives there).
- **Suggested fix:** Use repo-root paths throughout, or state "run from `backend/`".

### D12. Typo in the agent: stray backtick (LOW, Defect)
- **AGENT L31:** "If Stockfish fails to start or`scenarios.json cannot be read". There is an unmatched backtick and a missing space.
- **Suggested fix:** "If Stockfish fails to start or `scenarios.json` cannot be read, report it and stop."

---

## Summary

| ID | Severity | Files | Issue | Authoritative |
|---|---|---|---|---|
| D1 | High | PRD L17-18, L28; RUBRIC L57-66; test L52-54 | The unverified path makes the pytest gate fail, so the run cannot pass | Decide in PRD/rubric (test is the enforced behaviour) |
| D2 | Medium (was High) | AGENT L3-4, L11, L14, L18, L36; settings.json L7; agent-summary.md L46, L52 | Lichess sourcing requirement was dropped, but the agent still requires it and grants WebFetch | PRD/rubric (already correct); fix the agent |
| D3 | Medium | AGENT (missing); PRD L26-28; RUBRIC L66 | Agent has no Done-when or run-the-test step | PRD/rubric |
| D4 | Medium | AGENT L34 vs L29-30; PRD L22-23 | Agent claims write access to tests/fixtures | PRD |
| D5 | Low-Med | AGENT L18, L19, L25; PRD L11-12, L18; test L69-72 | Side to move, UCI format, `loss_cp` meaning and `analyse` missing from agent | PRD |
| D6 | Low | PRD L28; RUBRIC L66; engine.py L16-17; pyproject L24-25 | "Not skipped" describes a skip that does not exist; tests error instead | Code |
| D7 | Low-Med | PRD L27; RUBRIC L66 | "Only changed file" has no baseline | n/a (clarify) |
| D8 | Low | RUBRIC L6, L21; test L97-98 | Level 3 and Level 4 overlap | Rubric (reword) |
| D9 | Low | PRD L17, L19; AGENT L24, L26; RUBRIC L61 | Attempt limit not graded; attempt counts not required | PRD (decide) |
| D10 | Low | RUBRIC L67, L70; PRD L31 | "Phase 4" undefined | PRD (define) |
| D11 | Low | PRD L12, L28; AGENT L19, L35 | Mixed path roots and unstated working directory | Either (normalise) |
| D12 | Low | AGENT L31 | Stray backtick | n/a |

After the Phase 2 revision: 1 high (D1), 3 medium (D2, D3, D4), 2 low-medium (D5, D7), 6 low. D1 is the only open intent decision. D2 now has a set fix.

The user makes the final decision on every finding. No target file, code, fixture or config was edited.
=======
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
>>>>>>> 18bf59635310a08ab2c036c3af20484d63c22ccf
