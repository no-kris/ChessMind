# 1. Quality Rubric

## 1.1 Dimensions

### 1.1.1 Detection Accuracy

- Measures whether the agent finds real discrepancies from the target file and its directly referenced files, without inventing drift or missing obvious ones.

### Scoring Guide
1. Does not meet – Reports false drift or misses an obvious mismatch from the named file.

> Level 1 example: Claims the README and backend differ on the port, but both show 8000.

2. Partially meets – Finds some real drift, but misses clear claims or references from the target file.

> Level 2 example: Only checks commands in the README and ignores listed environment variables.

3. Meets – Verifies all relevant claims (if target is a doc) or all relevant doc references (if target is code) against only directly referenced files and reports real discrepancies.

> Level 3 example: Correctly catches a stale command by checking the referenced script and reports it with evidence.

4. Exceeds – Only reports verifiable drift within scope, with no false positives. Catches subtle issues while ignoring irrelevant files.

> Level 4 example: Finds a moved path that no longer exists, proves it’s unreferenced in scope, and doesn’t guess beyond it.

### 1.1.2 Evidence Quality

- Measures whether each finding has concrete locations and enough detail to be traceable.

### Scoring Guide

1. Does not meet – No file or line references are provided at all.

> Level 1 example: “The README is wrong about the backend.” with no locations.

2. Partially meets – Locations are only given on one side, or are vague (e.g. “backend config”).

> Level 2 example: Points to backend/ but doesn’t cite a specific file or line.

3. Meets – Every finding has file:line on both sides when they exist. If only one side exists, it is explicitly labeled (missing-doc or missing-code) with evidence.

> Level 3 example: “README.md:52 says uvicorn ... --port 8000; backend/app/main.py:11 reads from config.PORT with default 8000.”

4. Exceeds – Includes exact snippets, precise line ranges, and explicitly states what files were checked to reach the conclusion.

> Level 4 example: Quotes the exact claim and the exact code lines that contradict or confirm it, with context.

### 1.1.3 Classification & Recommendation

Measures correct use of classifications, quality of recommendations, and adherence to the “report only” rule.

### Scoring Guide

1. Does not meet – Uses incorrect classifications, gives no recommendations, or suggests making edits.

> Level 1 example: Labels drift as “fix now” and proposes changing code/docs.

2. Partially meets – Classifications are present, but recommendations are vague or rationales are missing.

> Level 2 example: “mismatch - fix this.” with no reasoning.

3. Meets – Every finding uses an allowed classification, has a recommendation and rationale, and never edits anything. The user is left to make the final decision.

> Level 3 example: “stale-reference - Prefer code (backend/app/main.py:23). The path scripts/start.sh no longer exists; command should be updated if desired. User decides.”

4. Exceeds – Rationale weighs both sides, notes tradeoffs, and uses ambiguous when evidence is insufficient after checking allowed files.

> Level 4 example: Explains why either side could be correct, cites the exact evidence checked, and explicitly states it’s ambiguous with no guess.

### Pass Threshold
- A run passes if it scores 3 or higher on all three dimensions.
- Reasoning: A report that does not include traceble and correctly classified disrepencies is of no use. All three dimensions are needed to produce a correct and trustable report.
