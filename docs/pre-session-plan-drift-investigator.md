# Pre-Session Plan: Testing drift-investigator 

## Task
Run drift-investigator on position-builder agent defined in position-builder.md to find any discrepancies between its claims and the actual codebase. 

## Agent
drift-investigator (.claude/agents/drift-investigator.md) 

## Phases 

### Phase 1: Extract
- Goal: Read position-builder.md, prd-positions.md, and rubric-positions.md.
- Rules: Read-only, no network, skip ignored directories, stay scoped to target. 

### Phase 2: Verify & Report
- Goal: Check claims against files directly referenced by position-builder.md, prd-positions.md, rubric-positions.md.
- Rules: For every difference, include file:line on both sides (or missing-doc/missing-code), classification, recommendation and rationale. Only write docs/drift-report.md. Never edit code, docs, or config. If more than 5 files needed, stop and ask which ones are needed and why. 

## Constraint Change
The 5-file limit. References may exceed 5, forcing the agent to stop and ask instead of reading more files. 

## Artifact To Revisit Later
docs/drift-report.md. Report created by the agent used to make decisions, however the agent must never act on or edit based off the report. 

## Evidence To Evaluate
- Conformance: Only docs/drift-report.md written, asks if more scope is needed, no edits, no network, ignored directories skipped. 
- Quality: Every finding has locations, a classification, and a recommendation and rationale.
- Rubric: 3  on Detection Accuracy, Evidence Quality, and Classification & Recommendation.
