# ChessMind Agent Sandbox Setup Guide

## 1. Setup & Execution Instructions

### Prerequisites
* Ensure [Docker](https://docs.docker.com/get-docker/) is running on your machine.
* Open your terminal in the root directory of your ChessMind repository.
* Docker Compose v2 is required (`docker compose version`).

### Build Command
Build the custom Docker image locally:
```bash
docker build -t chessmind .
```

### Start the egress proxy

The sandbox uses a tinyproxy sidecar as its only route to the internet. It is attached to two networks:

* `chessmind-net` — internal, no gateway. The dev container lives here.
* `chessmind-egress` — normal bridge. Only the proxy is attached.

Start the proxy first. This also creates both networks:
```bash
docker compose up -d proxy
docker compose ps
docker compose logs proxy
```

The allowlist is in [`filter`](./filter); the proxy config is in
[`tinyproxy.conf`](./tinyproxy.conf). After editing `filter`, restart the proxy:
```bash
docker compose restart proxy
```

> If you previously created `chessmind-net` or `chessmind-egress` manually,
> remove them before the first `docker compose up` so Compose can manage them:
> ```bash
> docker compose down
> docker compose up -d proxy
> ```


### Run the dev container

The container has no direct route to the internet. It reaches Anthropic and the
package registries only through `proxy:8888`.

#### Option A: Bash (Linux / macOS / WSL)
```bash
docker run -it --rm --network chessmind-net \
  -e HTTP_PROXY=http://proxy:8888 \
  -e HTTPS_PROXY=http://proxy:8888 \
  -e http_proxy=http://proxy:8888 \
  -e https_proxy=http://proxy:8888 \
  -e NO_PROXY=localhost,127.0.0.1,::1 \
  -v "${PWD}:/workspace" \
  -v claude-auth:/claude-auth \
  -v chessmind-node-modules:/workspace/frontend/node_modules \
  -v chessmind-venv:/opt/venv \
  -p 8000:8000 -p 5173:5173 \
  chessmind
```

#### Option B: Windows (PowerShell)
```powershell
docker run -it --rm --network chessmind-net `
  -e HTTP_PROXY=http://proxy:8888 `
  -e HTTPS_PROXY=http://proxy:8888 `
  -e http_proxy=http://proxy:8888 `
  -e https_proxy=http://proxy:8888 `
  -e NO_PROXY=localhost,127.0.0.1,::1 `
  -v "${PWD}:/workspace" `
  -v claude-auth:/claude-auth `
  -v chessmind-node-modules:/workspace/frontend/node_modules `
  -v chessmind-venv:/opt/venv `
  -p 8000:8000 -p 5173:5173 `
  chessmind
```

#### Option C: Docker Compose
```bash
docker compose run --rm --service-ports dev
```

---

## Installed Dependencies

The `Dockerfile` sets up a dedicated, minimal environment for the ChessMind backend (Python/Stockfish) and frontend (Node.js/Vite), while installing the Claude Code agent CLI.

### Included Dependencies & Tools:
* **Base:** `python:3.13-slim`, Node.js 22 LTS
* **Package Managers:** `uv` (for fast Python package management), `npm`
* **Agent CLI:** Claude Code (`@anthropic-ai/claude-code`)
* **Project Binaries & Utilities:** Stockfish (chess evaluation engine), `ripgrep`, `jq`, `procps`, `git`, `curl`, `ca-certificates`

### Summary of Configuration Parameters

Mounted Path: Only the host ChessMind repository directory is mapped into /workspace. Unrelated host directories, personal files, and system credentials remain strictly excluded and unmounted.

Network Mode: The container is attached only to `chessmind-net`, an internal Docker network with no gateway. Its only reachable peer is the `proxy` container, which is homed on `chessmind-egress`. tinyproxy enforces the allowlist in `filter` (`FilterDefaultDeny Yes`) and permits only HTTPS (`ConnectPort 443`). Domains not listed are denied with HTTP 403, and there is no direct route to bypass the proxy. The host itself is not restricted.

Storage Distinction:

  - --rm removes only the container’s writable layer. Named volumes such as claude-auth and opt/venv persist even though they are outside /workspace.

  - Named volumes (claude-auth, chessmind-venv, chessmind-node-modules) explicitly isolate Claude authentication tokens and Python/Node dependencies outside /workspace while persisting them across container restarts.

---

## 2. Smoke Test & Network Verification

### Network Egress Restriction Check

A blocked domain returns tinyproxy's 403 page:
```bash
root@18e19a5eff86:/workspace# curl -f https://www.example.com
curl: (22) The requested URL returned error: 403
```

There is also no direct route around the proxy:
```bash
root@18e19a5eff86:/workspace# curl --noproxy '*' https://www.example.com
curl: (6) Could not resolve host: www.example.com
```


### Anthropic API Reachability Check

Access to Anthropic Claude API for agentic capabilities is allowed:
```bash
root@18e19a5eff86:/workspace# claude -p "Reply with exactly: OK"
OK
```

A `401` means the request reached Anthropic and was rejected only for a missing API key:
```bash
root@18e19a5eff86:/workspace# curl -o /dev/null -w '%{http_code}\n' https://api.anthropic.com/v1/models
401
```

What the codes mean:

* `401` — reachable (no API key supplied)
* `403` — blocked by tinyproxy
* `000` / `curl: (56)` — tunnel failed
* `curl: (6)` — no direct route (proxy bypassed)

### Smoke Test Prompt

(Example: Asking Claude to summarize the repository structure)
- Prompt given to agent: Summarize the ChessMind repository structure and write the summary to /workspace/agent-summary.md.

### Terminal Output

root@18e19a5eff86:/workspace# claude

❯ Summarize the ChessMind repository structure and write the summary to /workspace/agent-summary.md.

I wrote the summary to /workspace/agent-summary.md.

ChessMind is an early-stage AI chess coach, and it has three main parts ... 

[Container]

root@18e19a5eff86:/workspace# ls -la agent-summary.md
-rw-r--r-- 1 root root 5862 Nov  1 21:31 agent-summary.md

[Host]

ls .\agent-summary.md

    Directory: C:\Users\17278\FullStackWeb\ChessMind

Mode                 LastWriteTime         Length Name
----                 -------------         ------
-a---           11/1/2026  4:31 PM           5862 agent-summary.md


## 3. File Boundary Check

From the host, inspect the container's mounts:
```bash
root@18e19a5eff86:/workspace# ls
Dockerfile        ai_chess_coach_project_plan.md  docker-entrypoint.sh  frontend          setup.md
README.md         backend                         docs                  session_tasks.md  statusline.sh
agent-summary.md  docker-compose.yml              filter                settings.json     tinyproxy.conf
```

Check that system host paths cannot be accessed from the container:
```bash
root@18e19a5eff86:/workspace# ls ~/host
ls: cannot access '/root/host': No such file or directory

root@18e19a5eff86:/workspace# ls ~/mnt/c
ls: cannot access '/root/mnt/c': No such file or directory
```

Write a file inside `/workspace`:
```bash
root@18e19a5eff86:/workspace# echo "persistence check" > /workspace/persistence-check.txt
root@18e19a5eff86:/workspace# cat /workspace/persistence-check.txt
persistence check
root@18e19a5eff86:/workspace#
```

Exit and start a fresh container with the same mount:
```bash
root@18e19a5eff86:/workspace# exit

$ docker run --rm -v "${PWD}:/workspace" chessmind cat /workspace/persistence-check.txt
persistence check
```

The file survives because `/workspace` is the host repository, not the container's writable layer.

Host-side confirmation:
```powershell
PS C:\Users\17278\FullStackWeb\ChessMind> Get-Content .\persistence-check.txt
persistence check
```

Create files in the container's ephemeral layer and in `/tmp`:
```bash
root@18e19a5eff86:/workspace# echo "container-local" > /root/scratch.txt
root@18e19a5eff86:/workspace# echo "temp" > /tmp/scratch.txt
root@18e19a5eff86:/workspace# ls -la /root/scratch.txt /tmp/scratch.txt
-rw-r--r-- 1 root root 16 Nov  2 17:27 /root/scratch.txt
-rw-r--r-- 1 root root  5 Nov  2 17:27 /tmp/scratch.txt
```


Exit that container and start a fresh one with the same workspace mount:
```bash
root@18e19a5eff86:/workspace# exit

$ docker run --rm -v "${PWD}:/workspace" chessmind sh -c 'cat /root/scratch.txt; cat /tmp/scratch.txt'
cat: /root/scratch.txt: No such file or directory
cat: /tmp/scratch.txt: No such file or directory
```

The workspace file is still there:
```bash
$ docker run --rm -v "${PWD}:/workspace" chessmind ls -la /workspace/persistence-check.txt
-rw-r--r-- 1 root root 18 Nov  2 17:21 /workspace/persistence-check.txt
```

This confirms the persistence boundary:
- `/workspace` is a host bind mount and persists across containers.
- `/root` and `/tmp` are part of the container's writable layer; `--rm` discards them when the container exits.
- Named volumes (`claude-auth`, `chessmind-venv`, `chessmind-node-modules`) persist independently.
