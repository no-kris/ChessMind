# Memory Recall & Resumption Standard (PRD)

**Workflow**
- Start a session, load project memory as `CLAUDE.md` describes, then recall facts or resume earlier work using only what memory and the repo contain.

**Trigger**
- Developer starts a session (usually fresh, with no pasted memory) and asks a recall question or asks to resume a task.

**Branches**
- If `.memory/SCOPE.md` does not match this project, report the mismatch and stop.
- If a memory entry's review date has passed, flag it and ask for confirmation before acting on it.
- If memory has no entry for what is asked, say so. Do not guess.

**Steps**
1. Read `.memory/SCOPE.md` and confirm it matches the repo.
2. Read `.memory/project/MEMORY_INDEX.md`.
3. Read the active entries relevant to the task, and check their review dates.
4. Answer the recall question or resume the task, citing the entries used.
5. If a significant decision is made, update an existing entry or add one, and update the index.

**Rules**
- `.memory/knowledge/` and `.memory/reference/` are read-only.
- Query `.memory/reference/` by keyword only. Never read the whole directory.
- Update existing entries instead of creating duplicates.
- Never write Confidential or Secret information to memory.
- Do not state facts as remembered unless they are in memory or the repo.

**Acceptance criteria**
- Scope check and index read happen before any task work.
- Recalled facts match the memory entries, with entry paths cited.
- Stale entries are flagged and not acted on without confirmation.
- The resumed task continues from where memory says it stopped and stays within the recorded scope.
- No writes to read-only layers and no duplicate entries.
