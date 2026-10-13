
## Development Setup (Docker)

## Prereqs

### 1. Install [Docker](https://docs.docker.com/get-docker/). 
### 2. Clone the repository: 
Choose a directory to clone the project
```bash 
git clone https://github.com/no-kris/ChessMind.git cd ChessMind
```


The dev container provides Python 3.13, uv, Node 22, Stockfish, and Claude Code. Source code is **not** copied into the image; mount the repository at `/workspace`.

### 1. Build the image

```bash
docker build -t chessmind .
```

### 2. Run the container

```bash
docker run -it --rm \
  -v "$(PWD)":/workspace \
  -v claude-auth:/claude-auth \
  -v chessmind-node-modules:/workspace/frontend/node_modules \
  -v chessmind-venv:/opt/venv \
  -p 8000:8000 \
  -p 5173:5173 \
  --env-file backend/.env \
  chessmind
```

- `-v "$(PWD)":/workspace` mounts the repo so edits on the host show up in the container.
- `-v claude-auth:/claude-auth` is a named volume that keeps your Claude Code login between runs. You log in once on the first run; after that the entrypoint restores the credentials automatically.
- `-v chessmind-node-modules:/workspace/frontend/node_modules` keeps the frontend's installed packages in a named volume instead of the host folder. This keeps Linux-built packages separate from any `node_modules` on the host, avoids slow bind-mount file access, and lets `npm ci` be skipped on later runs when `package-lock.json` hasn't changed.
- `-v chessmind-venv:/opt/venv` keeps the Python virtual environment between runs, so `uv sync` only installs what changed instead of starting from scratch.
- `--env-file backend/.env` injects environment variables needed for development into the container. **Security Risk** Do not store sensitive information. Keep it strictly for development/testing porpuses.
- Ports `8000` (backend) and `5173` (frontend) are published to the host.

On start, the container runs `uv sync` in `backend/` (installing Python dependencies into `/opt/venv`) and `npm ci` in `frontend/` when `package-lock.json` has changed, then drops you into a bash shell.

### 3. Start the apps

Open two shells in the container (for example, `docker exec -it <container> bash` for the second one).

```bash
# Backend: http://localhost:8000
cd /workspace/backend
uv run uvicorn app.main:app --reload 0.0.0.0 --port 8000
```

```bash
# Frontend: http://localhost:5173
cd /workspace/frontend
npm run dev
```

The Vite dev server proxies `/api` requests to `http://localhost:8000`, so the frontend calls the backend without extra configuration.

### 4. Check it works

- `http://localhost:8000/` returns `{"message": "ChessMind API up and running."}`
- `http://localhost:8000/docs` shows the interactive API docs.


## Environment Variables

The backend loads a `.env` file from `backend/` if one exists (`.env` files are git- and docker-ignored).

| Variable | Default | Purpose |
| --- | --- | --- |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated list of origins allowed to call the API. |


## Running Tests

```bash
cd /workspace/backend
uv run pytest
```



## Linting

```bash
# Backend lint
cd backend && uv run ruff check .

# Frontend lint / production build
cd frontend && npm run lint
cd frontend && npm run build
```
