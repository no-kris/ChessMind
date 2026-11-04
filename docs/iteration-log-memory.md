# Iteration Log

Record one section per run of the memory recall and task resumption tests. Each run checks whether a session can recall project memory (`.memory/`) correctly and resume earlier work.

Score every run against:
- Acceptance criteria: `docs/prd-memory.md`
- Rubric: `docs/rubric-memory.md` (pass = 3 or higher on all three dimensions)

---

## Run template

## Run 001 Startup-Memory Check

**Run ID:**
  - f8d700b9-d6bd-4c8d-a286-ff73240cdf63

**Date:**
  - 2026-11-04

**Agent name and version:**
  - Agent: Claude Code
  - Model: Claude Opus 5.5
  - Claude Code version: 2.1.318 (Claude Code)

**Task or workflow:**
  - Startup recall only. The session was asked to find the project memory, knowledge files and indexed references, and to explain how each category should guide work. No task was resumed and nothing was implemented.

**Prompt or Command:**
  - "report what project memory, Knowledge Files, and indexed references you can find and how each category should guide your work. Use CLAUDE.md as a reference."

**State of the memory system for the run:**
  - Session: fresh session with no pasted memory. CLAUDE.md was auto-loaded.
  - Active entries in `MEMORY_INDEX.md` at start: decision-001, decision-002, decision-003, coding-standards, testing-standards
  - Memory commit at start: 20fde5f. `testing-standards.md` also had uncommitted local changes, per git status.
  - Deliberate changes for this run: none.

**Results (against rubric and acceptance criteria):**
  - Rubric scores (with brief notes):
    - 1.1.1 Recall Accuracy: 3/4. All 3 decisions and both knowledge files were recalled correctly, with entry paths cited. The output separated recorded facts from unrecorded ones: decision-003 leaves routes and response shapes open, decision-002 leaves frontend test location undecided, and references are empty. It falls short of 4 because of one paraphrase drift and one unverified repo claim.
    - 1.1.2 Memory Policy Adherence: 4/4. It read SCOPE.md and the index first and verified scope against the git remote before any task work. It checked review dates and reported "no entries are stale" (all are 2027). It wrote nothing to any layer and reported what it checked.
    - 1.1.3 Task Resumption: N/A. The prompt was recall-only, so no task was resumed.
  - Acceptance criteria met / not met:
    - Scope check and index read before task work: met.
    - Recalled facts match entries, with paths cited: met, with one minor paraphrase drift.
    - Stale entries flagged: met. None were stale, and the output stated that explicitly.
    - Resumed task continues from recorded point: not applicable to this run.
    - No writes to read-only layers, no duplicates: met. No writes occurred at all.
  - Evaluation questions:
    - Found the intended files: yes. It found SCOPE.md, MEMORY_INDEX.md, decision-001/002/003, coding-standards.md, testing-standards.md, and an empty reference layer.
    - Distinguished changing project context from stable knowledge: yes. Decisions were presented as writable, dated project state with review dates. Knowledge files were presented as human-maintained, read-only standards to consult before coding or testing. Reference was presented as a keyword-query layer.
    - Respected ownership and write policies: yes. Nothing was written to any memory layer. It stated that the knowledge and reference layers are read-only and that project entries should be updated rather than duplicated.
    - Summarized entries accurately: mostly. The decision summaries match the source text, including the 6 decision-003 test behaviors plus the ruff/pytest gate. The knowledge summaries are accurate but condensed: they omit, for example, naming and constant rules and the TS import-order rule.
  - Specific evidence supporting each score:
    - Session output opened with: "SCOPE.md declares ChessMind (no-kris/ChessMind), and the git remote is https://github.com/no-kris/ChessMind.git ... All the review dates are in the future, so no entries are stale."
    - It cited `decision-003` for "move endpoint is stateless ... No engine, no LLM, no frontend. Route paths and response shapes are left open", which matches decision-003 lines 12 and 16-18.
    - Tools used: Bash (cat/find) and Read only. No Write or Edit on `.memory/`.

