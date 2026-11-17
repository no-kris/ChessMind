"""MCP server for the ChessMind TDD orchestration lesson.

This server exposes the tools the pipeline roles use and enforces a role-based
allow-list loaded from mcp/roles.allowlist.json.

Roles (the five pipeline agents):
    orchestrator, planner, tester, implementer, reviewer

One server process runs per role. The role is fixed at launch by the
COURSETOOLS_ROLE environment variable (set per server in .mcp.json), never by
the caller: no tool takes a role argument. Each agent is granted only the tools
of its own role's server (mcp__coursetools_<role>__*), so which role a call
runs as is decided by the agent's tool grants, not by what the agent claims.
The server refuses to start without a known role.

Tools:
    file_read        Read a UTF-8 text file from the project root.
    file_write       Write a UTF-8 text file under the project root, limited
                     per role by mcp/write_scopes.json (see check_write_scope).
    codebase_search  Substring search over text files under the project root.
    git_status       Fixed `git status --short` for baselines and diff
                     attribution (no other git commands are available).
    test_runner      Fixed test commands. Detects the project type: a
                     package.json project runs `npm install` (if requested)
                     and `npm test`, or `npm run build` with suite="build";
                     a pyproject.toml project runs `uv run pytest`.
    shell            Simulated only — never executes anything. Kept so
                     students can observe an authorization denial; no role is
                     on its allow-list.

A call the role isn't allowed fails with an authorization error, so students
can still observe a denial (for example, any call to ``shell``). Only the fixed, allow-listed commands above
are ever executed; no arbitrary shell input is accepted. The server is
deliberately small and should be used only for local course exercises.
"""

from __future__ import annotations

import fnmatch
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

# Defaults are anchored to this file (mcp/ inside the project), not to the
# working directory, so the server behaves the same wherever it is launched.
SERVER_DIR = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("COURSETOOLS_ROOT", SERVER_DIR.parent)).resolve()
ALLOWLIST_PATH = Path(os.environ.get("COURSETOOLS_ALLOWLIST", SERVER_DIR / "roles.allowlist.json"))
WRITE_SCOPES_PATH = Path(os.environ.get("COURSETOOLS_WRITE_SCOPES", SERVER_DIR / "write_scopes.json"))

DEFAULT_ALLOWLIST: dict[str, list[str]] = {
    "file_read": ["planner", "implementer", "reviewer", "tester", "orchestrator"],
    "file_write": ["planner", "implementer", "reviewer", "tester", "orchestrator"],
    "codebase_search": ["planner", "implementer", "reviewer"],
    "git_status": ["orchestrator", "tester", "implementer", "reviewer"],
    "test_runner": ["tester"],
    "shell": [],
}


def load_allowlist() -> dict[str, list[str]]:
    if ALLOWLIST_PATH.exists():
        return json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
    return DEFAULT_ALLOWLIST


ALLOWLIST = load_allowlist()

# Per-role write scopes for file_write. Each entry is a path pattern relative
# to ROOT (`*` matches within one path segment, `**` matches any number of
# segments) and a mode:
#   write      create or overwrite
#   create     create only; refuse if the file already exists
#   untracked  create, or overwrite only files git does not track, so a role
#              can revise its own new files but never edit existing ones
DEFAULT_WRITE_SCOPES: dict[str, list[dict[str, str]]] = {
    "orchestrator": [{"pattern": "docs/orchestrator-runs/*/log.md", "mode": "write"}],
    "planner": [{"pattern": "docs/orchestrator-runs/*/spec.md", "mode": "write"}],
    "tester": [
        {"pattern": "backend/tests/**", "mode": "untracked"},
        {"pattern": "docs/orchestrator-runs/*/red-proof.md", "mode": "write"},
        {"pattern": "docs/orchestrator-runs/*/green-report-round-*.md", "mode": "create"},
        {"pattern": "docs/iteration-log-test-author.md", "mode": "write"},
    ],
    "implementer": [
        {"pattern": "backend/app/api/**", "mode": "untracked"},
        {"pattern": "backend/app/services/**", "mode": "untracked"},
        {"pattern": "docs/orchestrator-runs/*/implementer-log.md", "mode": "write"},
        {"pattern": "docs/iteration-log-endpoint-builder.md", "mode": "write"},
    ],
    "reviewer": [{"pattern": "docs/orchestrator-runs/*/review.md", "mode": "write"}],
}


