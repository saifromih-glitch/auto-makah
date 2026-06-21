# ═══════════════════════════════════════════════════════
# 🌳 Worktree Isolation — Lopp Step 6
# Each agent gets its own isolated workspace
# Prevents file collisions, enables parallel work
# ═══════════════════════════════════════════════════════

import os, tempfile, shutil, json, logging, hashlib
from datetime import datetime

log = logging.getLogger("worktree")


class AgentWorkspace:
    """
    Lopp Step 6: Isolated workspace per agent.
    
    Problem: Multiple agents modifying same files = merge conflicts, data corruption.
    Solution: Each agent gets its own temp workspace, then results are merged.
    """

    def __init__(self, agent_id: str, base_dir: str = None):
        self.agent_id = agent_id
        self.base_dir = base_dir or os.path.join(tempfile.gettempdir(), "auto_makah_worktrees")
        self.workspace_path = os.path.join(self.base_dir, f"agent_{agent_id}")
        self.created_at = datetime.now().isoformat()
        self._ensure_exists()

    def _ensure_exists(self):
        """Create workspace if it doesn't exist."""
        if not os.path.exists(self.workspace_path):
            os.makedirs(self.workspace_path, exist_ok=True)
            log.info(f"Created workspace for agent '{self.agent_id}': {self.workspace_path}")

    def write_file(self, filename: str, content: str):
        """Write a file in the agent's isolated workspace."""
        path = os.path.join(self.workspace_path, filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return path

    def read_file(self, filename: str) -> str | None:
        """Read a file from the agent's workspace."""
        path = os.path.join(self.workspace_path, filename)
        if not os.path.isfile(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def list_files(self) -> list:
        """List all files in the workspace."""
        files = []
        for root, _, filenames in os.walk(self.workspace_path):
            for fn in filenames:
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, self.workspace_path)
                files.append({
                    "path": rel,
                    "size": os.path.getsize(full),
                    "modified": datetime.fromtimestamp(os.path.getmtime(full)).isoformat()
                })
        return files

    def diff_with(self, other_workspace: "AgentWorkspace") -> dict:
        """Compare files between two workspaces — find conflicts."""
        my_files = {f["path"] for f in self.list_files()}
        other_files = {f["path"] for f in other_workspace.list_files()}
        
        conflicts = my_files & other_files
        only_mine = my_files - other_files
        only_theirs = other_files - my_files

        # Check content conflicts
        actual_conflicts = []
        for path in conflicts:
            my_content = self.read_file(path)
            their_content = other_workspace.read_file(path)
            if my_content != their_content:
                actual_conflicts.append({
                    "path": path,
                    "my_hash": hashlib.md5(my_content.encode()).hexdigest()[:8],
                    "their_hash": hashlib.md5(their_content.encode()).hexdigest()[:8],
                })

        return {
            "conflicts": actual_conflicts,
            "only_mine": list(only_mine),
            "only_theirs": list(only_theirs),
            "shared": len(conflicts) - len(actual_conflicts),
        }

    def cleanup(self):
        """Remove the workspace."""
        if os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path)
            log.info(f"Cleaned up workspace for agent '{self.agent_id}'")

    def snapshot(self) -> dict:
        """Return a snapshot of the workspace state."""
        return {
            "agent_id": self.agent_id,
            "path": self.workspace_path,
            "created_at": self.created_at,
            "files_count": len(self.list_files()),
        }


class WorktreeManager:
    """
    Lopp Step 6: Manages multiple agent workspaces.
    
    Orchestrates parallel agent work without collisions.
    Merges results when ready.
    """

    def __init__(self):
        self.workspaces: dict[str, AgentWorkspace] = {}
        self.state_file = os.path.join(tempfile.gettempdir(), "auto_makah_worktrees_state.json")

    def get_workspace(self, agent_id: str) -> AgentWorkspace:
        """Get or create a workspace for an agent."""
        if agent_id not in self.workspaces:
            self.workspaces[agent_id] = AgentWorkspace(agent_id)
        return self.workspaces[agent_id]

    def get_all_snapshots(self) -> list:
        """Get snapshots of all active workspaces."""
        return [ws.snapshot() for ws in self.workspaces.values()]

    def check_conflicts(self, agent_a: str, agent_b: str) -> dict:
        """Check for conflicts between two agent workspaces."""
        ws_a = self.get_workspace(agent_a)
        ws_b = self.get_workspace(agent_b)
        return ws_a.diff_with(ws_b)

    def merge_to_target(self, agent_id: str, target_dir: str) -> list:
        """Copy agent workspace files to target directory. Returns list of copied files."""
        ws = self.get_workspace(agent_id)
        copied = []
        for f in ws.list_files():
            src = os.path.join(ws.workspace_path, f["path"])
            dst = os.path.join(target_dir, f["path"])
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            copied.append(f["path"])
        log.info(f"Merged {len(copied)} files from agent '{agent_id}' to {target_dir}")
        return copied

    def cleanup_all(self):
        """Clean up all workspaces."""
        for ws in list(self.workspaces.values()):
            ws.cleanup()
        self.workspaces.clear()

    def save_state(self):
        """Save workspace manager state."""
        state = {
            "workspaces": {k: v.snapshot() for k, v in self.workspaces.items()},
            "updated_at": datetime.now().isoformat(),
        }
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def load_state(self) -> dict:
        """Load workspace manager state."""
        if not os.path.isfile(self.state_file):
            return {"workspaces": {}}
        with open(self.state_file, 'r', encoding='utf-8') as f:
            return json.load(f)


# ═══ Quick integration ═══
_global_manager = None

def get_worktree_manager() -> WorktreeManager:
    """Get or create the global worktree manager."""
    global _global_manager
    if _global_manager is None:
        _global_manager = WorktreeManager()
    return _global_manager