**Pass / Fail result:**
  - Pass on the applicable dimensions (3 and 4). Task Resumption was not exercised, so this run does not count toward resumption.

**Recall errors or misfires observed:**
  - Paraphrase drift: the output said "reset in-memory stores between tests in `conftest.py`". testing-standards.md lists these as two separate rules: shared fixtures go in conftest.py, and in-memory stores are reset between tests.
  - Unverified repo claim: the output flagged `test_classify.py` and `test_classify_positions.py` as a possible conflict with "one test file per module". On inspection, `test_classify_positions.py` validates the agent-built fixtures in `fixtures/positions.json` (and imports engine helpers), not just the classify module, so the flag was weak and should have been checked before reporting.

**Cycle time:**
  - 1m32s

**Review time:**
  - 11m15s

**Cost per run (token counts if available):**
  -  sess in: 612.0k out: 12.4k $: $0.64

**Relevant commit SHAs:**
  - 20fde5f - Update MEMORY_INDEX.md (add testing-standards entry).
  - 2cf81d5 - Create testing-standards.md knowledge file.
  - 49f7541 - Add decision 003 (Phase 1 game store and move endpoint) and update index.
  - 8af83f0 - Add decision entries 001 and 002 and coding standards knowledge file, update index.
  - ffd61ea - Initialize memory directory structure, index, and CLAUDE.md configuration.
  - fde76d5 - Fix spelling mistakes in memory-architecture.md.
  - 1c053da - Update docs/memory-architecture.md.
  - e72805e - Add memory architecture document (allocation decision and pruning policy).

**Observations:**
  - What worked: The startup order from CLAUDE.md was followed (scope, index, entries), and the session reported the scope match and review-date check explicitly. It gave a clear layer-by-layer split between writable project decisions, read-only knowledge and the empty reference layer. It made no writes, and the read-only hook was respected.
  - What failed: Two small accuracy slips: the conftest paraphrase and an unverified "one test file per module" conflict. The resumption dimension was not tested.
  - What changed between runs: This is the baseline memory run, with no prior run to compare. Next run should exercise task resumption (e.g. "resume decision-001") and a deliberate stale review date or scope mismatch.

---

---

## Run 002 Task-Resumption Check

**Run ID:**
  - c8e9dff0-0889-488b-b9e7-7949af1a7e6b

**Date:**
  - 2026-11-04

**Agent name and version:**
  - Agent: Claude Code
  - Model: Claude Opus 5.5
  - Claude Code version: 2.1.318 (Claude Code)

**Task or workflow:**
  - Task resumption. The session was asked to confirm it had read CLAUDE.md, then to "resume the workflow in decision 001". Decision-001 work (drift findings D1–D12) was resumed, applied and committed.

**Prompt or Command:**
  - "resume workflow in decision 001"

**State of the memory system for the run:**
  - Session: fresh session with no pasted memory. CLAUDE.md was auto-loaded.
  - Active entries in `MEMORY_INDEX.md` at start: decision-001, decision-002, decision-003, coding-standards, testing-standards. Earliest review date 2027-02-01, so nothing was stale.
  - Memory commit at start: 20fde5f (on `main`).

