# Decision 005 - Game store runs in one process with async handlers and no lock

**Date:** 2026-11-05
**Review by:** 2027-02-03
**Status:** Active. Chosen by the agent while implementing [decision-003](decision-003.md); not yet reviewed by the user.

**Decision:** The session game store (`app/services/game_store.py`) is a plain dict on a module-level `GameStore` singleton. It is safe only under these constraints:

1. **Exactly one server worker process.** Never start uvicorn with `--workers N>1`, and never use gunicorn with several workers. Each process would have its own store, so a game created through one worker would 404 on the others. As of 2026-11-05 the only launch command is the one in README.md (`uv run uvicorn app.main:app --reload ...`), run by hand inside the container, and it uses one process. The Dockerfile `CMD` starts only a shell, so nothing launches the server automatically.
2. **Game handlers stay `async def`, and store methods stay synchronous with no `await`.** Everything then runs on one event loop, and a read followed by a write cannot interleave. That is why there is no lock. This also covers the no-gaps check ([decision-006](decision-006.md)). Since 2026-11-06 that check runs inside `GameStore.append_move`, in the same synchronous call as the append. Handlers may therefore `await` (e.g. an engine call) before calling `append_move`, and a race is rejected with 409. **The rule that must not break: store methods never `await`.** An `await` inside `append_move` would reopen the race; `test_two_requests_racing_from_the_same_position_record_only_one_move` guards it. If a handler becomes plain `def`, FastAPI runs it in a thread pool, and the store then needs a `threading.Lock`. The same applies if a store method gains an `await`, for example once Phase 2 adds engine calls.
3. **Access goes through the `get_game_store` FastAPI dependency.** Tests reset the singleton with the autouse `reset_game_store` fixture in `backend/tests/conftest.py`, as the testing standards require ("Reset in-memory stores between tests"). New in-memory stores, such as the Phase 2 evaluation cache or the Phase 5 LLM cache, should follow the same pattern: a singleton, a dependency getter and a conftest reset.

**Known consequences (accepted for now):**
- `uvicorn --reload` restarts the process on every code save and wipes all games. This is expected in development, not a bug.
- **Memory grows without limit.** There is no cap, TTL or idle eviction. A game is removed only by `DELETE /api/games/{id}` or a restart. The plan says games are "dropped when the session ends", but the server has no session-end signal yet; the frontend would have to call DELETE. Revisit before any shared deployment: add a cap, an idle TTL, or both.

**Rationale:** Decision-003 rules out a database, and the plan wants state cleared on restart. A dict needs no dependencies, and the async-only rule avoids locking.

**Alternatives rejected:**
- Redis or another shared store, which would allow several workers. It contradicts "nothing persisted" and adds infrastructure.
- An `asyncio.Lock` around store calls. It isn't needed while the methods have no awaits.
