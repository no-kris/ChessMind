# Memory Architecture

## What this workflow needs to remember

This workflow runs drift investigations. It compares claims in ChessMind's docs, PRDs, rubrics, and agent files against the code and tests, then reports discrepancies with evidence. It does not edit the files it checks.

Across sessions, it needs to remember:

- which fixes the user approved,
- which discrepancies are still open, and
- the constraints that still apply.

The same memory also carries implementation work forward. Coding and testing standards are kept in it, and so is the decision on what to build next (Phase 1, decision-003).

It does not need to store anything the code, tests, or config already record. It must never store credentials or secrets, and it does not keep run cost or timing.


## Layer 1: Project memory directory
**Belongs here**
- Open decisions: which findings are accepted, deferred, or rejected.
- Unresolved discrepancies, with file and line on both sides.
- Active constraints that affect the next investigation.
- The rule that the user makes the final call on fixes.
- Implementation decisions the user has approved, with scope and the tests that verify them. Example: `decisions/decision-003.md` (Phase 1).

**Does not belong here**
- API keys or environment secrets.
- Feature ideas or plans not yet decided. Once the user approves one, it becomes a decision entry.
- Copies of PRDs, code, or tests.
- Full findings. Link to the report instead.

- **Scope:** Shared across drift investigations.
- **Write permissions:** The investigator agent does not write here. It writes only `docs/drift-report.md`. The user or the main session adds or updates an entry after a significant decision, updating an existing entry rather than adding a duplicate (`CLAUDE.md` write policy).
- **Pruning policy:** An entry is never deleted outright. When it is resolved, set its `Status`, add the date and a link to the evidence, and move its line in `MEMORY_INDEX.md` from Active to Archived. An entry is not archived while any of its work is open, even if its branch has merged. While an entry is Active, its progress lists **Complete** and **Open** work separately. Completed work cites the commit that contains it, not "committed" or "uncommitted", so the wording stays true when the update itself is committed. Deferred work stays under Open, with a note saying it is deferred and what it checks. The session must flag any entry whose `Review by` date has passed and get the user's confirmation before acting on it (`CLAUDE.md` stale-memory policy).

**Maintenance of current content**

`MEMORY_INDEX.md`
- **Updated by:** the main session, in the same change as the entry it describes.
- **Review when:**
  - Every session start (it is read first).
  - An entry is added, changed, or archived. Bump `Last updated`.
- **Archive or remove when:** never removed. Lines move from Active to Archived. A pointer is fixed as soon as its target is renamed.

`decisions/decision-001.md` (drift fixes D1–D12)
- **Updated by:** the main session, after the user confirms.
- **Review when:**
  - The drift-investigator re-run on the position-builder finishes.
  - `.claude/agents/position-builder.md`, `docs/prd-positions.md`, or `docs/rubric-positions.md` changes.
  - The review date, 2027-02-01, passes.
- **Archive or remove when:** the re-run reports none of D1–D12 still open → `Status: Resolved`, archived. Merging `fix/drift-001-positions` to `main` (done) does not archive it, because the re-run is still open.
- **Current state:** the entry records the fixes as complete (`3cae3da`) and the drift-investigator re-run as open and deferred. The re-run checks the drift workflow, not this memory. A memory verification passes if the entry describes that state accurately, even though the re-run has not been done.

`decisions/decision-002.md` (tests in `tests/`)
- **Updated by:** the main session, after the user confirms.
- **Review when:**
  - The first frontend test is added (frontend location is still undecided).
  - Anyone proposes a test file next to its source.
  - `testing-standards.md` changes its Layout section.
  - The review date, 2027-02-01, passes.
- **Archive or remove when:** the user reverses it (`Status: Superseded`, with a link to the new entry). Or the human owner copies the full rule, frontend included, into `testing-standards.md`, which makes this entry a duplicate.

`decisions/decision-003.md` (Phase 1 slice)
- **Updated by:** the main session, after the user confirms.
- **Review when:**
  - A Phase 1 endpoint or one of its listed tests lands (record progress).
  - A route path or response shape is chosen (record it, since the entry leaves both open).
  - Anyone asks for an engine, LLM, or frontend change inside this slice.
  - The Phase 1 checkboxes in `ai_chess_coach_project_plan.md` change.
  - The review date, 2027-02-02, passes.
- **Archive or remove when:** all four endpoints and the listed tests exist, `ruff check` and `pytest` pass in `backend/`, and the plan's Phase 1 items are checked → `Status: Done`, archived.

