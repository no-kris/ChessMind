# Testing Standards

Last reviewed: 2026-11-04
Maintained by: Kris Treska

These apply to all tests. The agent should consult this file before writing tests. Humans maintain it; the agent reads it and never edits it.

## Layout
- Tests live in `backend/tests/`, fixtures in `backend/tests/fixtures/`.
- One test file per module.
- Test names state the behavior: `test_illegal_move_returns_400`.

## Writing tests
- One behavior per test. Arrange, act, assert.
- Test the public interface, not private helpers.
- Use explicit expected values; never copy them from the implementation.
- No network calls in unit tests — mock the boundary.
- No `sleep`. Inputs and outputs must be deterministic.
- File writes go under `tmp_path`.
- Repeat cases with `@pytest.mark.parametrize`, not copy-paste.
- Stockfish tests use `@pytest.mark.engine`; live LLM tests use `@pytest.mark.llm`.
- Tests must pass without optional env vars unless they carry one of those marks.
- Assert on status codes and the key phrase of an error, not the whole string.
- API tests use FastAPI's `TestClient`.
- Shared fixtures go in `conftest.py`. Reset in-memory stores between tests.

## Coverage
- Every new endpoint or module gets one happy-path test and one failure test.
- Coverage runs may be judged against `docs/prd-testing.md` and
  `docs/rubric-testing.md`. Those files define the required report
  (per-file percentages, weakest area, blockers) and how it is scored.
  Use them for coverage audits; use this file when writing the tests themselves.

## Before committing
- `pytest` passes in `backend/`.
- `ruff check` passes in `backend/`.
- New behavior has a test, or the commit message says why not.
