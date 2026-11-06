# Decision 007 - Logging is configured on the "app" logger, level from LOG_LEVEL

**Date:** 2026-11-06
**Review by:** 2027-02-04
**Status:** Active. The user asked for the fix; the approach was chosen by the agent.

**Decision:** `backend/app/main.py` calls `configure_logging(os.getenv("LOG_LEVEL", "INFO"))` at import.
- It sets the level on the **`app` logger** (the parent of every `logging.getLogger(__name__)` in `app/…`) and adds one stderr `StreamHandler` with the format `"%(levelname)-8s %(name)s: %(message)s"`. It does **not** touch the root logger.
- `LOG_LEVEL` accepts DEBUG, INFO, WARNING, ERROR or CRITICAL, in any case. Any other value raises `ValueError` at startup naming the bad value; the app fails fast and never falls back silently.
- New modules need no setup. `logger = logging.getLogger(__name__)` under `app.` inherits this.

**Why (things you can't tell from the code):**
- **Before this fix, every `logger.info` in the app was silently dropped** under a real `uvicorn` run. uvicorn configures only its own `uvicorn.*` loggers, and Python's root logger defaults to WARNING. The coding standard "log every create, update and delete with the entity id" was written in the code but never displayed. Tests didn't notice, because they never looked at log output. This was found by starting a real server on 2026-11-06.
- **Don't switch to `logging.basicConfig`.** It silently does nothing if the root logger already has a handler. pytest attaches one while it imports test modules, so `basicConfig` would work under uvicorn and do nothing in tests (or the other way round, depending on import order).
- Not touching root avoids duplicate lines: uvicorn's loggers don't propagate to root, so each line prints once. If someone later adds a root handler, `app.*` lines will print twice. In that case set `logging.getLogger("app").propagate = False`.

**Tests:** `test_app_loggers_emit_info_after_startup` and `test_invalid_log_level_is_rejected_with_clear_message` in `tests/test_api.py`. `test_create_move_takeback_and_delete_are_logged_with_the_game_id` in `tests/test_game_store.py` uses `caplog`.

**Alternatives rejected:**
- `logging.basicConfig`, which is unreliable under pytest (see above).
- A uvicorn `--log-config` file. It adds a file and works only when started through uvicorn, not in tests or scripts.
- Configuring logging inside each module. That duplicates setup and invites conflicting formats.
