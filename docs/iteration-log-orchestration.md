# Iteration Log: TDD orchestration

## Run 2026-11-17: pin-detection service

**Task:** add `backend/app/services/tactics.py`, which returns every absolute
pin for both sides of a FEN. Service module only, run through the orchestrator.

**Agents:** orchestrator 1.1.0, planner 1.0.0, backend-tester 1.1.0,
endpoint-builder 1.1.0 and reviewer 1.1.0 (definitions from `e37a35c`).
Coordinator: Claude Code (`claude-opus-5-5`). Baseline: `main` at `c760f59`,
96 tests passing.

### What happened

- **Spec (3 versions):**
  - v1 defined `find_pins(fen) -> list[Pin]`, sorted by the pinned piece's
    square index. An invalid FEN raises `TacticsError`. The planner raised four
    questions for the human.
  - The human sent v1 back with two changes. Error messages drop the
    `find pins failed:` prefix, because the router adds it (decision-004).
    `Pin` gains `pinned_color` and `pinned_piece`.
  - The human sent v2 back to close coverage gaps. It added a pinned black
    bishop and a pinned queen and a check that the prefix is absent. It renamed
    one test and dropped a duplicate.
  - The human approved v3 as is, leaving three cosmetic leftovers. The
    coordinator confirmed both new FENs in python-chess.
- **Red:** the tester wrote `backend/tests/test_tactics.py` with 11 tests and
  27 cases. They cover:
  - pins along ranks, files and diagonals;
  - a pin by a queen;
  - positions that look like pins but aren't;
  - pins on both sides;
  - the empty result;
  - invalid FENs.

  The run exited with code 2 on `ModuleNotFoundError`. G1 passed.
- **Build (round 1 of 3):** the implementer wrote `tactics.py` (98 lines). For
  each king it scans the enemy bishops, rooks and queens on a matching line. It
  reports a pin when exactly one friendly piece stands between the king and
  that slider.
- **Green:** 123 passed: 27 new and 96 existing. G2 passed, with the test file
  identical to the red-proof copy. The coordinator re-ran the suite and got the
  same result.
- **Review:** pass, with no blocking findings. There were four test-gap
  findings (issue 1) and one note about the extra file the tester changed.

There were no permission denials. Nothing was committed. Run files are in
`docs/orchestrator-runs/pin-detection-2026-11-17/`.

### Matched design?

Mostly. The stages, gates and round budget all worked as designed. There were
three deviations:

- **Relayed approvals:** all H1 approvals reached the orchestrator through the
  coordinator.
- **Extra file:** the tester modified `docs/iteration-log-test-author.md`,
  which is outside the spec's files.
- **Weak red:** red was a single import error, so no individual assertion was
  shown failing.

### Issues and improvements

**Test gaps found after the tests froze.** The code is correct on each
   point, but the tests would miss a regression:
   - The sort order isn't pinned down.
   - Exception chaining isn't checked.
   - No case has a non-sliding piece behind a blocker.
   - No test checks that each call returns a new list.

## Run 2026-11-17: Phase 5 "Why?" endpoint (templated fallback)

**Task:** add `POST /api/coach/explain` (`{game_id, move_id}` →
`{verdict, praise, concern, tip}`), built only from templates. No LLM, no
`openai`, no cache. Run through the orchestrator.

**Agents:** orchestrator 1.1.0, planner 1.0.0, backend-tester 1.1.0,
endpoint-builder 1.1.0 and reviewer 1.1.0 (definitions from `e37a35c`).
Coordinator: Claude Code (`claude-opus-5-5`). Baseline: `feat/pin-detection`
at `8fb58d1`, 123 tests passing.

### What happened

- **Spec (1 version):** 200 / 422 / 404 (game or move) / 503 (engine down).
  The engine runs on demand and is faked in tests. The planner raised six
  questions. The human approved v1 and kept every default. For Q1, the
  coordinator adds the two `main.py` router lines, because the implementer
  can't edit existing files.
- **Red:** the tester wrote 3 files with 100 cases. Exit code 1: 100 failed,
  123 passed. The service tests failed on `ModuleNotFoundError` and the API
  tests on 404s and assertions, with no import errors (`main.py` was left
  unchanged on purpose). G1 passed.
- **Build (round 1 of 3):** the implementer wrote 3 new files (295 lines).
  The run then paused so the coordinator could add the `main.py` lines.
- **Green:** 223 passed. G2 passed, with the test files' sha256 unchanged.
  The coordinator re-ran the suite and got the same result.
- **Review:** pass, with four non-blocking notes, all logged in `review.md`.

There was one permission denial (see below). Nothing was committed. The H1
answers are in memory `decision-011`. Run files are in
`docs/orchestrator-runs/coach-explain-2026-11-17/`.

### Matched design?

Mostly. There were four deviations:

- **Relayed approvals:** all H1 answers came through the coordinator.
- **Production edit outside the implementer:** the coordinator edited
  `main.py`, which needed a pause between build and green.
- **G2 check by a different agent:** the tester couldn't read red-proof.md because it was too large, so a read-only agent compared the files instead.
- **Extra file:** the tester modified `docs/iteration-log-test-author.md`
  again.

### Issues and improvements

- **The tester can't read a large red-proof.md.** The file is 53 KB, and
  reading the overflow file was denied ("Path escapes the project root").
  Record sha256 values in red-proof.md, or give the tester a hash tool.
- **Router wiring needs `main.py`.** Either allow the implementer a narrow
  edit there, or write the pause-for-human step into the contract.