def load_write_scopes() -> dict[str, list[dict[str, str]]]:
    if WRITE_SCOPES_PATH.exists():
        return json.loads(WRITE_SCOPES_PATH.read_text(encoding="utf-8"))
    return DEFAULT_WRITE_SCOPES


WRITE_SCOPES = load_write_scopes()

KNOWN_ROLES = set(WRITE_SCOPES) | {role for roles in ALLOWLIST.values() for role in roles}
ROLE = os.environ.get("COURSETOOLS_ROLE", "")
if ROLE not in KNOWN_ROLES:
    raise SystemExit(
        f"COURSETOOLS_ROLE must be one of {sorted(KNOWN_ROLES)}; got {ROLE!r}. "
        "Set it per server in .mcp.json."
    )

SERVER_NAME = f"coursetools_{ROLE}"
mcp = FastMCP(SERVER_NAME)


def authorize(tool_name: str) -> None:
    """Refuse the call unless this server's launch role is allowed the tool."""
    allowed_roles = ALLOWLIST.get(tool_name, [])
    if ROLE not in allowed_roles:
        raise PermissionError(
            f"Authorization error: role '{ROLE}' is not on the allow-list for {tool_name}. "
            f"Allowed roles: {allowed_roles or 'none'}."
        )


def safe_path(path: str) -> Path:
    candidate = (ROOT / path).resolve()
    # Compare path components, not strings: a string prefix check would let a
    # sibling such as /workspace-other through when ROOT is /workspace.
    if not candidate.is_relative_to(ROOT):
        raise ValueError(f"Path escapes the project root: {path}")
    return candidate


def _glob_match(parts: list[str], pattern: list[str]) -> bool:
    """Match path segments against pattern segments; `**` spans any number of segments."""
    if not pattern:
        return not parts
    if pattern[0] == "**":
        return any(_glob_match(parts[i:], pattern[1:]) for i in range(len(parts) + 1))
    return bool(parts) and fnmatch.fnmatchcase(parts[0], pattern[0]) and _glob_match(parts[1:], pattern[1:])


def _is_git_tracked(target: Path) -> bool:
    """True if git tracks the file. Fails closed: any git error counts as tracked."""
    rel = target.relative_to(ROOT).as_posix()
    code, _ = _run_fixed(["git", "ls-files", "--error-unmatch", "--", rel], ROOT)
    return code != 1


def check_write_scope(target: Path) -> None:
    """Refuse a write outside this server's role scopes in WRITE_SCOPES."""
    role = ROLE
    rel = target.relative_to(ROOT).as_posix()
    scopes = WRITE_SCOPES.get(role, [])
    for scope in scopes:
        if not _glob_match(rel.split("/"), scope["pattern"].split("/")):
            continue
        mode = scope["mode"]
        if mode == "create" and target.exists():
            raise PermissionError(
                f"Authorization error: role '{role}' may only create {rel}, and it already exists."
            )
        if mode == "untracked" and target.exists() and _is_git_tracked(target):
            raise PermissionError(
                f"Authorization error: role '{role}' may not overwrite {rel}: git tracks it "
                "(existing files are read-only for this role)."
            )
        if mode not in ("write", "create", "untracked"):
            raise PermissionError(f"Authorization error: unknown write mode '{mode}' for {rel}.")
        return
    allowed = [s["pattern"] for s in scopes]
    raise PermissionError(
        f"Authorization error: role '{role}' may not write {rel}. "
        f"Allowed paths: {allowed or 'none'}."
    )


@mcp.tool()
def file_read(path: str) -> str:
    """Read a UTF-8 text file from the project root."""
    authorize("file_read")
    target = safe_path(path)
    if not target.exists() or not target.is_file():
        raise FileNotFoundError(path)
    return target.read_text(encoding="utf-8")


