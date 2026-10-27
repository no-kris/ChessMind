# Handoff: Position-Builder Drift Investigation

Oct 27, 2026 · @kris

## Summary

The drift-investigator agent found 10 inconsistencies between the position-builder agent, its PRD and its rubric: 2 high, 4 medium, 4 low. No reviewed file or code was changed; all fixes are still open.

The run was a single drift-investigator agent, asked to compare `.claude/agents/position-builder.md`, `docs/prd-positions.md` and `docs/rubric-positions.md`, and to check their claims against the code. The findings below come from its report and were not independently re-checked.

## Scope and limits

Besides the three files under review, the agent read 6 code files to check claims: `scenarios.json`, `positions.json`, `test_classify_positions.py`, `classify.py`, `engine.py` and `pyproject.toml`.

- **No network access.** It could not confirm that the positions in `positions.json` come from real Lichess games.
- **5-file cap exceeded.** The drift PRD caps reads at 5 files (`docs/prd-drift-investigation.md:24`). The extra reads followed the session's instruction to check claims against code.
- **One new file.** It wrote the full report to `docs/drift-report.md`, as the drift PRD and agent definition require. That file is uncommitted.

## Findings

The two high findings block a clean run today; the rest are wording and grading gaps.

| ID | Severity | Conflict | Where | Suggested fix |
| --- | --- | --- | --- | --- |
| D1 | High | PRD lets a failing scenario be reported as unverified, but the test fails if any scenario is missing from `positions.json`. Rubric has the same conflict. | `prd-positions.md:17-18` vs `:28`; `test_classify_positions.py:45-51`; `rubric-positions.md:57-59` vs `:66` | State that an unverified scenario fails the run, or let the test accept a known-unverified list (xfail). |
| D2 | High | Only the agent requires real Lichess games and the move actually played. PRD says "choose" and allows a different move; rubric never checks the source; the test's 5 fixed fields leave no room for a game URL. | `position-builder.md:3,8,12,13`; `prd-positions.md:11,17`; `rubric-positions.md:41-43`; `test_classify_positions.py:28,57` | Add Lichess to the PRD and a source check to the rubric, or drop it from the agent. |
| D3 | Medium | Agent grants WebFetch, allows lichess.org only and stops if Lichess is down; PRD has no network rule or Lichess stop condition. | `position-builder.md:4,16,17`; `prd-positions.md:24` | Follows the D2 decision. |
| D4 | Medium | Agent may write only `positions.json`; PRD allows scratch scripts in `/tmp`. | `position-builder.md:14`; `prd-positions.md:22` | Add the `/tmp` allowance to the agent. |
| D5 | Medium | Rubric grades whether reported losses match the test, but the test never compares against `loss_cp` or prints the measured loss. | `rubric-positions.md:6,21-23`; `test_classify_positions.py:90-94` | Set a tolerance; assert it in the test or show the grader the measured loss. |
| D6 | Medium | Rubric "Meets" needs each passing scenario's loss and label in the report; PRD step 6 doesn't ask for them, so following the PRD scores 2, below the pass mark of 3. | `rubric-positions.md:17`; `prd-positions.md:19` | Add loss and label to PRD step 6. |
| D7 | Low | PRD doesn't set `multipv`; engine defaults to 3, test uses 1, so reported losses can differ. | `prd-positions.md:12`; `engine.py:26`; `test_classify_positions.py:84,86` | Add `multipv=1` to PRD step 3. |
| D8 | Low | Agent description says it builds positions for `scenarios.json`; the output is `positions.json`. | `position-builder.md:3` | Reword the description. |
| D9 | Low | Done-when gaps: "not skipped" can't happen (no skip logic; missing `STOCKFISH_PATH` errors instead); pytest working directory unstated; "only changed file" needs a baseline commit. | `prd-positions.md:27-28`; `rubric-positions.md:66` | Reword Done-when and name a baseline commit. |
| D10 | Low | Rubric refers to "Phase 4", which the PRD doesn't define. | `rubric-positions.md:67,70` | Remove the reference or define the phase. |

## Confirmed consistent

These checked out across the three files and the code, so they need no changes.

- Scenario and output field names (`prd-positions.md:10,18`) match `scenarios.json` and the test.
- Safe loss ranges (`prd-positions.md:13-16`) match the test (`test_classify_positions.py:21-26`) and fit inside the `bucket()` thresholds (`classify.py:14-22`).
- Depth 15 matches the test and the engine default.
- The referenced function names exist.
- The rule against changing a label agrees across all three files, and the test enforces it (`:61`).
- All 6 scenario IDs in the rubric's examples exist, with correct loss and label pairs.
- The output path is the same everywhere.

## Next steps

Decide D1 and D2 first: D3 depends on D2, and D5 and D6 depend on how strictly reported losses are checked.

- [ ] D1: should an unverified scenario fail the run, or should the test accept a known-unverified list?
- [ ] D2: are real Lichess games required? If yes, update the PRD and rubric; if no, update the agent.
- [ ] D5/D6: pick a loss tolerance and how the grader sees the measured loss.
- [ ] Apply the low-severity wording fixes (D4, D7-D10).
- [ ] Decide whether to keep and commit `docs/drift-report.md`.
- [ ] If Lichess sourcing matters, check `positions.json` against real games with network access.
