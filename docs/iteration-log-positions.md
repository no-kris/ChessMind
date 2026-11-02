# Iteration Log

## 1. Pre-Test Contract

**The definition and rubric were committed before Run 001.**

| Artifact | Commit | Date |
|---|---|---|
| Agent v0.1.0 | `a617a9e` | 2026-10-23 18:32:39 -0400 |
| PRD | `14615fd` | 2026-10-23 18:33:17 -0400 |
| Rubric + threshold | `0490393` | 2026-10-23 18:33:47 -0400 |
| Run 001 record | `8d21c5e` | 2026-10-23 19:14:13 -0400 |

`git merge-base --is-ancestor a617a9e 8d21c5e` succeeds. The baseline and rubric were committed about 41 minutes before the Run 001 record. `8d21c5e` is the **run record**, not the definition commit.

**Complete definition at baseline:**

| Element | Pre-test source |
|---|---|
| Role, tools, write restrictions, stop rule | agent v0.1.0 L4–13 |
| Workflow, loss ranges, retry limit, failure handling, report | PRD L10–19 |
| Pass gates | PRD L26–28; rubric L65–67 |

**Baseline definition v0.1.0 (`a617a9e`, verbatim):**

```markdown
---
name: position-builder
description: Builds and verifies chess test positions for ChessMind's move-quality scenarios. Use when asked to build positions for backend/tests/fixtures/scenarios.json.
tools: Read, Glob, Grep, Bash, Write
---

You build verified chess test positions for ChessMind.
Follow docs/prd-positions.md exactly.

Always:
- Write only backend/tests/fixtures/positions.json.
- Never change a scenario's expected label to match what Stockfish returned.
- If Stockfish or the scenarios file isn't working, report it and stop.
```

**Pass threshold (`0490393`):**

- Each dimension must score 3/4 or higher. An aggregate average is not enough.
- Both gates must pass: `positions.json` is the only changed file, and `test_classify_positions.py` passes with the engine tests running.

**Scoring anchors:**

| Dimension | 1/4 | 2/4 | 3/4 | 4/4 |
|---|---|---|---|---|
| Verification Accuracy | Claims verified, but a scenario fails | Claimed scenarios pass, but no evidence | Every scenario passes; loss and label reported | Losses match the test within 20 cp and each is shown inside its safe range |
| Scenario Fidelity | Right label for the wrong reason | Roughly fits, but unclear or unrelated mistake | Clearly shows the description | Clearly fits and is realistic/game-derived |
| Report Completeness | Scenario missing or label changed | All accounted for, but unverified lack details | All accounted; unverified include best attempt and loss | Level 3 plus specific failure reasons and attempt counts |

Run 001's puzzle-like `black_misses_mate` met Scenario Fidelity Level 3 but not Level 4, so it scored 3/4.

---

## 2. Version Ledger

| Version | Definition commit | Date | Evaluated by | Behavioral delta |
|---|---|---|---|---|
| 0.1.0 | `a617a9e` | 2026-10-23 | Run 001 | Baseline role, tools, write restriction, no label changes, stop on failure. PRD adds ranges/retries. |
| 0.2.0 | `e9df3bf` | 2026-10-23 | Run 002 | Added `WebFetch`, lichess-only real-game provenance, played-move requirement, network restriction, Lichess failure handling. |
| 0.3.0 | `d85e9c2` | 2026-11-01 | none | Post-run restructure of the PRD workflow. Did not participate in Run 001 or Run 002. |
| 0.3.1 | `e5a54fb` | 2026-11-02 | Run 002 (behavioral equivalence; no separate run) | Restores the 0.2.0 guarantees 0.3.0 dropped; adds the PRD Done-when gate; fixes the tools/write-access contradiction and stray backtick. No label, loss-range, retry, or output-schema change. |

**0.3.0 accounting:** 0.3.0 restated the PRD but dropped three 0.2.0 guarantees: the graded move must be the move actually played, the network is only for `lichess.org`, and Lichess is included in the failure stop condition. 0.3.1 restores all three.

**Why the submitted definition preserves the evaluated behavior:** v0.3.1 is a post-run consistency revision. It restores the v0.2.0 guarantees and adds only the PRD's already-binding "Done when" gate. It changes no label, loss-range, retry, scenario-selection, or output-schema rule. Its behavior is therefore the same as the v0.2.0 evaluated in Run 002; it was not separately run.

**Post-run note:** `docs/drift-report.md` later proposed dropping mandatory Lichess sourcing. That postdates Runs 001/002; if applied, log it as a separate revision.

---

## 3. Run 001

- **Run ID:** `136d239f-74cc-4e2a-8bc1-3a72bcb3ac0b` | **Date:** 10/23/2026
- **Definition used:** v0.1.0 `a617a9e` + PRD `14615fd` + rubric `0490393`
- **Run record:** `8d21c5e` — `chore(agent): complete Run 001 baseline evaluation...`
- **Prompt:** Build positions for `backend/tests/fixtures/scenarios.json`.
- **Cycle / review / cost:** 3m1s / 10m38s / 162.0k in, 1.2k out, $0.46
- **Changed files / test:** `positions.json` only / passed, engine tests ran
- **Scores:**
  - Verification Accuracy 4/4 — all positions passed; losses and labels reported.
  - Scenario Fidelity 3/4 — five positions from normal openings; `black_misses_mate` was puzzle-like. It showed the mate-in-one motive (Level 3) but was not game-derived (Level 4).
  - Report Completeness 4/4 — all six scenarios accounted for; no buckets changed.
