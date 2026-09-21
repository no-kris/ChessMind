# AI Chess Coach — Project Implementation Plan

## Overview
An instructional web application that combines standard board state engines, Stockfish tactical evaluation, a Python backend, a React frontend, and a Large Language Model (LLM) coaching layer to deliver real-time move explanations and positional feedback.

The app is **session-only and stateless-by-design**: no user accounts, and nothing persists after a game ends. Game state lives in memory for the duration of a session, and all evaluation/coaching results are held in in-memory caches (cleared on page close or server restart).

---

## 1. Technical Stack Architecture

| Layer | Recommended Tech | Purpose & Key Functions |
| :--- | :--- | :--- |
| **Web Frontend** | React (`react-chessboard`) | Single Page Application (SPA) providing an interactive board UI, move annotations, and coach feedback panel. |
| **Backend Logic** | Python 3.10+ (FastAPI) | REST service managing game flow, engine communication, tactical detection, and on-demand LLM prompting. |
| **Chess Engine** | `python-chess` | Python board representation, legal move validation, FEN/PGN parsing, and positional queries. |
| **Evaluation Engine** | Stockfish UCI (Python Driver) | Deep evaluation analysis, centipawn scoring, and top recommended lines executed via Python subprocesses. |
| **AI Coach Agent** | OpenAI SDK | Translates evaluation deltas and tactical motifs into move explanations using a provider-agnostic OpenAI-compatible client. |

---

## 2. Step-by-Step Implementation Roadmap


### Phase 1: Python Backend & React Setup
- [ ] Initialize repository structure with a Python backend (FastAPI/Flask) and React SPA frontend.
- [ ] Install core backend dependencies (`python-chess`, engine drivers, HTTP client for custom LLM).
- [ ] Build Python REST API endpoints to accept moves from React and manage board state.
- [ ] Implement FEN/PGN utilities for state synchronization between React client and Python server.
- [ ] Maintain an **in-memory session game store** keyed by a session ID (created per game, dropped when the session ends). No database — nothing persists after the game.
- [ ] Keep the move endpoint **stateless**: the client sends `FEN + move`, the backend returns the analysis. Game history for the "Why?" button lives only in the session store.

### Phase 2: Stockfish & Python Integration
- [ ] Configure Stockfish binary execution using Python's `python-chess.engine` wrapper.
- [ ] Implement asynchronous engine queries to compute top-N evaluation lines without blocking API threads.
- [ ] Normalize evaluation scores (centipawns and forced mates) within the Python engine handler.
- [ ] Add an **evaluation cache** keyed by canonical FEN + depth + multiPV (in-memory LRU/TTL). Transpositions and revisited positions skip engine calls.
- [ ] **One engine call per move:** the position before a move is the position after the previous move, so the pre-move `E_best` analysis is a cache hit. Only the resulting position needs a fresh engine query.

### Phase 3: Python Tactical Motif Detection
- [ ] Implement pin detection using `board.is_pinned()` and custom relative pin calculations in Python.
- [ ] Build multi-target fork analysis for knight, pawn, and major piece threats in backend modules.
- [ ] Evaluate open/semi-open file control and major piece positioning within board evaluation routines.

### Phase 4: Evaluation Pipeline & Delta Classification
- [ ] Calculate Evaluation Loss Delta with **perspective normalization**: `ΔE = E_best − (−E_result)`. Evaluate both scores from the mover's perspective (`+E` = good for the mover), so the *played* move's score from the resulting position (where the opponent is to move) is negated before subtracting. Convert forced mates to the centipawn scale defined in Phase 2.
- [ ] Categorize moves into buckets:
  - **Good / Optimal:** $< 30 \text{ centipawns}$
  - **Inaccuracy:** $30\text{--}99 \text{ centipawns}$
  - **Mistake:** $100\text{--}299 \text{ centipawns}$
  - **Blunder:** $\ge 300 \text{ centipawns}$
- [ ] Bundle board FEN, move metrics, and tactical alerts into a standardized JSON payload in Python. This payload is returned to the UI **after every move without calling the LLM**.

