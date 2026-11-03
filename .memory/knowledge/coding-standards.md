# Coding Standards


Last reviewed: 2026-11-02
Maintained by: Kris Treska

These standards apply to all code in this project. The
agent should consult this file before writing or reviewing
any code. These rules are set by humans and the agent
should never modify this file.

## Python

- Every function and class has a docstring. One sentence: what it does and why.
- Use descriptive names. No single letters except loop counters (`i`, `j`) and coordinates (`x`, `y`).
- Constants are `UPPER_SNAKE_CASE`; private helpers start with `_`.
- Type hints on every function signature.
- Use `logger = logging.getLogger(__name__)`, never `print`.
- Log every create, update, and delete with the entity id and what changed.
- Error messages name the operation, the bad input, and what was expected — enough to diagnose without reading the code.
- No hardcoded paths. Read them from environment variables or a settings module.
- Never log secrets, API keys, or full request bodies.
- Stockfish tests use `@pytest.mark.engine`; live LLM tests use `@pytest.mark.llm`.

## TypeScript

- `strict` stays on; no `any` — use `unknown` and narrow it.
- Components are `PascalCase`, hooks start with `use`, everything else is `camelCase`.
- One component per file; the filename matches the component (`App.tsx` → `App`).
- Props are typed with a named `type` or `interface`, not an inline object.
- Keep components presentational. Put `fetch` calls in a hook or the parent component.
- Check `res.ok` before reading the body, and handle loading and error states in the UI.
- Never render raw error objects or API payloads to the user.
- No unused variables or imports.
- External imports first, then local imports.
- Event handlers are named `handleX` and declared with `const` or as functions inside the component.

## Before committing

- `ruff check` and `pytest` pass in `backend/`.
- `npm run build` passes in `frontend/`.
