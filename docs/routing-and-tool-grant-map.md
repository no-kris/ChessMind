# Routing and Tool-Grant Map

The routing and permission contract for the TDD orchestration workflow. The
orchestrator agent (`.claude/agents/orchestrator.md`) names this file as its
full contract. For the visual flow, see
[orchestration-diagram.md](orchestration-diagram.md).

Sources: the five agent files in `.claude/agents/`, `mcp/tools_server.py`,
`mcp/roles.allowlist.json`, `mcp/write_scopes.json`. Last updated: 2026-11-17.

---

## 1. Roles

| Pipeline role | Agent file | MCP server (role) | Invoked by | Writes |
|---------------|-----------|------------------|------------|--------|
| Orchestrator | `orchestrator.md` | `coursetools_orchestrator` | Human | `docs/orchestrator-runs/<run-id>/log.md` only |
| Planner | `planner.md` | `coursetools_planner` | Orchestrator (first) | `docs/orchestrator-runs/<run-id>/spec.md` only |
| Tester | `backend-tester.md` | `coursetools_tester` | Orchestrator (twice: red, green) | New files under `backend/tests/`, `red-proof.md`, `green-report-round-<N>.md`, its log |
| Implementer | `endpoint-builder.md` | `coursetools_implementer` | Orchestrator (after G1) | New files under `backend/app/api/**`, new modules under `backend/app/services/`, `docs/orchestrator-runs/<run-id>/implementer-log.md` |
| Reviewer | `reviewer.md` | `coursetools_reviewer` | Orchestrator (after G2) | `docs/orchestrator-runs/<run-id>/review.md` only |

Each role has its own server process, started with that role in
`COURSETOOLS_ROLE` (§3, "Server registration"). An agent is granted only its
own server's tools, so the role a call runs as is fixed by the agent's grants,
not by anything the agent says. Each agent's "MCP role" section names its
server.

Every role can also be invoked directly by a human for standalone work
(standalone spec, coverage work, feature build, or review).

There is no verifier stage and no lint requirement (removed 2026-11-17, see
decision-009). The tester's green run is the only execution check: pytest,
plus `npm run build` when frontend files changed.

---

## 2. Routing table

| From | Condition | Route to | Payload |
|------|-----------|----------|---------|
| Human | New goal | Orchestrator | Goal text + context |
| Orchestrator | Run dir + baseline recorded | Planner | Goal, run-id, repo path |
| Planner | `spec.md` written | **Human (H1)** | `spec.md` |
| Human | Spec rejected | Planner | Human's notes |
| Human | Spec approved | Tester (red) | run-id, `spec.md` path |
| Tester (red) | Proof missing/vague | Tester (red) | The specific gap + rubric dimension |
| Tester (red) | No red proof possible | **Human, STOP** | Log entry |
| Tester (red) | G1 passes | Implementer | run-id, `spec.md`, `red-proof.md`, failing test path |
| Implementer | Files written | Tester (green) | run-id, `spec.md`, `red-proof.md` path, round number |
| Tester (green) | Report incomplete | Tester (green) | The specific gap |
| Tester (green) | Test file changed | **Hard fail → Human** | Log entry |
| Tester (green) | Still red, test files unchanged, round < 3 | Implementer | Failing output **verbatim** |
| Tester (green) | Still red, round 3 | **Human, STOP** | Failing output + accumulated findings |
| Tester (green) | G2 passes | Reviewer | run-id, `spec.md`, test file, changed prod files |
| Reviewer | Finding lacks location or spec statement | Reviewer | Clarifying notes |
| Reviewer | Reject, round < 3 | Implementer | Findings **verbatim** |
| Reviewer | Reject, round 3 | **Human, STOP** | All accumulated findings |
| Reviewer | Pass | Orchestrator → **Human (H2)** | Final verdict in `log.md`, then final report |

**Round budget.** A round is one implementer build; the first build is round 1.
A still-red green run and a reviewer reject draw from one shared budget of 3
rounds per run. Every build, whatever triggered it, goes through the green
re-run, G2 and review again.

---

## 3. Tool-grant matrix

Tools are granted in two layers, and a call has to pass **both**:

