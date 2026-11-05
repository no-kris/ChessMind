# Reference Index

Last updated: 2026-11-05

Source material used as evidence. Entries link to the original
files and never copy them. All paths are relative to the repo root.
Search by keyword and read only the files the current task points
to. Do not read every file listed here.

## Product and roadmap

- `ai_chess_coach_project_plan.md`: Full implementation plan.
 Covers the tech stack, Phases 1–6 and the data flow. The app is
 session-only and keeps no state.
 Keywords: roadmap, phases, architecture, stockfish, llm, why, stateless

- `agent-summary.md`: Repository summary covering layout, current
 build state and agent workflows.
 Keywords: overview, layout, status, orientation

- `README.md`: Docker development setup and the documented
 commands.
 Keywords: setup, docker, commands, lint, test

## Backend code

- `backend/app/main.py`: FastAPI app entry point and the root
 endpoint.
 Keywords: fastapi, app, startup, endpoint

- `backend/app/api/routes.py`: API router with the `/analyze`
 endpoint.
 Keywords: api, routes, endpoints, analyze

- `backend/app/services/engine.py`: Stockfish wrapper
 (`open_engine`, `analyse`).
 Keywords: stockfish, engine, uci, evaluation, STOCKFISH_PATH

- `backend/app/services/classify.py`: Move-quality classification
 (`eval_loss`, `bucket`).
 Keywords: classify, centipawn, delta, good, inaccuracy, mistake, blunder

- `backend/pyproject.toml`: Backend dependencies and tool config.
 Keywords: dependencies, uv, ruff, pytest, config

## Backend tests and fixtures

- `backend/tests/test_api.py`: API endpoint tests.
 Keywords: tests, api, routes

- `backend/tests/test_engine.py`: Stockfish wrapper tests.
 Keywords: tests, engine, stockfish

- `backend/tests/test_classify.py`: Unit tests for classification.
 Keywords: tests, classify, buckets, thresholds

- `backend/tests/test_classify_positions.py`: Position-based
 classification tests that use the fixtures.
 Keywords: tests, positions, fixtures, fen

- `backend/tests/fixtures/scenarios.json`: Move-quality scenarios
 that the position-builder targets.
 Keywords: fixtures, scenarios, labels

- `backend/tests/fixtures/positions.json`: Built and verified test
 positions.
 Keywords: fixtures, positions, fen, lichess

## Frontend

- `frontend/src/App.tsx`, `frontend/src/main.tsx`: React app
 scaffold.
 Keywords: react, frontend, ui, board

- `frontend/package.json`, `frontend/vite.config.ts`: Frontend
 dependencies and build config.
 Keywords: vite, npm, build, oxlint

## Environment and config

- `Dockerfile`, `docker-compose.yml`, `docker-entrypoint.sh`:
 Container build and runtime.
 Keywords: docker, container, environment, entrypoint

- `setup.md`: Agent sandbox setup guide.
 Keywords: sandbox, docker, setup, agents

## Agent definitions

- `.claude/agents/drift-investigator.md`: Drift-investigator agent
 (v0.1.0).
 Keywords: agent, drift, investigation, docs vs code

- `.claude/agents/position-builder.md`: Position-builder agent
 (v0.4.0).
 Keywords: agent, positions, scenarios, stockfish, lichess

- `.claude/hooks/protect-memory.sh`: PreToolUse hook that keeps
 `.memory/knowledge` and `.memory/reference` read-only.
 Keywords: hook, memory, read-only, protection

## Workflow standards (PRDs and rubrics)

- `docs/prd-drift-investigation.md`, `docs/rubric-drift-investigation.md`:
 Drift investigation standard.
 Keywords: prd, rubric, drift

- `docs/prd-positions.md`, `docs/rubric-positions.md`: Position
 builder standard.
 Keywords: prd, rubric, positions

- `docs/prd-testing.md`, `docs/rubric-testing.md`: Backend test
 coverage standard.
 Keywords: prd, rubric, testing, coverage

- `docs/prd-lint.md`, `docs/rubric-lint.md`: Lint standard.
 Keywords: prd, rubric, lint, ruff

- `docs/prd-memory.md`, `docs/rubric-memory.md`: Memory recall and
 resumption standard.
 Keywords: prd, rubric, memory, recall, resume

## Design notes and plans

- `docs/memory-architecture.md`: Three-layer memory design, with
 what belongs in each layer and the pruning policies.
 Keywords: memory, layers, architecture, pruning

- `docs/context-management-techniques.md`: Context boundary plan
 for the multi-phase runs.
 Keywords: context, boundaries, phases

- `docs/pre-session-plan.md`: Plan for testing the
 drift-investigator on the position-builder.
 Keywords: plan, drift, position-builder

- `session_tasks.md`: Parallel worktree session log for the
 classify and engine branches.
 Keywords: worktrees, parallel, classify, engine

## Prior reports and run history

- `docs/drift-report.md`: Drift report dated 2026-11-01 comparing
 the position-builder agent, PRD and rubric (findings D1–D12).
 Linked from decision-001.
 Keywords: drift, findings, position-builder, D1-D12

- `docs/handoff-drift-positions.md`: Handoff from drift run 2 on
 the position-builder.
 Keywords: handoff, drift, positions

- `docs/iteration-log-drift.md`, `docs/iteration-log-positions.md`,
 `docs/iteration-log-testing.md`, `docs/iteration-log-lint.md`,
 `docs/iteration-log-memory.md`: Per-run logs for each workflow
 standard.
 Keywords: iteration, runs, scores, history

## Excluded

These are never indexed:

- Lockfiles and vendored or generated files (`backend/uv.lock`,
 `frontend/package-lock.json`, `node_modules`, caches)
- Secrets and environment files
- `.memory/` itself. Project memory and knowledge have their own
 index.

## Pruning

- Drop an entry when its file is moved or deleted, or is no longer
 relevant.
- Keep an old report only while it still informs an open decision.
- Review this index whenever files are added to or removed from
 `docs/`.
