# Context Management Technique Plan 

## Explicit Context Boundaries

### Boundary 1: Phase 1 (Extract) then Phase 2 (Verify, Revisit & Report)
- Phase complete: position-builder.md, prd-positions.md, rubric-positions.md read, discrepancies found, and initial report generated.
- Next focus: Verify each claim against referenced files and apply the requirement change (dropping mandatory Lichess game sourcing).
- Active requirements: Read-only verification, no code/doc edits except updating docs/drift-report.md to reflect the requirement change.
- Changed requirements: Lichess game source requirement is dropped; any drift report findings related to Lichess sourcing must be updated/dismissed in the report.
- Info carried forward: Initial drift report, handoff summary, and the rule-change instruction.

Why: Forces a clean handoff and tests whether the agent/workflow can successfully handle a requirement change while keeping file-read scope adjustments.

## Proactive Summarization

### Summary Point 1: After Phase 1, before Phase 2
Ask the agent to summarize:
- Current goal: Verify initial drift findings against codebase files, then incorporate the mid-session rule change dropping Lichess game sourcing.
- Active requirements/constraints: Only docs/drift-report.md modified for the requirement change; no code, doc, or config edits; no network; skip ignored directories.
- Decisions made: Which files were read and why.
- Artifact state: Initial report status and pending drift-report adjustments.
- Unresolved questions: Any remaining ambiguous references to Lichess.org after dropping the Lichess requirement?
- Next planned action: Execute verification and update findings in the drift report.

Why: Catches ambiguity early and ensures the requirement change executes smoothly before final outputs are locked.

## Compaction (Use only if crowded)

### Trigger for compaction
Only if context becomes crowded during each phase and tokens are running low.

Plan: If approaching 60% context limit, summarize findings so far into a compact form (IDs, classifications, file:line pairs) while keeping the constraints and the active requirement change status. Don't include verbose file contents after extracting the report data. 

Why: Preserves traceability and constraint tracking while avoiding premature compaction.