1. **Agent frontmatter** (`tools` / `disallowedTools`) sets which tools Claude
   Code exposes to the agent.
2. **MCP allow-list** (`mcp/roles.allowlist.json`, checked by
   `authorize()` in `mcp/tools_server.py`) sets which tools each role's
   server will run. The role is the server's launch role, never a call
   argument.

Tool names below are written `<tool>`. Each agent's actual grant is
`mcp__coursetools_<role>__<tool>` on its own server. For example, the
planner has `mcp__coursetools_planner__file_read`.

Legend: **Yes** = granted in both layers. **Denied** = listed in the agent's
`disallowedTools` and refused by the server for that role. **Disallowed** =
listed in `disallowedTools` (built-in tool, no server layer). **-** = not
listed in the agent's `tools`, so not available.

| Tool | Orchestrator | Planner | Tester | Implementer | Reviewer |
|------|:-:|:-:|:-:|:-:|:-:|
| `Task` (spawn subagents) | Yes | - | - | - | - |
| `file_read` | Yes | Yes | Yes | Yes | Yes |
| `file_write` | Yes | Yes | Yes | Yes | Yes |
| `codebase_search` | Denied | Yes | Denied | Yes | Yes |
| `git_status` | Yes | Denied | Yes | Yes | Yes |
| `test_runner` | Denied | Denied | Yes | Denied | Denied |
| `shell` (simulated) | Denied | Denied | Denied | Denied | Denied |
| `Edit` (built-in) | Disallowed | Disallowed | Disallowed | Disallowed | Disallowed |
| `Write`, `Bash`, `Read`, `Skill`, etc. (built-in) | - | - | - | - | - |

The two layers agree for every role.

### Server registration

`.mcp.json` at the repo root registers five servers, one per role:
`coursetools_orchestrator`, `coursetools_planner`, `coursetools_tester`,
`coursetools_implementer` and `coursetools_reviewer`.
Each runs `uv run --no-project --with "mcp>=1.2,<2" python mcp/tools_server.py`
from the repo root, with its role in `COURSETOOLS_ROLE`.

- **The role is fixed at launch.** No tool takes a `role` argument; one
  passed anyway is ignored. A server started without a known role refuses to
  start.
- **Each agent's frontmatter grants only `mcp__coursetools_<own role>__*`**,
  so a subagent can't reach another role's server.
- **The main session isn't limited this way.** A human's own Claude Code
  session sees all five servers and can call any of them. Only subagents are
  restricted by their frontmatter.

- **`mcp` is pinned below 2.** In `mcp` 2.x, `FastMCP` was renamed and the
  server fails on import.
- **First launch needs network access** so `uv` can fetch `mcp`. After that
  it comes from the `uv` cache.
- **Claude Code asks before it starts servers from a project's
  `.mcp.json`.** Until all five are approved, a role whose server isn't
  approved has none of its grants.
- **Paths are anchored to the server file.** The project root defaults to the
  parent of `mcp/`, and the allow-list and write-scope files to `mcp/`. That
  holds wherever the server is started from. `COURSETOOLS_ROOT`,
  `COURSETOOLS_ALLOWLIST` and `COURSETOOLS_WRITE_SCOPES` override them.

### What each tool actually does

| Tool | Behavior |
|------|----------|
| `file_read` | Reads any UTF-8 file under the project root |
| `file_write` | Writes a file under the project root and creates parent dirs, but only inside the calling role's scopes in `mcp/write_scopes.json` (see below) |
| `codebase_search` | Case-insensitive substring search. Max 20 files, 3 lines each. Skips `.git`, `node_modules`, `.venv`, `__pycache__` |
| `git_status` | Fixed `git status --short` only. Used for the baseline and diff attribution |
| `test_runner` | Fixed commands only. pyproject: `uv run pytest` (no lint). package.json: `npm install` (if `install`) + `npm test`, or with `suite: "build"`, `npm run build`. The frontend defines no `test` script, so the default frontend suite always fails |
| `shell` | Never runs anything. It exists so a denied call can be observed |

### Write scope: enforced by the server

`file_write` checks every write against the calling role's entries in
`mcp/write_scopes.json` (`check_write_scope()` in `mcp/tools_server.py`; the
server has the same scopes built in if the file is missing). A pattern's `*`
matches within one path segment and `**` matches any number of segments.
Modes:

