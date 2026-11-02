# Handoff: Position-Builder Drift Investigation (Run 2)

Nov 1, 2026 · @kris

## Summary

A second drift-investigator run found 12 inconsistencies between the position-builder agent, its PRD and its rubric. Phase 1 rated them 2 high (D1, D2), 2 medium (D3, D4), 2 low-medium (D5, D7) and 6 low. None of the reviewed files, code or fixtures were changed, and all fixes are still open.

**Phase 2 update (Nov 1, 2026):** All citations were re-checked and hold, and the Stockfish test now passes (13 passed, 0 skipped). The requirement for real Lichess games was dropped, so D2 is no longer an open decision. It is now a medium finding about stale text in the agent (and the `lichess.org` WebFetch allow in `settings.json`), with a set fix. Counts are now 1 high, 3 medium, 2 low-medium, 6 low. Details are in `docs/drift-report.md`.

The run was a single drift-investigator agent. It compared the working-tree (uncommitted) versions of `.claude/agents/position-builder.md`, `docs/prd-positions.md` and `docs/rubric-positions.md`, and checked their claims against the code. The findings below come from its report (`docs/drift-report.md`). They were independently re-checked in Phase 2.

## Progress since run 1

Of the two high findings from run 1, D1 remains open and High. D2’s decision was settled by the requirement change; it is now a Medium/Stale cleanup finding.

## Scope and limits

- **5-file cap waived.** The agent read 9 files: the 3 targets plus `scenarios.json`, `positions.json`, `test_classify_positions.py`, `classify.py`, `engine.py` and `pyproject.toml`. The cap was waived in the Phase 1 prompt (`iteration-log-drift.md:21`).
- **Stockfish run in Phase 2.** Phase 1 did not re-measure the losses. Phase 2 ran `uv run pytest tests/test_classify_positions.py` with `STOCKFISH_PATH` set, and all 13 tests passed.
- **Report file.** It wrote the report to `docs/drift-report.md`, which had been deleted in the working tree. The run-1 report is still in git history.

## Findings

| ID | Severity | Conflict | Where | Suggested fix |
| --- | --- | --- | --- | --- |
| D1 | High | The PRD lets a scenario be reported as unverified. But the PRD and the rubric make a passing `test_classify_positions.py` a hard gate, and the test fails on any missing scenario. | `prd-positions.md:17-18` vs `:28`; `rubric-positions.md:57-63` vs `:66`; `test_classify_positions.py:52-54` | Say an unverified scenario means an honest fail, or have the test mark missing scenarios as expected failures (xfail). |
| D2 | Medium (was High) | *Revised:* Lichess sourcing is no longer required, but the agent still requires it, grants WebFetch and forbids constructed positions ("Never invent"). The PRD and rubric are already correct. | `position-builder.md:3,4,11,14,18,36`; `settings.json:7`; `agent-summary.md:46,52` | Remove the Lichess and WebFetch text from the agent, replace L18 with the PRD wording, remove the `settings.json` allow, update `agent-summary.md`, and bump the agent version. |
| D3 | Medium | The agent has no "Done when" step and never tells itself to run the test. | `position-builder.md:35`; `prd-positions.md:26-28`; `rubric-positions.md:66` | Add a "Done when" section to the agent. |
| D4 | Medium | The agent's tools section claims write access to test scripts and fixtures. Its own rules and the PRD allow writing only `positions.json`. | `position-builder.md:34` vs `:29-30`; `prd-positions.md:22-23` | Limit the tools line to `positions.json`. |
| D5 | Low-Med | The agent leaves out the right side to move, moves in UCI format, what `loss_cp` means, and the `analyse` function name. The test enforces the first two. | `prd-positions.md:11,12,18`; test `:69-72` | Copy these into the agent. |
| D6 | Low | "Engine tests not skipped" describes a skip that doesn't exist. Without `STOCKFISH_PATH` set, the tests error out instead. | `prd-positions.md:28`; `rubric-positions.md:66`; `engine.py:16-17` | Reword to require that `STOCKFISH_PATH` is set and the tests run. |
| D7 | Low-Med | "positions.json is the only changed file" doesn't say what to compare against. | `prd-positions.md:27`; `rubric-positions.md:66` | Name a baseline commit. |
| D8 | Low | Rubric Verification Accuracy Level 4 mostly repeats what passing the test already requires. | `rubric-positions.md:21`; test `:97-98` | Make Level 4 require that the losses in the report match what the test measures, with each safe range shown. |
| D9 | Low | The rubric doesn't penalise going over the 3-attempt limit, and it asks for attempt counts that the PRD and agent never require. | `rubric-positions.md:61`; `prd-positions.md:19`; `position-builder.md:26` | Add attempt counts to the PRD and agent, and grade the limit. |
| D10 | Low | The rubric refers to "Phase 4", which the PRD never defines. | `rubric-positions.md:67,70` | Remove or define it. |
| D11 | Low | Paths mix `backend/tests/...` with `app/...` and `tests/...`, and nothing says the pytest command has to run from `backend/`. | `prd-positions.md:12,28`; `position-builder.md:19,35` | Use one root and state the working directory. |
| D12 | Low | Stray backtick: "or`scenarios.json cannot be read". | `position-builder.md:31` | Fix the typo. |

## Confirmed consistent

The following checked out across all three files and the code:

- The scenario fields, depth 15 with `multipv=1`, and the safe ranges (which fit inside the `classify.py` thresholds).
- The five position fields, the 20 cp tolerance, the 3-attempt rule, never changing `expected_bucket`, and the write limits.
- `positions.json` has all 6 ids with the right fields and side to move, its stored losses are inside the safe ranges, and Stockfish confirms every label (Phase 2).

## Next steps

Decide D1 first. It is the only intent decision still open from run 1, because the requirement change settled D2.

- [ ] D1: should an unverified scenario fail the run, or should the test xfail missing scenarios?
- [x] D2: are real Lichess games required? **No** (requirement dropped Nov 1, 2026).
- [ ] D2 cleanup: remove the Lichess and WebFetch text from the agent and the `lichess.org` allow from `settings.json`, then update `agent-summary.md`.
- [ ] Apply the agent-file fixes: D3, D4, D5, D12.
- [ ] Apply the PRD and rubric wording fixes: D6–D11.
- [ ] Decide whether to commit `docs/drift-report.md` and this handoff.
- [ ] Re-run the drift-investigator after the fixes to confirm they're resolved.
