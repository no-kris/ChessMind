# 1. Quality Rubric

## 1.1 Dimensions

### 1.1.1 Verification Accuracy
- Measures whether the agent's report matches what the test actually finds. A high score requires every scenario the agent calls verified to pass `test_classify_positions.py`, with losses close to what the test measures.

### Scoring Guide
1. Does not meet – The agent claims scenarios are verified, but one or more fail the test.

- Level 1 example: Agent output reads: "All 6 scenarios verified." The test shows `white_passive_move` grading as "mistake" with a loss of 140.

2. Partially meets – Every claimed scenario passes, but the report gives no evidence of how it was checked.

- Level 2 example: Agent output reads: "Built 6 positions; they should all work." No losses or labels are reported.

3. Meets – Every claimed scenario passes, and the report gives each one's measured loss and label.

- Level 3 example: Agent output reads: "white_hangs_queen: loss 845, blunder. black_opening_reply: loss 4, good."

4. Exceeds – Every claimed scenario passes, losses match the test's measurements, and the report shows each loss is inside its safe range.

- Level 4 example: Agent output reads: "black_loses_pawn: loss 165, mistake (safe range 120–279)." The test measures the same 165.

### 1.1.2 Scenario Fidelity
- Measures whether each position actually shows what its scenario describes, not just the right label. Checked by reviewing positions.json (for example, on a board viewer).

### Scoring Guide
1. Does not meet – One or more positions get the right label for a different reason than the description.

- Level 1 example: `white_hangs_queen` is a blunder because White hangs a rook; the queen isn't involved.

2. Partially meets – Positions roughly fit their descriptions, but some are unclear or rely on an unrelated mistake.

- Level 2 example: `black_misses_mate` has a mate in one available, but the played move also hangs a piece, so it's unclear which caused the blunder.

3. Meets – Every position clearly shows what its description says.

- Level 3 example: In `white_hangs_queen`, the queen moves to a square where it is captured for free, and nothing else is lost.

4. Exceeds – Every position clearly fits, and the positions are realistic and easy to follow (reached from normal play, few unusual pieces).

- Level 4 example: `black_loses_pawn` comes from a standard opening after 6 moves, and the lost pawn is obvious at a glance.

### 1.1.3 Report Completeness
- Measures whether the final report gives a full, honest picture of the run, including any scenarios it couldn't verify.

### Scoring Guide
1. Does not meet – A scenario is missing from both positions.json and the report, or a label was changed to match Stockfish.

- Level 1 example: The report lists 5 scenarios; `white_passive_move` is never mentioned.

2. Partially meets – Every scenario is accounted for, but unverified ones have no details.

- Level 2 example: Agent output reads: "white_passive_move: couldn't verify." No attempts or losses are given.

3. Meets – Every scenario is accounted for. Unverified ones include the best attempt and its loss.

- Level 3 example: Agent output reads: "white_passive_move: unverified after 3 attempts; best loss 112 (mistake)."

4. Exceeds – Everything in Level 3, plus a specific reason for each failure and attempt counts for every scenario.

- Level 4 example: Agent output reads: "white_passive_move: unverified, 3 attempts. Every passive move I tried lost 110–150 because they also gave up the center. 5 others verified on the first attempt."

**Pass threshold:**
- A run passes if it scores 3 or higher on all three dimensions, and the PRD's pass/fail gates are met: positions.json is the only changed file, and `test_classify_positions.py` passes with the engine tests actually running.
- Reasoning: Verification Accuracy and Scenario Fidelity together decide whether the positions can be trusted for Phase 4. Report Completeness makes sure failures are visible instead of hidden. A dimension floor stops a strong report from covering for positions that test the wrong thing.

**Notes on Threshold Design:**
- Considered an aggregate minimum (9/12). Ruled out because a run scoring 1 on Scenario Fidelity (right labels, wrong situations) could still pass, and those positions wouldn't actually test the Phase 4 cases.
