# Iteration Log

## 1. Pre-Test History

**The definition and rubric were committed before Run 001.**

- Agent v0.1.0: `a617a9e`, 2026-10-23 18:32:39
- PRD: `14615fd`, 2026-10-23 18:33:17
- Rubric: `0490393`, 2026-10-23 18:33:47
- Run 001 record: `8d21c5e`, 2026-10-23 19:14:13

The baseline and rubric were committed about 41 minutes before the Run 001 record. `8d21c5e` is the **run record**, not the definition commit.

**Complete definition at baseline:**

- Role, tools, write restrictions, stop rule: agent v0.1.0 L4–13.
- Workflow, loss ranges, retry limit, report: PRD L10–19.
- Failure handling: PRD L24.
- Pass gates: PRD L26–28; rubric L65–66.

**Baseline agent definition v0.1.0 (`a617a9e`, verbatim):**

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

Verification Accuracy:
- 1/4 — claims verified, but a scenario fails.
- 2/4 — claimed scenarios pass, but no evidence.
- 3/4 — every scenario passes; loss and label reported.
- 4/4 — losses match the test within 20 cp and each is shown inside its safe range.

Scenario Fidelity:
- 1/4 — right label for the wrong reason.
- 2/4 — roughly fits, but unclear or unrelated mistake.
- 3/4 — clearly shows the description.
- 4/4 — clearly fits and is realistic or game-derived.

Report Completeness:
- 1/4 — scenario missing or label changed.
- 2/4 — all accounted for, but unverified lack details.
- 3/4 — all accounted; unverified include best attempt and loss.
- 4/4 — Level 3 plus specific failure reasons and attempt counts.

Run 001's puzzle-like `black_misses_mate` met Scenario Fidelity Level 3 but not Level 4, so it scored 3/4.

---

## 2. Agent version history

- **0.1.0** (`a617a9e`, 2026-10-23) — evaluated by Run 001. Baseline role, tools, write restriction, no label changes, stop on failure. The PRD adds ranges and retries.
- **0.2.0** (`e9df3bf`, 2026-10-23) — evaluated by Run 002 and the current submitted definition. Added `WebFetch`, lichess real-game sourcing, played-move requirement, network restriction, and Lichess failure handling.

---

## 3. Run 001

- **Run ID:** `136d239f-74cc-4e2a-8bc1-3a72bcb3ac0b` | **Date:** 10/23/2026
- **Definition used:** v0.1.0 `a617a9e` + PRD `14615fd` + rubric `0490393`
- **Run record:** `8d21c5e` — `chore(agent): complete Run 001 baseline evaluation...`
- **Prompt:** Use the position-builder agent to build positions for backend/tests/fixtures/scenarios.json.
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
- **Fix:** Added WebFetch and real-game sourcing instructions.
- **Prompt:** Use the position-builder agent to build positions for backend/tests/fixtures/scenarios.json. You can only use lichess.org to look up cheess positions.
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

**Scores (Run 001 - Run 002):**
- Verification Accuracy: 4/4 - 4/4, no change.
- Scenario Fidelity: 3/4 - 4/4, +1.
- Report Completeness: 4/4 - 4/4, no change.

**Time and cost (Run 001 - Run 002):**
- Cycle time: 3m1s - 10m0s, +6m59s.
- Review latency: 10m38s - 16m0s, +5m22s.
- Tokens: 162.0k in / 1.2k out - 155.7k in / 1.5k out, −6.3k in and +0.3k out.
- Cost: $0.46 - $1.38, +$0.92 (3.0×).

**Scope (Run 001 - Run 002):**
- Changed files: `positions.json` in both runs.
- Test gate: pass in both runs.

**Expected:** fidelity +1; verification and completeness unchanged; time and cost up from lichess.org retrieval; only `positions.json` changed.

**Unexpected:** cost tripled while total tokens fell 3.7%. No quality or scope regressions.

**Calibration:** the rubric and threshold stay fixed for future runs.

---

## 6. Revision Diff (v0.1.0 - v0.2.0)

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

The misfire was sourcing, not classification. The test already passed. The diff adds only the tool access and sourcing constraints needed to prevent a synthetic position from satisfying the label and loss checks.

---

## 8. Version history

```text
a617a9e 2026-10-23 .claude/agents/position-builder.md: version 0.1.0 agent builds and verfies test positions for move scenarios.
14615fd 2026-10-23 docs/prd-positions.md: Create prd for position-builder agent.
0490393 2026-10-23 docs/rubric-positions.md: Create grading rubric for prd-positions.md.
8d21c5e 2026-10-23 chore(agent): complete Run 001 baseline evaluation for position-builder v0.1.0 Rubric Score: 11/12 (Scenario fidelity docked for synthetic puzzle position in black_misses_mate). Cost: $0.46 (162.0k in / 1.2k out).
e9df3bf 2026-10-23 fix(agent): grant lichess web-fetch access for v0.2.0 position-builder
```