**Results (against rubric and acceptance criteria):**
  - Rubric scores (with brief notes):
    - 1.1.1 Recall Accuracy: 3/4. All three decisions were recalled correctly with paths cited. It separated what memory records from what it does not: decision-002 has no workflow, decision-001 does not say how D1 should be resolved, and decision-003 work has not started (checked against `backend/app/`). Held at 3 because of two loose repo claims (see misfires).
    - 1.1.2 Memory Policy Adherence: 3/4. Scope check, index read and review-date check happened before any work and were reported in the first reply. It updated decision-001 and its index line rather than adding a new entry, and wrote nothing to `knowledge/` or `reference/`. Held at 3 because the progress note it wrote ("Fixes applied, not yet committed"; index: "(uncommitted)") was committed in the same commit, so memory was already inaccurate when it landed.
    - 1.1.3 Task Resumption: 3/4. It resumed decision-001 from the handoff's next steps (D1 first, then D2 cleanup, then D3–D12), stayed in scope (docs, agent, summary; no test or code changes) and recorded progress in memory, which is the Level 4 behaviour. Held at 3 because the recorded verification step, re-running the drift-investigator, was not done.
  - Acceptance criteria met / not met:
    - Scope check and index read before task work: met.
    - Recalled facts match entries, with paths cited: met.
    - Stale entries flagged: met. None were stale, and the first reply said so.
    - Resumed task continues from recorded point, in scope: met. Verification (drift re-run) still open.
    - No writes to read-only layers, no duplicates: met.
  - Evaluation questions:
    - Identifies the current project state accurately: mostly. It found that decision-003 had not started, that none of the decision-001 fixes had been applied. Weak spots: it said `testing-standards.md` had real uncommitted edits without checking; they were line endings only.
    - Follows the stored standards and constraints: yes. CLAUDE.md startup order, update-don't-duplicate, read-only knowledge layer, decision-002's test location was not relevant to the decision 001 work. It committed on a new branch (`fix/drift-001-positions`) instead of `main`. It did not read `coding-standards.md` or `testing-standards.md`; the work it did didnt't require those standards.
    - Recognizes relevant decisions or deferred work: yes. It recognised that decision-002 is a rule, and checked that no Phase 1 code existed before asking. For decision-001 it surfaced the open intent decisions (D1, D9) and the conflict between the Nov 2 revert and decision-001's D2 fix. It listed the deferred items (drift re-run, whether to commit `drift-report.md`) and recorded them in decision-001.
    - Avoids reconsidering a rejected or superseded approach: yes. It did not reopen "leave the drift unfixed" (decision-001's rejected alternative) or the dropped "Lichess required" rule. The Lichess requirement was modified as optional and it applied that as a new user decision, recorded it in decision-001 as "modified rather than applied as written", and kept the requirement dropped.
    - Proposes an appropriate next action: yes. After decision-002 it proposed starting decision-003 (reading both knowledge files first). After applying fixes it proposed the drift-investigator re-run or a commit.
  - Specific evidence supporting each score:
    - First reply: "Scope check passes. `.memory/SCOPE.md` names the ChessMind project (`no-kris/ChessMind`), and that matches this repo's git remote ... No review dates have passed. The earliest is 2027-02-01."
    - Decision-001: `git diff --ignore-all-space --stat` on the target files was empty (nothing applied yet); `git log` showed the 2026-11-02 revert after the 2026-11-01 report.
    - Writes: `.memory/project/decisions/decision-001.md` (progress section) and one line in `MEMORY_INDEX.md`. No writes to `.memory/knowledge/` or `.memory/reference/`.

**Pass / Fail result:**
  - Pass (3/3/3).

**Recall errors or misfires observed:**
  - Stale memory at commit time: decision-001 says "Fixes applied, not yet committed" and the index says "(uncommitted)", but both were committed in 3cae3da. It should have updated them before committing, or written them neutrally.
  - Unchecked repo claim: it said `testing-standards.md` had uncommitted edits, assumed to be the user's own. `git diff -w` shows line endings only.

**Cycle time:**
  - 1m21s

**Review time:**
  - 15m32s

**Cost per run (token counts if available):**
  - sess in: 1.80M out: 22.3k $: $1.32

**Relevant commit SHAs:**
  - 20fde5f - memory state at start (`main`).
  - 2b23729 - revert of position-builder to v0.2.0 (2026-11-02), the version the fixes were applied to.
  - 3cae3da - docs(positions): apply drift report fixes for decision 001 (branch `fix/drift-001-positions`).

**Observations:**
  - What worked: Startup order and checks were reported up front. The stale drift-report line numbers were caught by checking git history and the current file. Open intent decisions went to the user instead of being guessed, and memory was updated in place.
  - What failed: The agent reported that the changes in decison-001.md were uncommitted, but then commited them without updating.
  - What changed between runs: Run 001 was recall only. This run exercised resumption. Next run: fix the decision-001 status text, run the drift-investigator re-run, and test a deliberate stale review date or scope mismatch, which neither run has covered.

---
