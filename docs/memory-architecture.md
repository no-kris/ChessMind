# Memory Architecture

## What this workflow needs to remember

This workflow runs drift investigations. It compares claims in ChessMind's docs, PRDs, rubrics, and agent files against the code and tests, then reports discrepancies with evidence. It does not edit the files it checks.

Across sessions, it needs to remember:

- which fixes the user approved,
- which discrepancies are still open, and
- the constraints that still apply.

It does not need to store anything the code, tests, or config already record. It must never store credentials or secrets, and it does not keep run cost or timing.


## Layer 1: Project memory directory
**Belongs here**
- Open decisions: which findings are accepted, deferred, or rejected.
- Unresolved discrepancies, with file and line on both sides.
- Active constraints that affect the next investigation.
- The rule that the user makes the final call on fixes.

**Does not belong here**
- API keys or environment secrets.
- Future feature decisions.
- Copies of PRDs, code, or tests.
- Full findings. Link to the report instead.

- **Scope:** Shared across drift investigations.
- **Write permissions:** The investigator agent does not write here. It writes only `docs/drift-report.md`. The user or workflow updates this file after a decision.
- **Pruning policy:** Move a resolved item to a short Resolved list with the date and a link to the report. Delete items that no longer affect future runs. Review the file when the investigation process changes.

## Layer 2: Knowledge files
Pointers to the files that define how the agent works.

**Belongs here**
- Agent instructions: `.claude/agents/drift-investigator.md`.
- Workflow rules and acceptance criteria: `docs/prd-drift-investigation.md`.
- Quality standard: `docs/rubric-drift-investigation.md`.

**Does not belong here**
- Handoffs and run logs. They record one session, not reusable instructions.
- Future feature plans or improvement ideas.
- Copies of these files. Point to the original.

- **Scope:** Shared across drift investigations.
- **Write permissions:** Read-only. The agent writes only `docs/drift-report.md`.
- **Pruning policy:** Update a pointer when its file is renamed or replaced. Remove pointers to files that no longer exist.

## Layer 3: Indexed reference documents
Source material the investigator reads, linked rather than copied.

**Belongs here**
- The named target and the files it directly references: docs, code, tests, fixtures, config.
- Prior drift reports, linked by path or commit.
- The canonical PRD and rubric, linked from Layer 2.

**Does not belong here**
- API keys or environment secrets.
- Vendored or generated files: virtual environments, node_modules, caches, lockfiles.
- Copies of source files. Link to the original.
- The current run's drift report and handoff. They become references after the run ends.

- **Scope:** Shared across drift investigations. Retrieve only what the named target references.
- **Write permissions:** Read-only. The agent may search and read, never edit.
- **Pruning policy:** Drop entries whose path moved, was deleted, or is no longer relevant. Keep an old report only while it still informs a decision.


## Allocation decision table

| Information | Store it in | Example |
|---|---|---|
| Decisions, open discrepancies, and active constraints | Layer 1: Project memory | A status line and a link to the report |
| Instructions, rules, and quality standards | Layer 2: Knowledge files | Agent, PRD, and rubric paths |
| Source material used as evidence | Layer 3: Indexed references | Docs, code, tests, and prior reports, linked |
| Notes and drift findings for the current run | The run's report and handoff (working artifacts) | Progress, file list, draft findings |
| Secrets, vendor files, or generated content | Nowhere | Never store secrets; exclude caches and node_modules |

When a run ends, decisions move to Layer 1 and the report becomes a Layer 3 reference. The handoff stays with the run or is discarded.


## Alternatives considered
- **One combined store.** Simpler, but decisions, instructions, and source files age at different rates, so stale entries are hard to spot and remove.
- **Copy every reference into memory.** Faster to search, but the copy can drift from the original, and the extra context costs space on every run.
- **No persistent memory.** Cheapest to maintain, but each session would rediscover open decisions and repeat settled disagreements.
