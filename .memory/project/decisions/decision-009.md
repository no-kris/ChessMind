# Decision 009 - The verifier is an agent that runs commands through test_runner

**Date:** 2026-11-17
**Review by:** 2027-02-15
**Status:** Active. User-confirmed 2026-11-17 ("go ahead with the verifier agent").

**Decision:** Stage 10 of the TDD orchestration run is a `verifier` subagent
(`.claude/agents/verifier.md`), spawned by the orchestrator through `Task`.
- Tools: `file_read`, `git_status`, `test_runner` only. No write tools, no
  shell, no `Skill`. It returns its report and the orchestrator writes it
  into `log.md`.
- MCP role `verifier` is on the allow-list for those three tools.
- Frontend checks use `test_runner` with `suite: "verify"`, which runs the
  fixed `npm run lint` + `npm run build` (added to `mcp/tools_server.py`).
- Routing (user-confirmed 2026-11-17, "route BLOCKED and PENDING to the
  human"): FAIL goes to the implementer and uses a round from the shared
  budget (decision-008). BLOCKED or PENDING goes to the human with the exact
  error and stops the run; it uses no round. PASS requires nothing BLOCKED
  or PENDING.
- The rules stay in `.claude/skills/verifier/SKILL.md`. The agent reads that
  file instead of repeating it, and humans keep `/verifier` as a pre-commit
  check in a normal session.

**Why (things you can't tell from the code):**
- A skill runs with the caller's tools. The orchestrator has no `Skill`, no
  shell and no `test_runner`, so the skill could not run in a pipeline run.
- Giving the orchestrator a shell would break its "never does the work" rule.
  Putting the skill on the reviewer would mix spec judgment with mechanical
  checks, and the reviewer has no execution tools either.
- `test_runner`'s default frontend suite runs `npm test`, and
  `frontend/package.json` has no `test` script, so it always fails. Hence the
  separate `verify` suite.
- For backend-only runs, the verifier repeats the tester's green run (same
  `test_runner` commands, and the reviewer changes no code in between). Its
  value there is an independent second run; the frontend checks are new
  coverage.

**Alternatives rejected:** `Skill` plus a shell on the orchestrator; the skill
on the reviewer; folding verification into the tester's green stage
(loses the independent final check); giving the verifier `Bash` (can't
enforce "no extra flags", and Bash can write files).