@mcp.tool()
def file_write(path: str, content: str) -> str:
    """Write a UTF-8 text file under the project root, within this role's write scopes."""
    authorize("file_write")
    target = safe_path(path)
    check_write_scope(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Wrote {path} ({len(content)} bytes)."


@mcp.tool()
def codebase_search(query: str, root: str = ".", max_results: int = 20) -> list[dict[str, Any]]:
    """Search text files under the project root for a query string."""
    authorize("codebase_search")
    search_root = safe_path(root)
    results: list[dict[str, Any]] = []
    ignored_dirs = {".git", "node_modules", ".venv", "__pycache__"}

    for path in search_root.rglob("*"):
        if len(results) >= max_results:
            break
        if any(part in ignored_dirs for part in path.parts):
            continue
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        line_matches = []
        for number, line in enumerate(text.splitlines(), start=1):
            if query.lower() in line.lower():
                line_matches.append({"line": number, "text": line.strip()})
                if len(line_matches) >= 3:
                    break
        if line_matches:
            results.append({"path": str(path.relative_to(ROOT)), "matches": line_matches})
    return results


@mcp.tool()
def shell(command: str) -> str:
    """Simulate a shell command. This dummy server does not execute arbitrary commands."""
    authorize("shell")
    return f"Simulated shell command only; nothing executed: {command}"


TEST_TIMEOUT_SECONDS = int(os.environ.get("COURSETOOLS_TEST_TIMEOUT", "300"))
MAX_OUTPUT_CHARS = 20000


def _run_fixed(cmd: list[str], cwd: Path) -> tuple[int, str]:
    """Run one fixed, allow-listed command (no shell) and return (exit code, output)."""
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=TEST_TIMEOUT_SECONDS,
            env={**os.environ, "CI": "1", "FORCE_COLOR": "0"},
        )
    except subprocess.TimeoutExpired:
        return 124, f"Timed out after {TEST_TIMEOUT_SECONDS}s: {' '.join(cmd)}"
    except FileNotFoundError as exc:
        return 127, f"Command not found: {exc}"
    output = (proc.stdout or "") + (proc.stderr or "")
    if len(output) > MAX_OUTPUT_CHARS:
        output = "...[truncated]...\n" + output[-MAX_OUTPUT_CHARS:]
    return proc.returncode, output


@mcp.tool()
def git_status() -> str:
    """Run the fixed command `git status --short` in the project root.

    Used by pipeline roles to capture a baseline before a run and to
    attribute the diff afterwards. No other git commands are available.
    """
    authorize("git_status")
    code, out = _run_fixed(["git", "status", "--short"], ROOT)
    return f"== git status --short (exit {code}) ==\n{out or '(clean tree)'}"


@mcp.tool()
def test_runner(path: str = ".", suite: str = "default", install: bool = True) -> str:
    """Run a project's real test suite with fixed, allow-listed commands.

    The project type is detected from `path` (relative to the project root):
      - package.json  -> `npm install` (if `install`) then `npm test`;
                         with suite="build", `npm run build` instead of
                         `npm test` (frontend)
      - pyproject.toml -> `uv run pytest` (backend; `install` is implicit
                         in `uv run`). Lint is not run.

    Only these fixed commands are executed; no arbitrary shell input is
    accepted. Returns exit codes and the real command output.
    """
    authorize("test_runner")
    project_dir = safe_path(path)

    if (project_dir / "package.json").is_file():
        report: list[str] = [f"Project: {path} (node)"]
        if install:
            code, out = _run_fixed(["npm", "install", "--no-audit", "--no-fund"], project_dir)
            report.append(f"== npm install (exit {code}) ==\n{out}")
            if code != 0:
                report.append("RESULT: ERROR (install failed; tests not run)")
                return "\n".join(report)
        if suite == "build":
            code, out = _run_fixed(["npm", "run", "build"], project_dir)
            report.append(f"== npm run build (exit {code}) ==\n{out}")
            report.append(f"RESULT: {'PASS' if code == 0 else 'FAIL'} (npm run build exit code {code})")
            return "\n".join(report)
        code, out = _run_fixed(["npm", "test"], project_dir)
        report.append(f"== npm test (exit {code}) ==\n{out}")
        report.append(f"RESULT: {'PASS' if code == 0 else 'FAIL'} (npm test exit code {code})")
        return "\n".join(report)

    if (project_dir / "pyproject.toml").is_file():
        report = [f"Project: {path} (python)"]
        code, out = _run_fixed(["uv", "run", "pytest"], project_dir)
        report.append(f"== uv run pytest (exit {code}) ==\n{out}")
        report.append(f"RESULT: {'PASS' if code == 0 else 'FAIL'} (uv run pytest exit code {code})")
        return "\n".join(report)

    raise FileNotFoundError(f"No package.json or pyproject.toml in {path}")


if __name__ == "__main__":
    mcp.run()
