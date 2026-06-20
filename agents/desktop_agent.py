# ═══════════════════════════════════════════
# 🕋 Auto Makah — Desktop Agent (Phase 5)
# System Tray + File System + Local Tools
# ═══════════════════════════════════════════

import sys
import os
import json
import time
import asyncio
import subprocess
import threading
import webbrowser
from pathlib import Path
from datetime import datetime
from typing import Optional


class DesktopAgent:
    """Local desktop agent — system tray, file system, notifications."""

    HOME = Path.home()
    APP_DIR = HOME / ".auto-makah"
    CONFIG_FILE = APP_DIR / "config.json"
    LOG_FILE = APP_DIR / "agent.log"

    DEFAULT_CONFIG = {
        "api_url": "https://auto-makah.fly.dev",
        "api_key": "",
        "theme": "dark",
        "language": "ar",
        "autostart": False,
        "watch_folders": [],
        "notifications": True,
    }

    def __init__(self):
        self.config = self._load_config()
        self.running = False
        self.watchers: dict = {}  # folder -> thread

    def _load_config(self) -> dict:
        self.APP_DIR.mkdir(parents=True, exist_ok=True)
        if self.CONFIG_FILE.exists():
            with open(self.CONFIG_FILE, "r") as f:
                return {**self.DEFAULT_CONFIG, **json.load(f)}
        cfg = dict(self.DEFAULT_CONFIG)
        self._save_config(cfg)
        return cfg

    def _save_config(self, cfg: dict = None):
        if cfg:
            self.config = cfg
        self.APP_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.CONFIG_FILE, "w") as f:
            json.dump(self.config, f, indent=2, default=str)

    def _log(self, msg: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {msg}"
        print(entry)
        try:
            with open(self.LOG_FILE, "a", encoding="utf-8") as f:
                f.write(entry + "\n")
        except:
            pass

    # ═══════════════════════════════════════════
    # File System Tools
    # ═══════════════════════════════════════════

    @staticmethod
    def list_directory(path: str = ".") -> dict:
        """List directory contents."""
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return {"error": f"Path not found: {path}"}
        if p.is_file():
            return {"type": "file", "name": p.name, "size": p.stat().st_size,
                    "modified": datetime.fromtimestamp(p.stat().st_mtime).isoformat()}
        
        items = []
        for item in sorted(p.iterdir()):
            items.append({
                "name": item.name,
                "type": "dir" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else 0,
                "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
            })
        return {"type": "dir", "path": str(p), "items": items, "count": len(items)}

    @staticmethod
    def read_file(path: str) -> dict:
        """Read file content."""
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return {"error": f"File not found: {path}"}
        try:
            content = p.read_text(encoding="utf-8")
            return {"path": str(p), "content": content, "size": len(content),
                    "lines": content.count("\n") + 1}
        except UnicodeDecodeError:
            return {"error": "Binary file — cannot read as text", "size": p.stat().st_size}

    @staticmethod
    def write_file(path: str, content: str) -> dict:
        """Write content to file."""
        try:
            p = Path(path).expanduser()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return {"path": str(p), "written": len(content), "success": True}
        except Exception as e:
            return {"error": str(e), "success": False}

    @staticmethod
    def search_files(query: str, directory: str = ".") -> dict:
        """Search for files matching query."""
        results = []
        root = Path(directory).expanduser().resolve()
        if not root.exists():
            return {"error": f"Directory not found: {directory}"}
        
        try:
            for item in root.rglob(f"*{query}*"):
                if len(results) >= 50:
                    break
                results.append({
                    "name": item.name,
                    "path": str(item),
                    "type": "dir" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0,
                })
        except PermissionError:
            pass
        
        return {"query": query, "directory": str(root), "results": results, "count": len(results)}

    @staticmethod
    def get_system_info() -> dict:
        """Get system information."""
        import platform
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
            "home": str(Path.home()),
            "cwd": str(Path.cwd()),
            "disk_usage": _disk_usage(),
        }

    # ═══════════════════════════════════════════
    # Local Command Execution
    # ═══════════════════════════════════════════

    @staticmethod
    def run_command(cmd: str, timeout: int = 30) -> dict:
        """Execute a local shell command."""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=timeout, encoding="utf-8", errors="replace"
            )
            return {
                "command": cmd,
                "exit_code": result.returncode,
                "stdout": result.stdout[:5000],
                "stderr": result.stderr[:5000],
                "success": result.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            return {"command": cmd, "error": f"Timeout ({timeout}s)", "success": False}
        except Exception as e:
            return {"command": cmd, "error": str(e), "success": False}

    # ═══════════════════════════════════════════
    # Cloud API Bridge
    # ═══════════════════════════════════════════

    async def chat(self, message: str, agent: str = None) -> dict:
        """Send message to Auto Makah cloud API."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{self.config['api_url']}/api/chat/chat",
                    json={"message": message, "session_id": "desktop", "agent": agent},
                    headers={"Authorization": f"Bearer {self.config.get('api_key','')}"},
                )
                return resp.json()
        except Exception as e:
            return {"error": str(e), "reply": "⚠️ لا يمكن الاتصال بـ Auto Makah — تأكد من الاتصال بالإنترنت."}

    # ═══════════════════════════════════════════
    # File Watcher
    # ═══════════════════════════════════════════

    def watch_folder(self, path: str):
        """Watch a folder for changes and auto-process files."""
        if path in self.watchers:
            return {"status": "already_watching", "path": path}
        
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return {"error": f"Folder not found: {path}"}
        
        def _watch():
            import time as _time
            seen = set(str(f) for f in p.rglob("*") if f.is_file())
            while self.running:
                current = set(str(f) for f in p.rglob("*") if f.is_file())
                new_files = current - seen
                for fpath in new_files:
                    self._log(f"New file: {fpath}")
                seen = current
                _time.sleep(5)

        t = threading.Thread(target=_watch, daemon=True)
        self.watchers[path] = t
        t.start()
        self._log(f"Watching: {path}")
        return {"status": "watching", "path": path}

    # ═══════════════════════════════════════════
    # System Tray (Windows)
    # ═══════════════════════════════════════════

    def start_systray(self):
        """Start system tray icon with menu."""
        try:
            import pystray
            from PIL import Image, ImageDraw
        except ImportError:
            self._log("pystray/PIL not installed. Run: pip install pystray pillow")
            return

        # Create icon
        img = Image.new("RGB", (64, 64), color=(13, 79, 46))
        d = ImageDraw.Draw(img)
        d.ellipse([8, 8, 56, 56], fill=(212, 160, 23))
        d.text((22, 18), "AM", fill=(13, 79, 46))

        def on_open(_):
            webbrowser.open(self.config["api_url"])

        def on_kimi(_):
            webbrowser.open(f"{self.config['api_url']}/kimi")

        def on_quit(icon):
            self.running = False
            icon.stop()

        menu = pystray.Menu(
            pystray.MenuItem("🕋 Auto Makah", on_open, default=True),
            pystray.MenuItem("🎨 Kimi UI", on_kimi),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("⚙️ Settings", lambda _: webbrowser.open(str(self.CONFIG_FILE))),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("❌ Exit", on_quit),
        )

        icon = pystray.Icon("auto-makah", img, "Auto Makah 🕋", menu)
        self.running = True
        self._log("System tray started")

        # Run in thread so we can do other things
        t = threading.Thread(target=icon.run, daemon=True)
        t.start()
        return icon

    # ═══════════════════════════════════════════
    # Startup
    # ═══════════════════════════════════════════

    def start(self):
        """Initialize and run the desktop agent."""
        self._log("🚀 Auto Makah Desktop Agent — Starting...")
        self._log(f"   App dir: {self.APP_DIR}")
        self._log(f"   API: {self.config['api_url']}")
        self._log(f"   Home: {self.HOME}")

        # Start system tray if available
        tray = self.start_systray()

        return {
            "status": "running",
            "app_dir": str(self.APP_DIR),
            "api_url": self.config["api_url"],
            "home": str(self.HOME),
            "tray": tray is not None,
        }


# ═══════════════════════════════════════════
# CLI Entry Point
# ═══════════════════════════════════════════

def _disk_usage() -> dict:
    """Get disk usage info."""
    try:
        import shutil
        usage = shutil.disk_usage(str(Path.home()))
        return {
            "total_gb": round(usage.total / 1024**3, 1),
            "used_gb": round(usage.used / 1024**3, 1),
            "free_gb": round(usage.free / 1024**3, 1),
            "percent": round(usage.used / usage.total * 100, 1),
        }
    except:
        return {"error": "Cannot get disk usage"}


if __name__ == "__main__":
    agent = DesktopAgent()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "start":
            result = agent.start()
            print(json.dumps(result, indent=2, default=str))
            if result.get("tray"):
                print("\n🕋 Desktop Agent is running in system tray.")
                print("   Right-click the tray icon for options.")
                while agent.running:
                    time.sleep(1)
        elif cmd == "config":
            print(json.dumps(agent.config, indent=2, default=str))
        elif cmd == "list":
            path = sys.argv[2] if len(sys.argv) > 2 else "."
            print(json.dumps(agent.list_directory(path), indent=2, default=str))
        elif cmd == "read":
            if len(sys.argv) > 2:
                print(json.dumps(agent.read_file(sys.argv[2]), indent=2, default=str))
        elif cmd == "write":
            if len(sys.argv) > 3:
                print(json.dumps(agent.write_file(sys.argv[2], sys.argv[3]), indent=2, default=str))
        elif cmd == "run":
            if len(sys.argv) > 2:
                print(json.dumps(agent.run_command(" ".join(sys.argv[2:])), indent=2, default=str))
        elif cmd == "sysinfo":
            print(json.dumps(agent.get_system_info(), indent=2, default=str))
        elif cmd == "watch":
            path = sys.argv[2] if len(sys.argv) > 2 else "."
            print(json.dumps(agent.watch_folder(path), indent=2, default=str))
        elif cmd == "chat":
            if len(sys.argv) > 2:
                async def _chat():
                    result = await agent.chat(" ".join(sys.argv[2:]))
                    print(json.dumps(result, indent=2, default=str, ensure_ascii=False))
                asyncio.run(_chat())
            else:
                print("Usage: desktop_agent.py chat <message>")
        elif cmd == "search":
            if len(sys.argv) > 2:
                path = sys.argv[3] if len(sys.argv) > 3 else "."
                print(json.dumps(agent.search_files(sys.argv[2], path), indent=2, default=str))
        else:
            print(f"Unknown command: {cmd}")
            print("Commands: start, config, list, read, write, run, search, sysinfo, watch, chat")
    else:
        # Interactive mode
        print(json.dumps(agent.get_system_info(), indent=2, default=str))
        print("\nUsage: python desktop_agent.py <command> [args]")
        print("Commands: start, config, list, read, write, run, search, sysinfo, watch, chat")