`.memory/SCOPE.md` (read alongside this layer)
- **Updated by:** the human owner.
- **Review when:** the repo is renamed, forked, or moved to a new remote.
- **Archive or remove when:** never, while `.memory/` exists.

## Layer 2: Knowledge files
The human-maintained standards in `.memory/knowledge/`. The directory holds only these two files (plus `.gitkeep`). Pointers to agent definitions, PRDs, and rubrics are kept in the Layer 3 reference index, not here.

**Belongs here**
- Coding standards: `.memory/knowledge/coding-standards.md`.
- Testing standards: `.memory/knowledge/testing-standards.md`.

**Does not belong here**
- Agent definitions, PRDs, rubrics, or pointers to them. They are indexed in Layer 3.
- Handoffs and run logs. They record one session, not reusable instructions.
- Feature plans or improvement ideas.
- Decisions with a scope or an end. They go in Layer 1.

- **Scope:** Every session that writes, reviews, or tests code, not only drift investigations.
- **Owner:** The human owner named in each file's `Maintained by` line. The owner created and committed both files (`8af83f0`, `2cf81d5`) and is the only one who changes their content.
- **Write permissions:** Read-only for every agent (`CLAUDE.md`, `docs/prd-memory.md`). The `.claude/hooks/protect-memory.sh` hook enforces this for Bash commands. The Edit and Write tools rely on the `CLAUDE.md` rule. An agent that finds a wrong or outdated rule follows the `CLAUDE.md` permission-denial rule: it reports the rule, the evidence, and the exact edit it proposes in its session output, and the owner decides whether to make it.
- **Pruning policy:** The owner edits the content in a normal commit when one of the events in the table below occurs. This layer has no time-based review. The 90-day review in `MEMORY_INDEX.md` covers project-scoped entries only. After a review, the owner updates the file's `Last reviewed` date, and the main session updates the matching date on the file's line in `MEMORY_INDEX.md`. A rule is deleted when the tool, marker, command, or path it names no longer exists. A file is deleted only when repo config enforces all of its rules, and its `MEMORY_INDEX.md` line moves to Archived in the same change.

**Maintenance of current content**

`coding-standards.md` (Python, TypeScript, pre-commit gate)
- **Updated by:** the human owner.
- **Review when:**
  - The ruff rule set in `backend/pyproject.toml` or the frontend linter config changes.
  - `strict` or other `tsconfig` settings change.
  - A new pytest marker is registered, or `engine`/`llm` is renamed.
  - The commands in its "Before committing" section change in `README.md` or `frontend/package.json`.
  - A drift report or code review shows accepted code that breaks a rule, which means either the rule or the code is wrong.
  - A new language or framework enters the repo.
  - An agent reports a problem with a rule.
- **Remove when:** a rule names a tool, marker, or command that is gone (e.g. `npm run build` is replaced). The file is removed only if repo config (ruff or linter rules) enforces every rule.

`testing-standards.md` (layout, test-writing rules, coverage minimum)
- **Updated by:** the human owner.
- **Review when:**
  - decision-002 changes or frontend tests are added (Layout covers only `backend/tests/`).
  - A new test framework or runner is added.
  - `conftest.py` or store-reset conventions change.
  - `docs/prd-testing.md` or `docs/rubric-testing.md` is renamed or changes its required report.
  - pytest markers change.
  - `coding-standards.md` changes its marker or pre-commit lines, because both files repeat them and must stay in step.
  - An agent reports a problem with a rule.
- **Remove when:** a rule names a path, marker, or file that is gone. The Coverage pointer lines are removed if the testing PRD and rubric are deleted.

## Layer 3: Indexed reference documents
Source material linked from `.memory/reference/REFERENCE_MEMORY_INDEX.md`, never copied.

**Belongs here**
- Docs, code, tests, fixtures, and config, found by keyword.
- Agent definitions, PRDs, and rubrics for each workflow (drift, positions, testing, lint, memory).
- Prior reports, handoffs, and iteration logs, linked by path.

**Does not belong here**
- API keys, secrets, and environment files.
- Vendored or generated files: virtual environments, node_modules, caches, lockfiles.
- Copies of source files. Link to the original.
- `.memory/` itself. Project memory and knowledge have their own index.
- The current run's drift report and handoff. They are indexed after the run ends.

