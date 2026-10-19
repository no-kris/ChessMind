# 1. Quality Rubric

## 1.1 Dimensions

### 1.1.1 Lint Result Accuracy 
- Measures whether the agent’s stated lint outcome matches ruff’s actual result. A high score requires the stated pass/fail to be correct and backed by evidence from the run.

### Scoring Guide
1. Does not meet – The agent reports the wrong outcome, or no outcome at all.

- Level 1 example: Agent output reads: “Lint passed — no issues.” ruff actually exited 1 with three findings.

2. Partially meets – The agent gestures at a result without committing to pass/fail.

- Level 2 example: Agent output reads: “ruff ran with a few style notes.” The exit code was 1 with two errors.

3. Meets – The agent correctly states whether lint passed or failed.

- Level 3 example: Agent output reads: “ruff failed with two errors.” This matches exit code 1.

4. Exceeds – The agent states the correct outcome and supports it with evidence.

- Level 4 example: Agent output reads: “uv run ruff check . exited 1 with 2 errors (F401 ×1, F821 ×1).” Correct result plus exit code, command, and counts.

### 1.1.2 Finding Completeness 
- Measures whether the agent captured every finding in the lint output with enough detail to locate it. A high score requires all findings, each with file, line, and rule code.

### Scoring Guide
1. Does not meet – The agent omits one or more findings, leaving an incomplete or misleading picture.

- Level 1 example: ruff reports three findings but the agent only reports “one issue found.”

2. Partially meets – The agent lists all findings but without location or rule code for some.

- Level 2 example: Agent output reads: “Issues: unused import, line too long, undefined name.” No file, line, or rule code is given.

3. Meets – Every finding is listed with file, line, and rule code.

- Level 3 example: Agent output reads: “app/main.py:7 F401; app/services/engine.py:12 E501; app/services/classify.py:3 F821.”

4. Exceeds – Every finding is listed with location and rule code, and the agent distinguishes auto-fixable from manual findings.

- Level 4 example: Agent output reads: “3 findings: main.py:7 F401 (auto-fixable); engine.py:12 E501 (manual); classify.py:3 F821 (manual).”

### 1.1.3 Recommendation Quality 
- Measures whether each finding receives a correct, specific suggested fix. The agent may recommend fixes but it can NOT apply them. Whether it applied fixes is a pass/fail gate in the PRD.

### Scoring Guide
1. Does not meet – The agent gives no recommendations or gives wrong/irrelevant ones.

- Level 1 example: Agent output reads: “Fix the lint errors before merging.” No finding is addressed.

2. Partially meets – The agent recommends fixes for some findings, but they are vague and unhelpful.

- Level 2 example: Agent output reads: “Remove unused imports and tidy up formatting.” This does not address the specific rule codes or files.

3. Meets – Each finding has a correct, specific recommended fix.

- Level 3 example: Agent output reads: “F401: delete the unused os import. E501: wrap the line at 12. F821: define foo or import it.”

4. Exceeds – Each recommendation is correct and specific, and explains why the fix matters or the tradeoff involved.

- Level 4 example: Agent output reads: “F401: remove the unused os import. F821: define foo before use — this is a runtime NameError, so it is the only blocking issue. E501: wrap the line; cosmetic and safe to defer.”

**Pass threshold:**
- A run passes if it scores 3 or higher on all four dimensions.
- Reasoning: Accuracy and Completeness are primary. A summary that misrepresents the result or hides findings is unusable. Recommendation Quality depends on those being correct, so a dimension floor prevents a well written report of a wrong or incomplete result from passing.

**Notes on Threshold Design:**
- Considered an aggregate minimum (9/12). Ruled out because it would let a run scoring 1 on Lint Result Accuracy pass if it scored 4 on the other two.
