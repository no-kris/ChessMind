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

---

## Findings

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