- **Scope:** All workflows. Query the index by keyword and read only the files the task points to.
- **Owner:** The index is owned by the same human owner as Layer 2, who created and committed it (`ce7f94d`). The file has no `Maintained by` line. Each linked file is maintained in normal commits by whoever owns it. Of the agents, the drift-investigator writes only `docs/drift-report.md` and the position-builder writes only `backend/tests/fixtures/positions.json`. Reports, handoffs, and iteration logs are committed by the human owner.
- **Write permissions:** Read-only to agents (`CLAUDE.md`, `docs/prd-memory.md`). The hook enforces this for Bash only, as in Layer 2. An agent that finds a stale or missing entry reports it with the proposed change, following the `CLAUDE.md` permission-denial rule, and the owner edits the index.
- **Pruning policy:** The index's own Pruning section is the implemented rule set: (1) drop an entry when its file is moved or deleted, or is no longer relevant; (2) keep an old report only while it still informs an open decision; (3) review the index whenever files are added to or removed from `docs/`. The owner updates `Last updated` after each change. The table below lists the concrete events for the current entries.

**Maintenance of current content**

Entries for code, tests, fixtures, frontend, and config
- **Updated by:** the human owner.
- **Review when:**
  - A file is added, renamed, or deleted under `backend/app/`, `backend/tests/`, `frontend/src/`, or the Docker files.
  - An entry's description stops being true: e.g. `routes.py` is described as having only `/analyze`, which goes stale when the decision-003 game endpoints land.
- **Remove when:** the linked path is moved or deleted (rule 1).

Entries for agents, PRDs, and rubrics
- **Updated by:** the human owner.
- **Review when:**
  - A PRD or rubric is added to or removed from `docs/` (rule 3).
  - An agent is added to `.claude/agents/`.
  - A recorded agent version changes (drift-investigator v0.1.0, position-builder v0.4.0). A version bump also triggers a drift run.
- **Remove when:** the file is deleted, or its workflow is retired (rule 1).

Prior reports and handoff: `docs/drift-report.md`, `docs/handoff-drift-positions.md`
- **Updated by:** the human owner, for the index entry. The drift-investigator writes the report once, and the human owner commits the report and the handoff.
- **Review when:**
  - decision-001 changes status.
  - A new drift report on the same target replaces the old one.
- **Remove when:** decision-001 is archived and no other active entry links to them (rule 2).

Iteration logs: `docs/iteration-log-*.md`
- **Updated by:** the human owner, both the index entry and the logs. The owner records each run in a commit (e.g. `e859544`).
- **Review when:**
  - A new log file is added to `docs/` (rule 3).
  - The matching PRD or rubric changes.
- **Remove when:** the matching PRD and rubric are retired, and no open decision relies on the logged scores (rule 2).


## Allocation decision table

| Information | Store it in | Example |
|---|---|---|
| Decisions, open discrepancies, and active constraints | Layer 1: Project memory | A status line and a link to the report |
| Approved implementation decisions | Layer 1: Project memory | `decision-003.md` (Phase 1 scope and tests) |
| Coding and testing rules set by the human owner | Layer 2: Knowledge files | `coding-standards.md`, `testing-standards.md` |
| Agent definitions, PRDs, and rubrics | Layer 3: Indexed references (linked) | `.claude/agents/drift-investigator.md`, `docs/rubric-drift-investigation.md` |
| Source material used as evidence | Layer 3: Indexed references | Docs, code, tests, and prior reports, linked |
| Notes and drift findings for the current run | The run's report and handoff (working artifacts) | Progress, file list, draft findings |
| Secrets, vendor files, or generated content | Nowhere | Never store secrets; exclude caches and node_modules |

When a run ends, decisions move to Layer 1 and the report becomes a Layer 3 reference. The handoff stays with the run or is discarded.


## Submitted memory files

### `.memory/knowledge/coding-standards.md` (Layer 2)
Python and TypeScript rules (docstrings, type hints, logging, error messages, test marks) and the pre-commit gate: `ruff check` and `pytest` in `backend/`, `npm run build` in `frontend/`.

**Why Layer 2:** It tells the agent how to work, not what was decided or what happened. A human sets it, and it applies to every session that writes or reviews code. It changes rarely and only when a human decides, so agents treat it as read-only. An agent that could edit it could loosen its own rules.

**Why not Layer 1:** It is not a decision with a scope or an end. It is a standing rule. Both layers are reviewed, but the reviewers differ. In Layer 1 the session updates or archives an entry once the user confirms. In Layer 2 only the human changes the text, using the triggers in the Layer 2 maintenance table. Putting the standards in Layer 1 would let a session rewrite them as if they were project state.

**Why not Layer 3:** Layer 3 is evidence the agent looks up by keyword when a task needs it. The standards have to be read before any code is written, not only when a keyword happens to match.

