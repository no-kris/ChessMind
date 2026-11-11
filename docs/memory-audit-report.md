# Memory Audit Report

- Date: 2026-11-11
- Auditor: memory-auditor agent (read-only)
- Scope: `.memory/SCOPE.md`, `.memory/project/MEMORY_INDEX.md`, `.memory/project/decisions/decision-001..007.md`, `.memory/knowledge/coding-standards.md`, `.memory/knowledge/testing-standards.md`, `.memory/reference/REFERENCE_MEMORY_INDEX.md` (plus the three `.gitkeep` files, which are empty)
- Rules source: `CLAUDE.md`, section "Memory Configuration"

**Read-only contract:** No file under `.memory/` was written, and no permission, owner, attribute or ACL was changed anywhere. All fixes below are proposals for a human to apply. Tags: `[HUMAN-ACTION]` means a human needs to decide or edit something. `[INFO]` means no action is required.

## 1. Baseline and integrity proof

Before any reads, `git status --short` was empty (clean tree) and `git status --short .memory/` was empty. The full SHA-256 of every file under `.memory/` at run start is listed in section 7.

The full before/after hash comparison and the `git status` comparison are in section 7, at the end of the report.

## 2. Findings by severity

### Blocker

None. No Secret content (credential, token, API key) was found, so the "flag and do not proceed" rule was not triggered.

### Should-fix

**S1 [HUMAN-ACTION] Reference index is stale against `docs/`, `.claude/agents/` and the backend.**
- Location: `.memory/reference/REFERENCE_MEMORY_INDEX.md:3` ("Last updated: 2026-11-05"). The index's own pruning rule is at `:173-174` ("Review this index whenever files are added to or removed from `docs/`").
- Rule: Stale memory policy, plus the index's own pruning rule. `reference/` is read-only, so only a human can edit it.
- Evidence: these files exist but are not indexed:
  - `docs/iteration-log-security.md`. It is missing from the iteration-log list at `:152-155`.
  - `docs/rubric-memory-audit.md`, `docs/rubric-endpoint-builder.md`, `docs/rubric-test-author.md`
  - `.claude/agents/backend-test-author.md`, `endpoint-builder.md`, `memory-auditor.md`. Only drift-investigator and position-builder are listed, at `:90-96`.
  - The Phase 1 code from decision-003: `backend/app/api/games.py`, `backend/app/services/game_store.py`, `backend/app/services/moves.py`
- Proposed fix (human): add the missing entries in the existing format and set `:3` to `Last updated: <date of edit>`. Example for `:152-155`: append `` `docs/iteration-log-security.md` `` to the list.

**S2 [HUMAN-ACTION] MEMORY_INDEX "Last updated" date is behind its last change.**
- Location: `.memory/project/MEMORY_INDEX.md:3` ("Last updated: 2026-11-08").
- Evidence: the file was last changed in commit `d8b05ab` (2026-11-09 21:31 UTC, "archive after Phase 1 merged to main"). That commit added the archived section at `:64-72`.
- Rule: Stale memory policy. The index is the startup orientation file, so its date should be trustworthy.
- Proposed fix: change `:3` to `Last updated: 2026-11-09`.

### Note