### Phase 5: On-Demand LLM Coaching Pipeline
- [ ] Re-scope the LLM to an **on-demand "Why?" endpoint**: `POST /api/coach/explain` with `{ game_id, move_id }`. No LLM request is made on the per-move path.
- [ ] Server-side, reassemble the **structured JSON context** for the requested move:
  ```json
  {
    "fen": "<canonical fen>",
    "move": "e2e4",
    "delta_cp": 150,
    "bucket": "mistake",
    "tactical_alerts": ["pin", "fork"],
    "best_line": "e2e4 e7e5 ...",
    "prompt_version": 1,
    "schema_version": 1
  }
  ```
- [ ] Use the **OpenAI Python SDK** with a provider-agnostic client: `base_url`, `api_key`, and `model` come from env vars. Configure Groq for testing (`https://api.groq.com/openai/v1`, e.g. `llama-3.3-70b-versatile`) and OpenAI for production (default endpoint, e.g. `gpt-4o-mini`).
- [ ] Enforce a **schema-constrained, structured JSON response** via SDK JSON mode (`response_format={"type":"json_object"}`) and prompt instructions:
  ```json
  {
    "verdict": "Mistake — 150 CP lost.",
    "praise": "Opening the f-file was the right plan.",
    "concern": "Bb5 walks into the pin.",
    "tip": "Consider a3 → b4 to challenge the open file."
  }
  ```
  Keep output short and informative: `verdict` one short sentence, `tip` one sentence, `praise`/`concern` at most a phrase. No extended prose.
- [ ] Add an **LLM explanation cache** keyed by a hash of `FEN + move + bucket + tactical alerts + prompt_version + schema_version`. Re-clicks are instant; version bumps invalidate stale responses.
- [ ] Implement **offline fallback logic**: on API failure or timeout, return a templated explanation built from the bucket and tactical alerts so the "Why?" button always responds.

### Phase 6: React UI Integration
- [ ] Connect React Web UI to Python backend using `react-chessboard` for rendering moves and state.
- [ ] Build interactive UI components in React for displaying move annotations and a **compact coach card** (verdict/praise/concern/tip) driven by the structured JSON response.
- [ ] Add a **"Why?" button** per move (or on the last move). On click, fire the on-demand `POST /api/coach/explain`; show a loading state and disable the button while a request is pending. Per-move analysis (badge + tactical alerts) is already displayed without any LLM call.
- [ ] Perform end-to-end testing across opening, middlegame tactical, and endgame scenarios.

---

## 3. System Data Flow Architecture

Two request paths: the engine-only per-move path and the on-demand LLM path. Both are backed by in-memory caches.

### Per-move path (no LLM, sub-second)
- **React Web UI** → sends `FEN + move` to **Python API Backend**
  - **Stockfish Engine** — evaluates the resulting position, cached by canonical FEN
  - **python-chess Tactics** — detects pins, forks, file control
  - **ΔE Normalization & Bucket Classification** — computes `ΔE = E_best − (−E_result)` and the move bucket
  - **In-memory Session Game Store** — records the analyzed move (referenced by "Why?" on demand)
  - Returns **JSON Analysis Payload** (badge + tactics) to React UI

### On-demand "Why?" path (LLM only on click)
- **React** → `POST /api/coach/explain {game_id, move_id}` → **Python API Backend**
  - Reassemble structured JSON context from the session store + caches (FEN, move, delta, bucket, tactics, best line)
    - **LLM Explanation Cache** (key: FEN + move + bucket + tactics + prompt/schema version) → hit returns directly
    - **OpenAI SDK Client** (Groq for testing, OpenAI in prod) → miss calls the LLM
  - Returns **Schema-Constrained JSON Response** (verdict / praise / concern / tip)
  - **React UI** — renders the compact coach card

### Key Implementation Takeaways
- The React client handles UI rendering and user interactions; the Python backend coordinates Stockfish evaluation, `python-chess` tactical analysis, and on-demand LLM prompt generation.
- **Stateless and session-only:** no accounts, no database, no persistence after a game ends. All state is in-memory and cleared when the session ends.
- **Engine-first, LLM-second:** every move gets instant engine analysis; the LLM is invoked only when the user asks "Why?".
