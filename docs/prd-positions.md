# Position Builder Standard (PRD)

**Workflow**
- The agent builds a chess test position for each scenario in `backend/tests/fixtures/scenarios.json` and checks with Stockfish that it gets the expected move-quality label. 
- These positions are the test cases for Phase 4 (Evaluation Pipeline & Delta Classification) of `ai_chess_coach_project_plan.md`.

**Trigger**
- A developer asks the agent to build positions for the scenarios file.

**Steps**
All commands run from `backend/`. Paths below are from the repo root.
1. Read `backend/tests/fixtures/scenarios.json`. Each scenario has `id`, `side_to_move`, `description` and `expected_bucket`.
2. For each scenario, choose a position (FEN) and a move that fit the description. The FEN must be valid, with the right side to move, and the move must be legal. Positions may be constructed or taken from real games. Prefer realistic positions; if no realistic constructed position fits, the agent may take one from a real game on lichess.org.
3. Check it with Stockfish at depth 15 with `multipv=1` (matching the test), using `analyse` from `backend/app/services/engine.py` and `eval_loss` and `bucket` from `backend/app/services/classify.py`. It passes if the label matches `expected_bucket` and the loss is in the safe target range:
   - good: 10 or less
   - inaccuracy: 50–79
   - mistake: 120–279
   - blunder: 320 or more
4. If it doesn't pass, try a different position or move, up to 3 attempts in total. Never change `expected_bucket`. If it still fails, report it as unverified and move on.
5. Write the passing positions to `backend/tests/fixtures/positions.json`, one entry each: `id`, `fen`, `move` (UCI), `expected_bucket`, `loss_cp`. `loss_cp` is the loss measured in step 3; the test fails if it is more than 20 cp from what the test measures.
6. Report every scenario with its attempt count. Say which passed, and for each unverified one, the best attempt and its loss.

**Rules**
- Write only `positions.json`. Scratch scripts may go in `/tmp`.
- Don't edit `scenarios.json`, the test file, or anything in `backend/app/`, `docs/` or `.claude/`.
- Use the network only for lichess.org, and only for the step 2 fallback.
- If Stockfish won't start or the scenarios file can't be read, report it and stop. If lichess.org can't be reached, carry on with constructed positions.

**Done when**
- `positions.json` is the only file changed relative to the working tree at the start of the run (compare `git status` / `git diff --stat` before and after).
- `uv run pytest tests/test_classify_positions.py`, run from `backend/` with `STOCKFISH_PATH` set and the `engine` marker not deselected, passes.
- A run with any unverified scenario fails this gate, because the test requires a position for every scenario. That run is an honest fail: it is still graded on the rubric, but it does not pass.

**Out of scope**
- Tactical motif positions. These will be added once tactics detection exists.
