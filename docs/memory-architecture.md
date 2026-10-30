# Memory Architecture

## What this workflow needs to remember
This workflow helps maintain ChessMind’s docs, PRDs, rubrics, and agent definitions by running drift investigations that compare documented claims against the code/tests and report discrepancies with evidence, without editing anything. Across sessions, it needs to remember decisions about which fixes to apply, any unresolved direpancies, and the current active constraints. It does not need to store information already captured by code, tests, or configurations. It must not store credentials, API keys, environment secrets, or previous run details such as cost, or timing.

## Layer 1: Project memory directory
# Belongs here
- Store: Prior findings located in drift-report.md.
- Any unresolved conflicts with exact file/line reference.
- Current goals: User approved decisions for resolving code/document conflicts.
- Preferred approach: User has the final word for implementing fixes.

# Does not belong here
- API keys or environment secrets.
- Future feature decisions.
- Copies of PRDs, code, or tests.

- **Scope:** Shared across drift investigations.
- **Write permissions:** The agent may write to only docs/drift-report.md, but all other files are read-only.
- **Pruning policy:** 
  - Entries tied to a specific conflict are archived when that conflict is resolved.
  - Review when the investigation process changes.

## Layer 2: Knowledge files
# Belongs here
- Agent: Use .claude/agents/drift-investigator.md to see the agent instructions.
- Rules and acceptance criteria: Use docs/prd-drift-investigation.md to see the workflow rules and acceptance criteria.
- Quality Standards: Use docs/rubric-drift-investigations.md to see the qualitiy standards for drift investigations.

# Does not belong here
- Handoffs: Any agent generated summary handoffs.
- Logs: The runs in docs/iteration-log-drift.md do not have reusable instructions.
- Future feature decisions and/or improvements.

- **Scope:** Shared across drift investigations.
- **Write permissions:** The agent may write to only docs/drift-report.md, but all other files are read-only.
- **Pruning policy:** 
  - Entries tied to a specific conflict are archived when that conflict is resolved.

## Layer 3: Indexed reference documents
# Belongs here
- History: Any prior drift reports.
- Previous decisions: Previous decisions made to resolve conflicts.
- Quality Standards: Copies of any relevant PRDs and/or rubrics relevant to drift reports.

# Does not belong here
- API keys, or environment secrets.
- Vendor files such as Python virtual environments, node_modules, caches, or lockfiles.

- **Scope:** Shared across ChessMind drift investigations; retrieve only what’s relevant to the named target.
- **Write permissions:** Investigator agent may search/read, not edit. 
- **Pruning policy:** 
  - Refresh when sources change.
  - Remove deleted or out-of-scope entries. 
  - Keep old reports indexed only while useful.


## Allocation decision table

| Information | Store it in | Example |
|---|---|---|
| Cross-investigation decisions or unresolved discrepancies | Layer 1: Project memory | Brief status and evidence links; not a copied report |
| Reusable investigation instructions and quality rules | Layer 2: Knowledge files | Drift-investigator agent, PRD, and rubric |
| Source material to search for evidence | Layer 3: Indexed references | Docs, code, tests, and useful past reports linked to originals |
| Notes and findings for the current investigation | That investigation's report or handoff | Temporary file list, progress, and draft findings |
| Secrets or irrelevant/generated content | Nowhere | Never store secrets; exclude vendor files and caches from the index |

## Alternatives considered
- One combined memory store: Simpler, but mixes decisions, procedures, and source references, making stale information harder to manage.
- Copy all references into memory: Convenient to search, but duplicates docs and code, risking stale evidence and context bloat.
