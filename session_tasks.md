## Session A

Branch name: feature/classify

Worktree directory: ChessMind-classify (mounted as /workspace in the container)

Task:
Write two small functions that grade how good a chess move was, plus tests for them.

1. backend/app/services/classify.py (plain math only, no FastAPI or chess.engine imports)
   - eval_loss(best_cp, result_cp): how much the players postion worsens or improves after a move (measure in centipawns).
     - best_cp: score before the move, from the moving player's point of view.
     - result_cp: score after the move, from the opponent's point of view.
     - Formula: max(0, best_cp - (-result_cp)). Never negative.
   - bucket(delta): turns the loss into a label:
       under 30    = "good"
       30 to 99    = "inaccuracy"
       100 to 299  = "mistake"
       300 or more = "blunder"

2. backend/tests/test_classify.py
   - Label boundaries (use pytest.mark.parametrize):
     29 = "good", 30 = "inaccuracy", 99 = "inaccuracy",
     100 - 299 = "mistake", 300 = "blunder"
   - Best move loses nothing: eval_loss(50, -50) == 0
   - Score flips to the right side: eval_loss(100, 200) == 300
   - Missing a checkmate is a blunder: bucket(eval_loss(10000, 0)) == "blunder"
   - Loss is never negative: eval_loss(50, -60) == 0

Files or folders the agent may write to:
- backend/app/services/classify.py 
- backend/tests/test_classify.py 

Files or folders the agent may read but not write to:
- ai_chess_coach_project_plan.md
- backend/pyproject.toml
- backend/app/ (all existing files)

Commands the agent may run:
- uv run pytest tests/test_classify.py
- uv run pytest (full suite)
- uv run ruff check, on its own files only

Definition of done:
- Only the two files above were created; nothing else changed
- uv run pytest passes, including any pre-existing tests.
- The expected values in the tests match the task exactly.
- The agent ends with a short summary of what it did.

## Session B

Branch name: feature/engine

Worktree directory: ChessMind-engine (mounted as /workspace in the container)

Task:
Write a small helper that talks to the Stockfish chess engine, plus tests for it.

1. backend/app/services/engine.py
   - open_engine(): starts Stockfish and returns it.
     - The path to Stockfish is in the STOCKFISH_PATH environment variable.
     - Use python-chess's async version: chess.engine.popen_uci.
   - analyse(engine, board, depth=15, multipv=3): asks Stockfish for its top moves.
     - Never search deeper than 18, even if asked to.
     - Only one analysis at a time (use an asyncio.Lock).
     - Return one entry per line, like: {"score_cp": 35, "pv": ["e2e4", "e7e5", ...]}
     - score_cp is from the point of view of the player whose turn it is

2. backend/tests/test_engine.py (mark both tests @pytest.mark.engine and @pytest.mark.anyio)
   - Starting position: returns 3 lines, every score between -100 and 100,
     every line has at least one move.
   - Mate-in-one position (choose one and check it's legal):
     the best line's score is 9000 or higher.
   - Always close the engine at the end of each test.

Files or folders the agent may write to:
- backend/app/services/engine.py 
- backend/tests/test_engine.py 

Files or folders the agent may read but not write to:
- ai_chess_coach_project_plan.md
- backend/pyproject.toml
- backend/app/ (all existing files)

Commands the agent may run:
- uv run pytest tests/test_engine.py
- uv run pytest (full suite)
- uv run ruff check, on its own files only
- stockfish (to check the engine runs; quit right after)

Definition of done:
- Only the two files above were created; nothing else changed
- uv run pytest passes, including any pre-existing tests.
- analyse uses .pov(board.turn) and caps depth at 18.
- Every test closes the engine (no leftover Stockfish processes: check with ps).
- The agent ends with a short summary of what it did.
