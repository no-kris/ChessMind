# Context Management Technique Plan 

## Explicit Context Boundaries

### Boundary 1: Phase 1 (Extract) then Phase 2 (Verify & Report)
- Phase complete: position-builder.md, prd-positions.md, rubric-positions.md read, any disrepancies found, and referenced files listed in the report.
- Next focus: Verify each claim listed in the report.
- Active requirements: Only write docs/drift-report.md, never edit code, docs, or config, skip ignored directories, no network.
- Changed requirements: Shift from extraction to verification.
- Info carried forward: Report file, and a handoff report summarizing what happened in phase 1.

Why: Forces a clean handoff from extraction phase to verifacation phase. 

## Proactive Summarization

### Summary Point 1: After Phase 1, before Phase 2
Ask the agent to summarize:
- Current goal: Find discrepancies between position-builder.md, prd-positions.md, rubric-positions.md and the actual codebase.
- Active requirements/constraints: only docs/drift-report.md written, no edits to code, docs, or config, no network, skip ignored directories.
- Decisions made: Which files are directly referenced and why.
- Artifact state: Files being referenced and report status.
- Unresolved questions: Any ambiguous references?
- Next planned action: Verify claims against referenced files in the drift-investigator agent's report.

Why: Catches ambiguity early before any verifications take place. 

## Compaction (Use only if crowded)

### Trigger for compaction
Only if context becomes crowded during each phase and tokens are running low.

Plan: If approaching 60% context limit, summarize findings so far into a compact form (IDs, classifications, file:line pairs) while keeping the constraints. Don't include verbose file contents after extracting the report data. 

Why: Preserves traceability and constraints while avoiding premature compaction.
