# ChessMind Agent Sandbox Setup Guide

## 1. Setup & Execution Instructions

### Prerequisites
* Ensure [Docker](https://docs.docker.com/get-docker/) is running on your machine.
* Open your terminal in the root directory of your ChessMind repository.

### Build Command
Build the custom Docker image locally:
```bash
docker build -t chessmind .
```

### Run Command

Start the container with your explicit filesystem mounts, persistent volumes, and network configuration:

```bash
docker run -it --rm \
  -v ${PWD}:/workspace \
  -v claude-auth:/claude-auth \
  -v chessmind-node-modules:/workspace/frontend/node_modules \
  -v chessmind-venv:/opt/venv \
  -p 8000:8000 \
  -p 5173:5173 \
  chessmind
```

---

## Installed Dependencies

The `Dockerfile` sets up a dedicated, minimal environment tailored for the ChessMind backend (Python/Stockfish) and frontend (Node.js/Vite), while installing the Claude Code agent CLI.

### Included Dependencies & Tools:
* **Base:** `python:3.13-slim`, Node.js 22 LTS
* **Package Managers:** `uv` (for fast Python package management), `npm`
* **Agent CLI:** Claude Code (`@anthropic-ai/claude-code`)
* **Project Binaries & Utilities:** Stockfish (chess evaluation engine), `ripgrep`, `jq`, `procps`, `git`, `curl`, `ca-certificates`

### Summary of Configuration Parameters

Mounted Path: The host ChessMind repository directory is mapped to /workspace.

Network Mode: Standard default network enabled to allow outbound HTTPS communication with the Anthropic API required by Claude Code.

---

## 2. Smoke Test & Verification

### Smoke Test Prompt

(Example: Asking Claude to summarize the repository structure)
- Prompt given to agent: Summarize the ChessMind repository structure and write the summary to /workspace/agent-summary.md.

### Terminal Output
root@b34941e100ca:/workspace# claude

❯ Summarize the ChessMind repository structure and write the summary to /workspace/agent-summary.md.

I wrote the summary to /workspace/agent-summary.md.

ChessMind is an early-stage AI chess coach, and it has three main parts ... 

[Container]

root@b34941e100ca:/workspace# ls -la agent-summary.md
-rw-r--r-- 1 root root 5862 Nov  1 21:31 agent-summary.md

[Host]

ls .\agent-summary.md

    Directory: C:\Users\17278\FullStackWeb\ChessMind

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a---           11/1/2026  4:31 PM           5862 agent-summary.md
