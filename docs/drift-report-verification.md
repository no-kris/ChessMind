# Drift Report Verification

Oct 27, 2026 · position-builder drift investigation, phase 1 check

An independent check of `docs/drift-report.md` and its handoff, `docs/handoff-drift-positions.md`, against the agent definition, PRD, rubric and code. The drift-investigator was not rerun, and no reviewed file was changed.

## Verdict

The report holds up. All 10 findings are real, and every file and line reference points to what the report says it does. Four details in the report and three in the handoff need correcting. The most important: D7 is understated, because the engine's default setting pushes one position out of its safe range.

## What was run

- **Positions test.** `uv run pytest tests/test_classify_positions.py -rA` from `backend/` with `STOCKFISH_PATH=/usr/games/stockfish`: 13 of 13 passed, with the engine tests actually running. D1 is latent today, since all 6 scenarios are verified. It only matters on a run that leaves a scenario unverified.
- **Without Stockfish.** With `STOCKFISH_PATH` unset, the engine test fails with a `RuntimeError`. It doesn't skip, and pytest reports it as a failure, not an error.
- **Loss comparison.** Each position's loss was re-measured at depth 15 with the test's setting (`multipv=1`) and the engine's default (`multipv=3`).

| Scenario | Label | Safe range | Reported | multipv=1 | multipv=3 |
| --- | --- | ---: | ---: | ---: | ---: |
| `white_opening_move` | good | 0–10 | 0 | 0 | 0 |
| `black_opening_reply` | good | 0–10 | 0 | 0 | 0 |
| `white_hangs_queen` | blunder | ≥320 | 813 | 813 | 780 |
| `black_misses_mate` | blunder | ≥320 | 9537 | 9537 | 9516 |
| **`white_passive_move`** | inaccuracy | 50–79 | 55 | 55 | **48 (out of range)** |
| `black_loses_pawn` | mistake | 120–279 | 220 | 220 | 219 |

Every stored `loss_cp` matches what the test measures exactly. So D5 (the test never checks `loss_cp`) is a gap in the test, not a problem with the current data.

## Corrections to the drift report

1. **D7 should be Medium, not Low-Medium.** The report says scores "can differ slightly." The table above shows they do: with the engine's default `multipv=3`, `white_passive_move` scores 48, below its 50–79 range. An agent that follows the PRD as written would have rejected that position or reported a loss the test doesn't measure.
2. **D10 is partly wrong.** "Phase 4" is defined in `ai_chess_coach_project_plan.md:45` as "Evaluation Pipeline & Delta Classification." The PRD just doesn't link to it, so the fix is a link, not a new definition.
3. **D9 has a small wording error.** Without `STOCKFISH_PATH`, the engine tests fail; they don't error. The conclusion is unchanged: they never skip.
4. **D6 is slightly overstated.** A report written by following the PRD sits between Level 2 and Level 3, not clearly at Level 2. The gap is still real, because nothing in the PRD makes a run reach Level 3.

## Corrections to the handoff

1. **Commit status.** The handoff says `docs/drift-report.md` is uncommitted. It was committed in `18308b4`.
2. **D7 severity.** The handoff lists D7 as Low and the report as Low-Medium. Given the loss comparison, both should say Medium. The severity count becomes 2 high, 5 medium, 3 low.
3. **File limit.** The handoff treats the 5-file limit as a scope note. The drift PRD (`docs/prd-drift-investigation.md:24`) says to ask the user before reading more than 5 files. The agent read 9 without asking, which is a process violation.

## Finding by finding

| ID | Severity | Verdict | Notes |
| --- | --- | --- | --- |
| D1 | High | Confirmed | The test fails if any scenario is missing (`test_classify_positions.py:45-51`). Latent today: all 6 pass. |
| D2 | High | Confirmed | Only the agent requires real Lichess games. Sourcing can't be checked without network access. |
| D3 | Medium | Confirmed | The PRD has no network rule or Lichess stop condition. |
| D4 | Medium | Confirmed | The agent forbids the `/tmp` scripts the PRD allows. |
| D5 | Medium | Confirmed | The test never compares against `loss_cp`. The current values match anyway. |
| D6 | Medium | Mostly | The gap is real; "scores only Level 2" overstates it. |
| D7 | Low-Medium → **Medium** | Understated | `multipv=3` puts `white_passive_move` at 48, outside its range. |
| D8 | Low | Confirmed | The description names `scenarios.json`; the output is `positions.json`. |
| D9 | Low | Mostly | The tests fail, not error. The other points hold. |
| D10 | Low | Partly wrong | Phase 4 is defined in the project plan. Only the link is missing. |

The report's "Checked and consistent" section also holds: field names, safe ranges against `bucket()`, depth 15, function names, the label rule, scenario IDs, the rubric's example loss/label pairs and the output path all check out. `scenarios.json` shows as modified in git, but the change is line endings only.

## Still unchecked

Whether the positions in `positions.json` come from real Lichess games (D2). This needs network access.
