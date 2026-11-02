# ChessMind Repository Summary

ChessMind is an early-stage AI chess coach. The plan is a React board UI, a FastAPI backend that runs Stockfish to grade moves (good / inaccuracy / mistake / blunder), and an on-demand LLM "Why?" explanation layer. By design it keeps no state between sessions: there are no accounts and no database. The full roadmap is in `ai_chess_coach_project_plan.md`. Only Phase 1 setup is checked off, but the classification logic from Phase 4 and the Stockfish wrapper from Phase 2 have already been built.

The repo also serves as a workspace for Claude Code agent workflows. Many of its files are PRDs, rubrics and iteration logs for agents that maintain the project.

## Top-level layout

```
.
├── backend/                  FastAPI + python-chess + Stockfish (Python 3.13, uv)
├── frontend/                 React 19 + Vite + react-chessboard (TypeScript)
├── docs/                     Agent workflow PRDs, rubrics, iteration logs, reports
├── .claude/agents/           Custom Claude Code subagents
├── Dockerfile                Dev container (Python 3.13, Node 22, uv, Stockfish, Claude Code)
├── docker-entrypoint.sh      Restores/persists Claude Code login via the claude-auth volume
├── settings.json             Claude Code settings copied into the image (status line, permissions)
├── statusline.sh             Claude Code status line script
├── README.md                 Docker dev setup, env vars, test and lint commands
├── setup.md                  Agent sandbox setup guide (untracked)
├── session_tasks.md          Task briefs for parallel worktree sessions (e.g. feature/classify)
└── ai_chess_coach_project_plan.md   Architecture and phased implementation roadmap
```

## Backend (`backend/`)

| Path | Purpose |
| --- | --- |
| `app/main.py` | FastAPI app. Loads `.env`, sets CORS from `CORS_ORIGINS` (default `http://localhost:5173`), mounts the router, `GET /` health message. |
| `app/api/routes.py` | `/api` router. Currently only a placeholder `GET /api/analyze`. |
| `app/services/engine.py` | Async Stockfish wrapper. `open_engine()` launches the binary at `STOCKFISH_PATH`. `analyse()` returns the top-N lines (`score_cp`, `pv`) from the side to move's point of view, with depth capped at 18, mates mapped to ±10000 cp, and an asyncio lock around calls. |
| `app/services/classify.py` | Pure math. `eval_loss(best_cp, result_cp)` gives the loss after negating the opponent-perspective score, floored at 0. `bucket(delta)` maps it to <30 good, <100 inaccuracy, <300 mistake, else blunder. |
| `tests/test_api.py` | Tests the API endpoints with the FastAPI test client. |
| `tests/test_classify.py` | Boundary and perspective unit tests for `classify.py`. |
| `tests/test_engine.py` | Engine tests (pytest marker `engine`, needs Stockfish). |
| `tests/test_classify_positions.py` | End-to-end check that real positions get the expected label from Stockfish. |
| `tests/fixtures/scenarios.json`, `positions.json` | 6 move-quality scenarios and the 6 matching verified positions, built by the `position-builder` agent. |
| `pyproject.toml` / `uv.lock` | Runtime deps: fastapi, python-chess, openai, python-dotenv, uvicorn. Dev deps: pytest, pytest-cov, httpx, ruff. Pytest markers: `engine`, `llm`. |

## Frontend (`frontend/`)

This is a minimal Vite + React 19 + TypeScript app. `src/App.tsx` renders a `react-chessboard` board and a "Coach" side panel. Its Analyze button calls `/api/analyze`. `vite.config.ts` proxies `/api` to `http://localhost:8000`. Linting uses `oxlint`, and `npm run build` runs `tsc -b && vite build`.

## Agent tooling

- **`.claude/agents/position-builder.md`** finds chess positions from real Lichess games and checks them with Stockfish for `scenarios.json`. Its spec is `docs/prd-positions.md` and `docs/rubric-positions.md`. Its version history and pre-test baseline are recorded in `docs/iteration-log-positions.md`.
- **`.claude/agents/drift-investigator.md`** reports where docs and code disagree and does not edit anything. Its spec is `docs/prd-drift-investigation.md` and `docs/rubric-drift-investigation.md`.
- **`docs/`** holds the rest of the agent material:
  - **Standards:** each one has a PRD and a rubric, and four of them have an iteration log. They cover drift, lint (`ruff`), positions, and testing/coverage.
  - **Reports:** `drift-report.md`, `drift-report-verification.md` and `handoff-drift-positions.md` are the October 2026 drift investigation of the position-builder.
  - **Process notes:** `context-management-techniques.md`, `memory-architecture.md` and `pre-session-plan.md`.
- **`settings.json`** allows WebFetch to `lichess.org`. It blocks reading or editing `.env` files, running `env`/`printenv`, and editing lockfiles.

## Dev workflow

1. `docker build -t chessmind .`, then `docker run` with the repo mounted at `/workspace`. Named volumes hold the Claude auth, `node_modules` and the venv at `/opt/venv`. Ports 8000 and 5173 are published.
2. On start, the container runs `uv sync`, and runs `npm ci` only if the lockfile changed.
3. Backend: `cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`. The README omits `--host`.
4. Frontend: `cd frontend && npm run dev`.
5. Tests: `cd backend && uv run pytest`. Lint: `uv run ruff check .` for the backend, and `npm run lint` / `npm run build` for the frontend.

## Current state

- **Built:** the scaffolding, Docker dev environment, Stockfish analysis wrapper, move classification and its tests, and verified fixture positions.
- **Not built yet:** the real move/analysis endpoints, the session game store, the evaluation cache, tactical motif detection (pins, forks, files), the LLM `POST /api/coach/explain` endpoint, and a frontend beyond the placeholder.
- **Working tree:** many files have uncommitted changes across the backend, tests, docs and Docker files, and `setup.md` is untracked.
