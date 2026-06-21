# ═══════════════════════════════════════════════════════
# 🧠 Auto Makah Agent OS — v1.0
# Rabei runs inside Auto Makah — code, files, git, deploy
# ═══════════════════════════════════════════════════════

import os, subprocess, tempfile, json, hashlib, logging, urllib.request
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

log = logging.getLogger("agent_os")

WORKSPACE_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "workspace")
os.makedirs(WORKSPACE_ROOT, exist_ok=True)


@dataclass
class ExecResult:
    success: bool
    output: str
    error: str = ""
    exit_code: int = 0
    files_affected: list = None

    def __post_init__(self):
        if self.files_affected is None:
            self.files_affected = []

    def to_dict(self) -> dict:
        return asdict(self)


# ═══ 1. FILE SYSTEM ═══

def fs_list(path: str = "/") -> list:
    """List workspace files — like `ls`."""
    full_path = _resolve(path)
    if not os.path.exists(full_path):
        return [{"error": f"Path not found: {path}"}]

    items = []
    if os.path.isdir(full_path):
        for name in sorted(os.listdir(full_path)):
            item_path = os.path.join(full_path, name)
            is_dir = os.path.isdir(item_path)
            items.append({
                "name": name,
                "type": "dir" if is_dir else "file",
                "size": os.path.getsize(item_path) if not is_dir else 0,
                "modified": datetime.fromtimestamp(os.path.getmtime(item_path)).isoformat(),
            })
    else:
        items.append({
            "name": os.path.basename(full_path),
            "type": "file",
            "size": os.path.getsize(full_path),
            "modified": datetime.fromtimestamp(os.path.getmtime(full_path)).isoformat(),
        })
    return items


def fs_read(path: str) -> ExecResult:
    """Read a file — like `cat`."""
    full_path = _resolve(path)
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return ExecResult(True, content[:50000])  # Max 50KB
    except Exception as e:
        return ExecResult(False, "", str(e))


def fs_write(path: str, content: str) -> ExecResult:
    """Write/create a file."""
    full_path = _resolve(path)
    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return ExecResult(True, f"Written {len(content)} bytes → {path}", files_affected=[path])
    except Exception as e:
        return ExecResult(False, "", str(e))


def fs_edit(path: str, old_text: str, new_text: str) -> ExecResult:
    """Edit a file — find and replace."""
    full_path = _resolve(path)
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if old_text not in content:
            return ExecResult(False, "", f"Text not found in {path}")

        new_content = content.replace(old_text, new_text, 1)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return ExecResult(True, f"Edited {path} ({len(content)} → {len(new_content)} bytes)", files_affected=[path])
    except Exception as e:
        return ExecResult(False, "", str(e))


def fs_delete(path: str) -> ExecResult:
    """Delete a file."""
    full_path = _resolve(path)
    try:
        if os.path.isfile(full_path):
            os.remove(full_path)
            return ExecResult(True, f"Deleted: {path}", files_affected=[path])
        return ExecResult(False, "", f"Not a file: {path}")
    except Exception as e:
        return ExecResult(False, "", str(e))


# ═══ 2. CODE EXECUTION ═══

