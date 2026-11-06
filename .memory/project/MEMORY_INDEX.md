# Project Memory Index

Last updated: 2026-11-06

## Active entries

- `decisions/decision-001.md` — Implement the fixes for drift
 report findings D1–D12 so the position-builder agent, PRD and
 rubric agree with each other and with the tests. Recorded 2026-11-03.
 Fixes committed 2026-11-04 (3cae3da); drift re-run still open.
 Review by 2027-02-01.

- `decisions/decision-002.md` — Keep test files in a separate
 `tests/` directory (e.g. `backend/tests/`), not alongside the
 source files. Recorded 2026-11-03. Review by 2027-02-01.

- `decisions/decision-004.md` — Game API contract: `/api/games`
 routes (incl. takeback), 201/200/204 success, 404 unknown game,
 400 bad FEN or move, 409 FEN mismatch or nothing to take back,
 UCI-only moves (castling normalised to e1g1), every error `detail` a
 string (422 included) reading "<operation> failed: <problem>", `move_id` = 0-based ply index, uuid4-hex game ids.
 Error rule: services raise domain errors and only routers map them
 to HTTP. Recorded 2026-11-05 (agent choice, unreviewed).
 Review by 2027-02-03.

- `decisions/decision-005.md` — The game store is a process-local
 dict. Requires one uvicorn worker and store methods that never
 `await` (no lock); handlers may await before calling the store. Memory grows without limit
 (no TTL). Singleton + dependency + conftest reset pattern for future
 caches. Recorded 2026-11-05 (agent choice, unreviewed).
 Review by 2027-02-03.

- `decisions/decision-006.md` — History has no gaps: a move whose
 canonical FEN isn't the game's current position gets 409; checks run
 404 → 400 → 409. The check is in `GameStore.append_move` (race-safe),
 and `Game.history` is a read-only tuple. `POST /api/games/{id}/takeback` removes one ply
 (409 if empty). `move_id` is reused after a takeback (risk for the
 Phase 5 "Why?" lookup); games start only from the standard position.
 User-confirmed 2026-11-06 (reversed the original trust-the-client
 choice). Review by 2027-02-04.

- `decisions/decision-007.md` — Logging: `main.py`'s
 `configure_logging` sets the `app` logger (not root) from `LOG_LEVEL`
 (default INFO; an invalid value fails at startup). Before this, all
 app INFO logs were silently dropped under uvicorn. Don't use
 `logging.basicConfig` (it does nothing under pytest). Recorded
 2026-11-06. Review by 2027-02-04.

- `../knowledge/coding-standards.md` — Coding standards
 for this project. Human-maintained, read-only.
 Last reviewed 2026-11-02.

- `../knowledge/testing-standards.md` — Testing standards
 for this project. Defines how tests should be written and what should be covered. Human-maintained, read-only.
 Last reviewed 2026-11-04.

- `../reference/REFERENCE_MEMORY_INDEX.md` — Keyword index of reference
 source material (docs, code, tests, fixtures, PRDs, rubrics, prior
 reports). Links only, read-only. Query by keyword; do not read
 every listed file. Last reviewed 2026-11-05.

## Archived entries

- `decisions/decision-003.md` — Phase 1 slice: in-memory game store
 and game/move/takeback endpoints. Completed and merged to `main`
 2026-11-06 (fast-forward to f7b8663; not pushed). Archived per the
 pruning rule (the branch merged). Still-relevant notes inside: PGN
 export was dropped by the user (do not re-add without asking); if
 ruff EXE002 reappears, `chmod 644` the files (they arrive as 777).
 Details now live in decisions 004–007.

## Pruning schedule

- Workflow-scoped entries: archived when the branch
 merges to main
- Project-scoped entries: reviewed every 90 days
