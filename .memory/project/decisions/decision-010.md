# Decision 010 - coursetools runs one server per role; role fixed at launch

**Date:** 2026-11-17
**Review by:** 2027-02-15
**Status:** Active. User-requested 2026-11-17 ("fix the self-declared role gap"); design chosen by the agent.

**Decision:**
- `.mcp.json` registers six servers, `coursetools_<role>` for orchestrator,
  planner, tester, implementer, reviewer and verifier. Each runs
  `mcp/tools_server.py` with `COURSETOOLS_ROLE=<role>`.
- No tool takes a `role` argument. The server refuses to start without a
  known role. Each agent's frontmatter grants only
  `mcp__coursetools_<own role>__*`.
- `file_write` is limited per role by `mcp/write_scopes.json`, with modes
  `write`, `create` (green reports) and `untracked` (new test and app files;
  git-tracked files are read-only, and a git error refuses the write).
- `mcp` is pinned `>=1.2,<2`.

**Why (things you can't tell from the code):**
- Before this, every tool took a `role` argument and the server trusted it,
  so any agent could claim another role, including its write scopes.
  Subagents share the session's MCP connections, so a single server can't
  tell callers apart. One process per role makes Claude Code's tool grants
  decide the role.
- `mcp` 2.x renamed `FastMCP`, and the server fails on import without the
  pin.
- The `untracked` mode exists because a create-only rule would block the
  implementer from revising its own files in loop rounds.

**Limits:** The human's main session sees all six servers and can call any of
them. Only subagents are restricted. Freezing `red-proof.md` after G1 and
"current run only" are still instructions.

**Alternatives rejected:** Keeping the `role` argument and checking it
against a token (agents could still read and reuse it); one server with
per-call identity (Claude Code doesn't tell MCP servers which subagent is
calling).