- **write**: create or overwrite.
- **create**: create only. Refused if the file already exists.
- **untracked**: create, or overwrite only files git doesn't track. A role can
  revise the new files it made in earlier rounds, but can't edit existing
  code or tests. If git can't answer, the write is refused.

| Role | Allowed writes (`<run>` = `docs/orchestrator-runs/*`) | Mode |
|------|------------------------|------|
| Orchestrator | `<run>/log.md` (writing it creates the run dir) | write |
| Planner | `<run>/spec.md` | write |
| Tester | `backend/tests/**` | untracked |
| | `<run>/red-proof.md` | write |
| | `<run>/green-report-round-*.md` | create |
| | `docs/iteration-log-test-author.md` (its log) | write |
| Implementer | `backend/app/api/**`, `backend/app/services/**` | untracked |
| | `<run>/implementer-log.md`, `docs/iteration-log-endpoint-builder.md` (standalone) | write |
| Reviewer | `<run>/review.md` | write |

Still instructions only:

- **Freezing `red-proof.md` after G1.** The server can't tell whether G1 has
  passed, so the tester can still rewrite it. Only the tester can, though:
  the implementer can no longer touch it, or any test file.
- **Which run a role writes to.** Patterns match any run directory, not just
  the current `<run-id>`.
- **Narrower rules inside a scope**, such as the implementer never touching
  `.env` (outside its scopes anyway) or only creating *modules* under
  `services/`.

Scopes apply to the server's launch role, so an agent can't take on another
role's scopes by claiming it.
G2 remains the check that catches changed test files, and the reviewer's
code-vs-spec check catches scope creep in production code.

---

## 4. Gates

| Gate | Checked by | Evidence required | On failure |
|------|-----------|-------------------|-----------|
| **H1** Spec approval | Human | `spec.md` | Back to planner with notes |
| **G1** Red proof | Orchestrator | `red-proof.md` with verbatim failing output and every new test file quoted in full | Run fails; escalate; implementer not invoked |
| **G2** Green intact | Orchestrator | Quoted green output (pytest exit 0, plus `npm run build` exit 0 if frontend files changed) **and** each test file identical to its copy in `red-proof.md` | Changed test file = hard failure, never accepted. Still red with unchanged tests = implementer, shared round budget |
| **G3** Review | Reviewer, enforced by orchestrator | `review.md` = pass/reject with `file:line` findings | Implementer, max 3 rounds (shared budget), then escalate |
| **H2** Commit/merge | Human | `log.md` + final report | Agents never commit or merge |

---

## 5. Human review and approval points

| Point | Blocking? | Trigger |
|-------|-----------|---------|
| Spec approval (H1) | **Yes**, every run | After the planner |
| Red-proof failure | **Yes**, run stops | G1 fails |
| Test file tampering | **Yes**, hard failure | G2 detects a changed test file |
| Round limit | **Yes**, run stops | Round 3 still red or rejected by the reviewer (one shared budget) |
| Environment problems | **Yes**, role stops | Baseline already failing, `STOCKFISH_PATH` missing, required key missing |
| Commit / merge (H2) | **Yes**, always | End of every run |
| Follow-ups | No (after the run) | Shared-code changes the implementer reported, open spec questions, checks a role marked pending |

---

## 6. Run artifacts

`docs/orchestrator-runs/<run-id>/` (`<run-id>` = `<slug>-<YYYY-MM-DD>`):

| File | Author | Required for "done" |
|------|--------|:-:|
| `spec.md` | Planner | Yes |
| `red-proof.md` | Tester | Yes. Failure output + full copy of each new test file. Frozen once G1 passes |
| `green-report-round-<N>.md` | Tester | Yes, one per implementer build (`<N>` = round). Never overwritten |
| `implementer-log.md` | Implementer | No. Handoff contract for the latest build; overwritten each round |
| `review.md` | Reviewer | Yes |
| `log.md` | Orchestrator | Yes |

---

## 7. Known gaps and inconsistencies

None open. Gaps found while writing this map have all been resolved. Add new
ones here as they turn up.
