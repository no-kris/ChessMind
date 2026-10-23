# Position Builder Standard (PRD)

**Workflow**
- The agent builds a chess test position for each scenario in `backend/tests/fixtures/scenarios.json` and checks with Stockfish that it gets the expected move-quality label. 

**Trigger**
- A developer asks the agent to build positions for the scenarios file.

**Steps**
1. Read `scenarios.json`. Each scenario has `id`, `side_to_move`, `description` and `expected_bucket`.
2. For each scenario, choose a position (FEN) and a move that fit the description. The FEN must be valid, with the right side to move, and the move must be legal.
3. Check it with Stockfish at depth 15, using `analyse` from `app/services/engine.py` and `eval_loss` and `bucket` from `app/services/classify.py`. It passes if the label matches `expected_bucket` and the loss is in the safe target range:
   - good: 10 or less
   - inaccuracy: 50–79
   - mistake: 120–279
   - blunder: 320 or more
4. If it doesn't pass, try a different position or move, up to 3 attempts. Never change `expected_bucket`. If it still fails, report it as unverified and move on.
5. Write the passing positions to `backend/tests/fixtures/positions.json`, one entry each: `id`, `fen`, `move` (UCI), `expected_bucket`, `loss_cp`.
6. Report which scenarios passed, and for each unverified one, the best attempt and its loss.

**Rules**
- Write only `positions.json`. Scratch scripts may go in `/tmp`.
- Don't edit `scenarios.json`, the test file, or anything in `backend/app/`, `docs/` or `.claude/`.
- If Stockfish won't start or the scenarios file can't be read, report it and stop.

**Done when**
- `positions.json` is the only changed file.
- `uv run pytest tests/test_classify_positions.py` passes, with the engine tests actually running, not skipped.

**Out of scope**
- Tactical motif positions. These will be added once tactics detection exists.
