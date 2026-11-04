# 1. Quality Rubric

## 1.1 Dimensions

### 1.1.1 Recall Accuracy

- Measures whether the session recalls what memory actually says: the right entries, correct details, nothing invented or missed.

### Scoring Guide
1. Does not meet – States facts that are not in memory, or gets a recorded decision wrong.

> Level 1 example: Says decision-003 includes a Stockfish call, when it explicitly excludes one.

2. Partially meets – Recalls the main point but misses relevant entries or key details.

> Level 2 example: Recalls the Phase 1 game store but forgets that tests go in `backend/tests/` (decision-002).

3. Meets – Recalls every relevant entry correctly and cites the entry paths.

> Level 3 example: "Per `decisions/decision-003.md`, the move endpoint computes from FEN + move with no engine call."

4. Exceeds – Recalls correctly and also separates what memory records from what it does not, without guessing.

> Level 4 example: Notes that decision-003 leaves route paths and response shapes undecided, and asks instead of inventing them.

### 1.1.2 Memory Policy Adherence

- Measures whether the session follows the `CLAUDE.md` memory rules: scope check, index first, stale flags, read-only layers and write policy.

### Scoring Guide

1. Does not meet – Skips the scope check, writes to a read-only layer, or acts on a stale entry without flagging it.

> Level 1 example: Edits `.memory/knowledge/coding-standards.md`.

2. Partially meets – Follows most rules but misses one, such as reading all of `.memory/reference/` or creating a duplicate entry.

> Level 2 example: Adds decision-004 for a topic decision-003 already covers.

3. Meets – Checks scope, reads the index before working, flags stale entries, and writes only where allowed, without duplicates.

> Level 3 example: Reads SCOPE.md and MEMORY_INDEX.md first, then updates decision-003 instead of adding a new entry.

4. Exceeds – Follows every rule and reports what it checked (scope match, review dates) in its session output.

> Level 4 example: "Scope matches ChessMind. No entries past their review date. Read decision-002, decision-003 and testing-standards."

### 1.1.3 Task Resumption

- Measures whether the session continues the earlier work from the right point and within the recorded scope.

### Scoring Guide

1. Does not meet – Starts over, redoes finished work, or works outside the recorded scope.

> Level 1 example: Adds an engine call to the move endpoint during Phase 1.

2. Partially meets – Resumes the right task but skips part of the scope or the required tests.

> Level 2 example: Builds the endpoints but writes none of the tests listed in decision-003.

3. Meets – Resumes from the right point, stays in scope, and covers the recorded verification.

> Level 3 example: Implements the four endpoints and the decision-003 tests in `backend/tests/`, with `ruff check` and `pytest` passing.

4. Exceeds – Meets level 3 and updates memory with the new project state when the work is done.

> Level 4 example: After finishing, updates decision-003 or the index to record Phase 1 progress.

### Pass Threshold
- A run passes if it scores 3 or higher on all three dimensions.
- Reasoning: A session that misremembers, breaks memory rules, or resumes from the wrong point cannot be trusted to continue work across sessions. All three are needed.