**N1 [INFO] Personal name in knowledge files. Classified Internal, not Secret. A human should confirm.**
- Location: `.memory/knowledge/coding-standards.md:5` and `.memory/knowledge/testing-standards.md:5` (a `Maintained by:` line with a person's full name; the value is not repeated here).
- Rule: Write policy (PII counts as Secret).
- Assessment: the line attributes a document owner. The same name already appears as the git author on every commit, so I classified it as Internal and did not halt. If the project treats maintainer names as PII, a human should replace it with a role, e.g. `Maintained by: project owner`.

**N2 [HUMAN-ACTION] decision-004 and decision-005 are agent choices that the user has not reviewed.**
- Location: `decision-004.md:5`, `decision-005.md:5`, `MEMORY_INDEX.md:25` and `:32`. The same open item is repeated at `decision-003.md:41`.
- Rule: no rule is violated. This is pending human confirmation of active entries that other work depends on (the API contract and the single-worker constraint).
- Proposed action: the user reviews both. Then a human (or an agent at the user's request) changes `:5` to `Status: Active. Confirmed by the user on <date>.` and drops "unreviewed" from the index.

**N3 [INFO] An archived entry tells future agents to run `chmod 644` on their own.**
- Location: `decision-003.md:33` ("**If EXE002 comes back** ... use the same fix, `chmod 644 <files>`"), repeated in `MEMORY_INDEX.md:70-71`.
- Rule context: CLAUDE.md's permission rules cover `.memory/knowledge/` and any change made to get around a denial. A chmod on backend source files is outside both, so this is **not a violation**. But it is a standing instruction for an agent to change permissions on its own, which conflicts with how the rest of the policy treats permissions.
- Proposed fix (optional, human): change `decision-003.md:33` and `MEMORY_INDEX.md:71` to "report the affected files and ask a human to run `chmod 644 <files>`".

**N4 [INFO] Small mismatches between the index summaries and the entries.**
- `MEMORY_INDEX.md:22-23` says every error `detail` reads `"<operation> failed: <problem>"`, "422 included". But `decision-004.md:25` gives the 422 format as `"<METHOD> <path> failed: invalid request (...)"`. Proposed fix: change `:23` to read `... reading "<operation> failed: <problem>" (422: "<METHOD> <path> failed: ...")`.
- `MEMORY_INDEX.md:44-49` (decision-007) leaves out that the approach was the agent's choice (`decision-007.md:5`), while the summaries for 004 and 005 include that caveat. Proposed fix: append "(approach chosen by agent)" after "Recorded 2026-11-06" at `:48-49`.

**N5 [INFO] Overlapping entries. These are cross-referenced, not duplicates.**
- `decision-005.md:10` and `decision-006.md:11` both describe the "store methods never `await`" rule and the race test. Each points to the other, and they cover different topics: store concurrency and history continuity. No merge is needed.
- `decision-004.md:13-14` and `decision-006.md:8-10` both describe the 409 and takeback behaviour, also with links between them. They are consistent.
- `decision-002.md:7` repeats `knowledge/testing-standards.md:9` (tests in `backend/tests/`). The two agree. The decision also records the rejected alternative and the open frontend question (`decision-002.md:13`), so keeping both is reasonable.
- No two entries record the same decision.

**N6 [INFO] Read-only layers: modes and how they are enforced.**
- Observed modes: `knowledge/` and `reference/` are `dr-xr-xr-x root:root`; their files are `-r--r--r-- root:root`. `project/`, `decisions/`, `SCOPE.md` and `MEMORY_INDEX.md` are writable by the owner (`rw-r--r--`). This matches the layer rules.
- The agent runs as root, and root ignores these mode bits. The real protection is the PreToolUse hook `.claude/hooks/protect-memory.sh`, which is indexed at `REFERENCE_MEMORY_INDEX.md:98-100`.
- Git stores all of these files as `100644` (`git ls-files -s`). The read-only modes exist only in this checkout, so a fresh clone would have writable files.
- Attributes and ACLs could not be checked because `lsattr` and `getfacl` are not installed.
- No permission change is proposed. If a human wants enforcement that does not depend on the hook (e.g. a read-only bind mount, or running the agent as a non-root user), that is their decision.

**N7 [INFO] Review dates.**
- All active decisions have review dates that have not passed: 001 and 002 are 2027-02-01 (`:4`), 004 and 005 are 2027-02-03 (`:4`), 006 and 007 are 2027-02-04 (`:4`). Each is the recorded date + 90 days, which matches the pruning schedule at `MEMORY_INDEX.md:78`.
- Archived decision-003 still has `Review by: 2027-02-02` (`decision-003.md:4`). This is harmless. A human could optionally replace it with `Archived: 2026-11-08`.
- The knowledge files have `Last reviewed` dates (2026-11-02 and 2026-11-04) but no "review by" date. Under the 90-day rule they are due around 2027-01-31 and 2027-02-02, so neither is overdue. Optional: add `Review by:` lines.
- `SCOPE.md` has no review date. It is a static declaration and does not need one.

**N8 [INFO] The archived decision-003 contains superseded text.**
- `decision-003.md:30` still says decision-006 means "client FEN is trusted; needs user confirmation". This was reversed at `:35` and in `decision-006.md:5`. The entry is a dated progress log and is archived, so the record is accurate as history. No change is needed.

## 3. Index consistency (decisions/ vs MEMORY_INDEX.md)

| File | In index | Index status | Entry status (line) | Dates match | Result |
|---|---|---|---|---|---|
| decision-001.md | `:7-13` | Active | Active (`:5`) | 2026-11-03 / 2027-02-01 | Clean |
| decision-002.md | `:15-17` | Active | Active (`:5`) | 2026-11-03 / 2027-02-01 | Clean |
| decision-003.md | `:66-72` | Archived | Completed and archived 2026-11-08 (`:5`) | yes | Clean. Archived per the workflow-scoped rule (`:76-77`) after branch merged in `3cc4ce8` (`decision-003.md:40`) |
| decision-004.md | `:19-26` | Active, unreviewed | Active, unreviewed (`:5`) | 2026-11-05 / 2027-02-03 | Clean (see N2, N4) |
| decision-005.md | `:28-33` | Active, unreviewed | Active, unreviewed (`:5`) | 2026-11-05 / 2027-02-03 | Clean (see N2) |
| decision-006.md | `:35-42` | Active, user-confirmed | Active, confirmed 2026-11-06 (`:5`) | yes / 2027-02-04 | Clean |
| decision-007.md | `:44-49` | Active | Active (`:5`) | 2026-11-06 / 2027-02-04 | Clean (see N4) |

Every file in `decisions/` is in the index, and every decision entry in the index points to a file that exists. `.gitkeep` is empty and not an entry. The knowledge and reference pointers (`:51-62`) point to files that exist, and their "Last reviewed" dates match the files: `coding-standards.md:4` 2026-11-02, `testing-standards.md:3` 2026-11-04, `REFERENCE_MEMORY_INDEX.md:3` 2026-11-05.

## 4. Rule-by-rule coverage (CLAUDE.md "Memory Configuration")

| Rule | Checked against | Result |
|---|---|---|
| Startup: read MEMORY_INDEX.md | Index | Present and readable. Date is stale (S2) |
| Update existing entries, no duplicates | All 7 decisions, knowledge | No duplicates. Overlaps are cross-referenced (N5) |
| project/ is writable for significant decisions | project/ | Writable by owner. Entries are decision records |
| knowledge/ is read-only, never written | knowledge/ (2 files) | Mode is r-x/r--. No sign of agent edits. Both files say "human-maintained" (`coding-standards.md:9-10`, `testing-standards.md:6`) |
| knowledge/: never change permissions | knowledge/ | Not touched in this run. Observed modes reported (N6) |
| reference/ is read-only, query by keyword | reference/ | Mode is r-x/r--. Only the index was read; paths spot-checked (section 5). Index is stale (S1) |
| Write policy: Public/Internal OK | All files | All content is Public or Internal (code design, commit hashes, file paths) |
| Write policy: no Confidential | All files | None found |
| Write policy: no Secret (credentials/tokens/keys/PII) | All files (keyword scan plus a full read of every non-reference file and the reference index) | No credentials, tokens or keys. Maintainer name: see N1. `coding-standards.md:22` and `REFERENCE_MEMORY_INDEX.md:164` mention "secrets" only as policy text |
| Permission denials: stop, report, no workaround | This run | One hook denial, handled under the read-only exception (section 6) |
| Stale memory: flag passed review dates | All entries | None passed (N7) |
| Scope verification | SCOPE.md | `SCOPE.md:3-4` say ChessMind / no-kris/ChessMind, which matches this repo (the caller had already confirmed this) |

## 5. Reference spot-check (paths only, contents not read)

These paths from `REFERENCE_MEMORY_INDEX.md` exist: `ai_chess_coach_project_plan.md`, `agent-summary.md`, `README.md`, `setup.md`, `session_tasks.md`, `backend/app/main.py`, `backend/app/api/routes.py`, `backend/app/services/engine.py`, `backend/app/services/classify.py`, `backend/tests/test_api.py`, `backend/tests/fixtures/scenarios.json`, `backend/tests/fixtures/positions.json`, `frontend/src/App.tsx`, `.claude/agents/drift-investigator.md`, `.claude/agents/position-builder.md`, `.claude/hooks/protect-memory.sh`, `docs/drift-report.md`, `docs/memory-architecture.md`. The agent versions in the index (`:91` v0.1.0, `:95` v0.4.0) match the `version:` frontmatter of the agents. No broken links were found in this sample.

## 6. Permission denial during this run

- Tool: Bash
- Command: a `for p in ...; do [ -e "$p" ] ...; done` loop that tested whether the referenced paths exist, followed by `getfacl`/`git log`/`ls`.
- Exact message: `PreToolUse:Bash hook error: .memory/knowledge and .memory/reference are read-only: 'for' is not a read-only command`
- Intent: read-only existence checks of paths listed in the reference index.
- Handling: CLAUDE.md allows a retry with a simpler read-only command when the denied call was read-only. I retried with plain `ls -d <paths>`, `git log` and `getfacl` as separate commands. No write was attempted, and the hook was not modified or bypassed.

## 7. Integrity proof (before vs after)

Baseline SHA-256 (captured before any reads):

```
3a14dbc3f1448aff03821eee16fa3eed4cdccc00d7668f8b3e28e4e0a9b4929b  .memory/SCOPE.md
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  .memory/knowledge/.gitkeep
bb7f187b073ec1b4afd8e9db8a4908da5d8d9fd4334104a9c7e701e901155254  .memory/knowledge/coding-standards.md
2b685e623da5d54749f41b968054c22e44c416238260bbf139583857fbc98a27  .memory/knowledge/testing-standards.md
9aff4ee65f9c46b224ebc71510ae8dee46b6a40003110408227cdb0e9fbffe16  .memory/project/MEMORY_INDEX.md
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  .memory/project/decisions/.gitkeep
5f685a708b091c0a4d1c5d0b5f612d4d793c56f23f2066d6e5926d4b5508b5c6  .memory/project/decisions/decision-001.md
9d89faa06f58d3cbae9aeff537f27c6d05438576d84c270cb0e2444d53d8c6c6  .memory/project/decisions/decision-002.md
2b22f5a0ab90de74567156aa9a613f9607a2bd7138d2478f7a557e3fdf78b9e5  .memory/project/decisions/decision-003.md
ddcd74a990906258d255a9d81d5255679e72f61f0a3bd9b7e59e7173ce84f209  .memory/project/decisions/decision-004.md
7cdea851f7d8310de9ce5824e3e9ac410d2a38f3b6dfccd72a8f08cc5592886d  .memory/project/decisions/decision-005.md
3194f3872532968e6f59e900e4640cca90ebce33a1507803dfc1aab64a579ff5  .memory/project/decisions/decision-006.md
741c9652a37f7f5ec883e34426be870f90b579ffb4af9f54e45510928d79f245  .memory/project/decisions/decision-007.md
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  .memory/reference/.gitkeep
d75887321381c217ed65e4e031487b8a32912eeb55f1fb973bffc6971f05c393  .memory/reference/REFERENCE_MEMORY_INDEX.md
```

Post-run check: `sha256sum -c` against the baseline returned OK for all 15 files. `git status --short` before the run was empty. After the run it shows only `?? docs/memory-audit-report.md`. `git status --short .memory/` is empty both before and after.

No memory files were edited and no permissions were changed. Every fix above (S1, S2 and the optional items in N1-N8) needs a human decision and a human edit.