def exec_python(code: str, timeout: int = 30) -> ExecResult:
    """Execute Python code in a sandboxed subprocess."""
    try:
        result = subprocess.run(
            ["python", "-c", code],
            capture_output=True, text=True,
            timeout=timeout,
            cwd=WORKSPACE_ROOT,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        output = result.stdout
        error = result.stderr
        if output and error:
            output = output + "\n" + error
        elif error:
            output = error

        return ExecResult(
            success=result.returncode == 0,
            output=output[:10000],
            exit_code=result.returncode,
        )
    except subprocess.TimeoutExpired:
        return ExecResult(False, "", "Timeout", exit_code=-1)
    except Exception as e:
        return ExecResult(False, "", str(e))


def exec_shell(command: str, timeout: int = 30) -> ExecResult:
    """Execute a shell command."""
    try:
        result = subprocess.run(
            command, shell=True,
            capture_output=True, text=True,
            timeout=timeout,
            cwd=WORKSPACE_ROOT,
        )
        return ExecResult(
            success=result.returncode == 0,
            output=(result.stdout + result.stderr)[:10000],
            exit_code=result.returncode,
        )
    except subprocess.TimeoutExpired:
        return ExecResult(False, "", "Timeout", exit_code=-1)
    except Exception as e:
        return ExecResult(False, "", str(e))


# ═══ 3. GIT OPERATIONS ═══

GIT_REPO = os.path.dirname(os.path.dirname(__file__))  # auto_makah repo


def git_status() -> ExecResult:
    """Show git status."""
    return exec_shell(f"cd {GIT_REPO} && git status --short")


def git_commit(message: str) -> ExecResult:
    """Stage all changes and commit."""
    result1 = exec_shell(f"cd {GIT_REPO} && git add -A")
    if not result1.success:
        return result1
    return exec_shell(f'cd {GIT_REPO} && git commit -m "{message}"')


def git_push() -> ExecResult:
    """Push to origin."""
    return exec_shell(f"cd {GIT_REPO} && git push")


def git_log(count: int = 5) -> ExecResult:
    """Show recent commits."""
    return exec_shell(f"cd {GIT_REPO} && git log --oneline -{count}")


# ═══ 4. DEPLOY ═══

def deploy_to_fly() -> ExecResult:
    """Deploy to Fly.io."""
    result = exec_shell(f"cd {GIT_REPO} && flyctl deploy --remote-only", timeout=180)
    return result


# ═══ 5. SELF-UPDATE (Agent can modify its own code) ═══

def self_read(path: str) -> ExecResult:
    """Read any file in the auto_makah project."""
    full_path = os.path.join(GIT_REPO, path)
    if not os.path.isfile(full_path):
        return ExecResult(False, "", f"File not found: {path}")
    with open(full_path, 'r', encoding='utf-8') as f:
        return ExecResult(True, f.read()[:50000])


def self_edit(path: str, old_text: str, new_text: str) -> ExecResult:
    """Edit any file in the auto_makah project."""
    full_path = os.path.join(GIT_REPO, path)
    return fs_edit(path, old_text, new_text)


# ═══ 6. Web Fetch ═══

def web_fetch(url: str) -> ExecResult:
    """Fetch a URL and return content."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "AutoMakah/1.0",
        })
        with urllib.request.urlopen(req, timeout=15) as r:
            data = r.read()
            # Try to decode
            content_type = r.headers.get("Content-Type", "")
            charset = "utf-8"
            if "charset=" in content_type:
                charset = content_type.split("charset=")[-1].split(";")[0].strip()
            try:
                text = data.decode(charset)
            except:
                text = data.decode('utf-8', errors='replace')
            return ExecResult(True, text[:20000])
    except Exception as e:
        return ExecResult(False, "", str(e))


# ═══ Helpers ═══

def _resolve(path: str) -> str:
    """Resolve a path — prevent directory traversal."""
    # Normalize and ensure within WORKSPACE_ROOT
    full = os.path.normpath(os.path.join(WORKSPACE_ROOT, path.lstrip("/")))
    # Security: ensure path stays within WORKSPACE_ROOT
    if not full.startswith(os.path.normpath(WORKSPACE_ROOT)):
        raise ValueError(f"Path traversal denied: {path}")
    return full


def get_capabilities() -> dict:
    """Return all available Agent OS capabilities."""
    return {
        "platform": "Auto Makah Agent OS",
        "version": "1.0.0",
        "capabilities": {
            "files": ["list", "read", "write", "edit", "delete"],
            "code": ["python", "shell", "javascript"],
            "git": ["status", "commit", "push", "log"],
            "deploy": ["fly"],
            "web": ["fetch"],
            "self": ["read", "edit", "deploy"],
        },
        "workspace": WORKSPACE_ROOT,
    }
