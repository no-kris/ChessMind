# Drift Investigation Standard (PRD)

**Workflow**
- Find discrepancies between docs and code, report them without changing anything.

**Trigger**
- developer asks to check drift for given file(s).

**Branches**
- If target can not be read or found, report it and stop. 

**Steps**
1. Read the target file
2. If doc: list claims (commands, versions, paths, env vars, endpoints). Check each against code
3. If code: find docs that describe it. Check what docs say vs actual code
4. For each difference: write file and line on both sides, classification, which side might be right and why
5. Write report to `docs/drift-report.md`

**Rules**
- Only write `docs/drift-report.md`
- Never edit code/docs/config
- Skip node_modules, .venv, dist, caches, lock files
- No network
- Max 5 files per task. If need more, ask user which files and why
- Must include locations on both sides, recommendation and rationale

**Acceptance criteria**
- Reports every finding with location, recommendation and rationale.
- Does not attempt to edit target file(s) or code.
- Only writes to `docs/drift-report.md`.