- **Misfire / gap:** `black_misses_mate` was synthetic; the definition required the right label and loss but not real-game provenance or a played move.
- **Pass/Fail:** Pass

---

## 4. Run 002

- **Run ID:** `a5c7eb7c-7d94-424f-a292-1c02206dfd1b` | **Date:** 10/23/2026
- **Definition used:** v0.2.0 `e9df3bf` (the same commit contains the run record)
- **Fix:** Added WebFetch and real-game provenance instructions.
- **Prompt:** Same, restricted to `lichess.org`.
- **Cycle / review / cost:** 10m0s / 16m0s / 155.7k in, 1.5k out, $1.38
- **Changed files / test:** `positions.json` only / passed, engine tests ran
- **Scores:**
  - Verification Accuracy 4/4 — all positions passed; losses and labels reported.
  - Scenario Fidelity 4/4 — `black_misses_mate` replaced with a real-game line.
  - Report Completeness 4/4 — all six scenarios accounted for; no buckets changed.
- **Weak spot:** `e9df3bf` was committed at run completion, but the v0.2.0 working-tree definition (WebFetch plus the lichess-only prompt) was the input to the run. The clean pre-test commit example is the Run 001 baseline (`a617a9e` + `14615fd` + `0490393`).
- **Pass/Fail:** Pass

---

## 5. Comparison & Calibration

| Metric | Run 001 | Run 002 | Delta |
|---|---|---|---|
| Verification Accuracy | 4/4 | 4/4 | 0 |
| Scenario Fidelity | 3/4 | 4/4 | +1 |
| Report Completeness | 4/4 | 4/4 | 0 |
| Cycle time | 3m1s | 10m0s | +6m59s |
| Review latency | 10m38s | 16m0s | +5m22s |
| Tokens (in / out) | 162.0k / 1.2k | 155.7k / 1.5k | −6.3k / +0.3k |
| Cost | $0.46 | $1.38 | +$0.92 (3.0×) |
| Changed files | `positions.json` | `positions.json` | Same |
| Test gate | Pass | Pass | Same |

**Expected:** fidelity +1; verification and completeness unchanged; time and cost up from retrieval; only `positions.json` changed.

**Unexpected:** cost tripled while total tokens fell 3.7%. Effective cost per 1M tokens rose from $2.82 to $8.78, so the token counts do not explain the increase. Flag as an open calibration question for a future run (possible per-request or web-fetch billing). No quality or scope regressions.

**Calibration:** the rubric and threshold stay fixed for future runs.

---

## 6. Revision Diff (v0.1.0 → v0.2.0)

```diff
-tools: Read, Glob, Grep, Bash, Write
+tools: Read, Glob, Grep, Bash, Write, WebFetch

-You build verified chess test positions for ChessMind.
+You find verified chess test positions for ChessMind, taken from real games.
 Follow docs/prd-positions.md exactly.

 Always:
+- Use only positions from real games on lichess.org. Never invent or edit a position.
+- The graded move must be the move actually played in that game.
 - Write only backend/tests/fixtures/positions.json.
 - Never change a scenario's expected label to match what Stockfish returned.
+- Use the network only for lichess.org.
-- If Stockfish or the scenarios file isn't working, report it and stop.
+- If Stockfish, Lichess or the scenarios file isn't working, report it and stop.
```

The misfire was provenance, not classification. The test already passed. The diff adds only the tool access and provenance constraints needed to prevent a synthetic position from satisfying the label and loss checks.

---

## 7. Instruction Trace (v0.2.0 → v0.3.x)

| 0.2.0 rule | 0.3.0 | 0.3.1 |
|---|---|---|
| Real Lichess games; never invent/edit | L18 | Keep |
| Played move must be the actual game move | — | Restore |
| Write only `positions.json` | L29 | Keep |
| Never change expected label | L24 | Keep |
| Network only for `lichess.org` | — | Restore |
| Stop on Stockfish/Lichess/scenarios failure | L31 partial | Restore |
| Follow the PRD | L16–26 | Keep |

0.3.1 also adds the PRD Done-when test gate and fixes the tools/write-access contradiction. Label, loss-range, attempt, and output-schema rules are unchanged.

---

## 8. Evidence

```bash
git show -s --format='%h %ai %s' a617a9e 14615fd 0490393 8d21c5e e9df3bf d85e9c2 e5a54fb
git merge-base --is-ancestor a617a9e 8d21c5e && echo "baseline-before-run-001"
```

No credentials, `.env` files, or tokens are included. The only network permission is `WebFetch(domain:lichess.org)` in `settings.json`.