### `.memory/knowledge/testing-standards.md` (Layer 2)
Test layout, how to write tests (one behavior per test, mocked boundaries, `parametrize`, reset in-memory stores), the coverage minimum (one happy-path and one failure test per new endpoint or module), and the pre-commit gate. It points to `docs/prd-testing.md` and `docs/rubric-testing.md` for coverage audits.

**Why Layer 2:** Same reasons as the coding standards: human-maintained, needed before every test is written, and must not be changed by the agent. It links to the testing PRD and rubric rather than copying them, so there is one source for how coverage reports are scored.

**Why separate from coding standards:** Tests and production code are written at different times, and each file has its own `Last reviewed` date. Keeping them apart lets a human update one without re-reviewing the other.

### `.memory/project/decisions/decision-003.md` (Layer 1)
The next implementation slice is Phase 1 of `ai_chess_coach_project_plan.md`: an in-memory game store with create, get, move, and delete endpoints. The move endpoint is computed from the sent `FEN + move`. History is kept only for the later "Why?" lookup. There is no engine, LLM, or frontend work in this slice, and route paths and response shapes are left open. The entry lists the tests to write and the `ruff check`/`pytest` gate.

**Why Layer 1:** It is a decision the user made, with a date, a scope, and a review date (2027-02-02). It is project state that later sessions must recall correctly so they don't add an engine call or invent response shapes. It will change as Phase 1 is built (status, tests written), so it has to be writable. It follows the Layer 1 rules: the entry is indexed in `MEMORY_INDEX.md`, the session updates it instead of adding a duplicate, and it is reviewed or archived when its review date passes.

**Why not Layer 2:** It is not a standing rule. Once Phase 1 is done it stops guiding work and should be archived. Read-only standards cannot record that.

**Why not Layer 3:** The project plan it points to is a Layer 3 reference. The decision adds what the plan does not: which slice is next, what is out of scope, and how to verify it. Copying the plan would risk drift, so the entry cites plan lines 25–31 instead.


## Filesystem permissions

Recorded 2026-11-08 (22:51 UTC) inside the `dev` container, on branch `fix/memory-rubric`.

### Environment
- `/workspace` is the repo bind mount from `docker-compose.yml` (`.:/workspace`). It is mounted **read-write** (`9p ... aname=drvfs ... metadata`). There is no `:ro` mount for any part of `.memory/`.
- Nothing in `Dockerfile` or `docker-entrypoint.sh` sets permissions on `.memory/`. The modes below were applied by hand and are not reproducible from the repo. Git records every `.memory/` file as `100644`, does not track directory modes, and `core.fileMode` is `false`.

### Applied permissions

Captured with `stat -c '%A %a %U:%G %n'`:

| Path | Mode | Intended |
|---|---|---|
| `.memory/` | `drwxr-xr-x 755` | — |
| `.memory/knowledge/` | `dr-xr-xr-x 555` | read-only |
| `.memory/knowledge/coding-standards.md` | `-rwxrwxrwx 777` | read-only, **but world-writable** |
| `.memory/knowledge/testing-standards.md` | `-rwxrwxrwx 777` | read-only, **but world-writable** |
| `.memory/knowledge/.gitkeep` | `-r--r--r-- 444` | read-only |
| `.memory/reference/` | `dr-xr-xr-x 555` | read-only |
| `.memory/reference/REFERENCE_MEMORY_INDEX.md` | `-rw-r--r-- 644` | read-only, but owner-writable |
| `.memory/reference/.gitkeep` | `-r--r--r-- 444` | read-only |
| `.memory/project/` | `drwxr-xr-x 755` | writable |
| `.memory/project/MEMORY_INDEX.md` | `-rwxrwxrwx 777` | writable |
| `.memory/SCOPE.md` | `-rw-r--r-- 644` | — |

### Effect
- The `555` directories block creating, deleting, and renaming files. They do not block edits to existing files, and the two standards files and `MEMORY_INDEX.md` are `777`.
- The agent is prevented from modifying files in `.memory/knowledge/` and `.memory/reference/` by the `.claude/hooks/protect-memory.sh` PreToolUse hook. The hook denies any Bash command that touches those directories unless it is read-only.


## Alternatives considered
- **One combined store.** Simpler, but decisions, instructions, and source files age at different rates, so stale entries are hard to spot and remove.
- **Copy every reference into memory.** Faster to search, but the copy can drift from the original, and the extra context costs space on every run.
- **No persistent memory.** Cheapest to maintain, but each session would rediscover open decisions and repeat settled disagreements.
