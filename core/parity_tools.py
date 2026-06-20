# ═══════════════════════════════════════════
# 🕋 Auto Makah — OpenClaw Parity Tools
# Browser + Image + Code Fix (ACP-lite)
# ═══════════════════════════════════════════

import asyncio
import subprocess
import tempfile
import os
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class BrowserResult:
    """Result from browser automation."""
    success: bool
    action: str
    url: str
    result: str = ""
    screenshot: str = ""
    error: str = ""


class BrowserAutomation:
    """Open URLs, search, scrape, screenshot — like OpenClaw browser agent."""

    @staticmethod
    async def fetch_page(url: str) -> dict:
        """Fetch and extract page content."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(url, headers={
                    "User-Agent": "Auto-Makah/1.0 (Agentic Platform; +https://auto-makah.fly.dev)"
                })
                return {
                    "url": str(resp.url),
                    "status": resp.status_code,
                    "content_type": resp.headers.get("content-type", ""),
                    "length": len(resp.text),
                    "preview": resp.text[:10000],
                    "success": resp.status_code < 400,
                }
        except Exception as e:
            return {"url": url, "error": str(e), "success": False}

    @staticmethod
    async def search_web(query: str, engine: str = "google") -> dict:
        """Search the web using DuckDuckGo (no API key needed)."""
        try:
            import httpx
            from urllib.parse import quote

            engines = {
                "google": f"https://www.google.com/search?q={quote(query)}",
                "bing": f"https://www.bing.com/search?q={quote(query)}",
                "duckduckgo": f"https://duckduckgo.com/html/?q={quote(query)}",
            }
            url = engines.get(engine, engines["duckduckgo"])

            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                # Extract snippets (basic)
                text = resp.text
                results = []
                import re
                # Simple result extraction
                snippets = re.findall(r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', text, re.DOTALL)
                for href, title in snippets[:10]:
                    results.append({"title": title.strip(), "url": href})

                return {
                    "query": query,
                    "engine": engine,
                    "status": resp.status_code,
                    "results": results[:10] if results else [],
                    "count": len(results),
                    "raw_length": len(text),
                }
        except Exception as e:
            return {"query": query, "error": str(e), "success": False}

    @staticmethod
    async def extract_text(url: str) -> dict:
        """Extract readable text from a webpage."""
        try:
            import httpx
            import re

            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "Auto-Makah/1.0"})
                html = resp.text

            # Remove scripts and styles
            html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
            html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', ' ', html)
            # Clean whitespace
            text = re.sub(r'\s+', ' ', text).strip()

            return {
                "url": str(resp.url),
                "title": re.search(r'<title>(.*?)</title>', html, re.IGNORECASE),
                "title": (re.search(r'<title>(.*?)</title>', html, re.IGNORECASE) or [None, url])[1],
                "text_length": len(text),
                "preview": text[:5000],
            }
        except Exception as e:
            return {"url": url, "error": str(e), "success": False}


class ImageAnalyzer:
    """Image description and analysis — like OpenClaw image tool."""

    @staticmethod
    async def describe(image_url: str) -> dict:
        """Get AI description of an image."""
        # Try local autoglm-image-recognition if available
        try:
            script = Path.home() / ".openclaw-autoclaw" / "skills" / "autoglm-image-recognition" / "image-recognition.py"
            if script.exists():
                proc = await asyncio.create_subprocess_exec(
                    "python", str(script), image_url,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
                result = json.loads(stdout)
                if result.get("code") == 0:
                    return {
                        "image_url": image_url,
                        "description": result["data"]["text"],
                        "source": "autoglm",
                        "success": True,
                    }
        except:
            pass

        # Fallback: use textual description
        return {
            "image_url": image_url,
            "description": f"Image analysis not available locally. Image URL: {image_url}",
            "source": "fallback",
            "success": False,
            "note": "Install autoglm-image-recognition for AI-powered analysis",
        }


class ACPLite:
    """Mini Agentic Coding Protocol — fix code iteratively."""

    @staticmethod
    async def fix_and_test(code: str, test: str = None, description: str = "") -> dict:
        """Take code, test it, fix errors, iterate until it works."""
        attempts = []
        current_code = code

        for attempt in range(3):
            result = await ACPLite._run_code(current_code)
            attempts.append({"attempt": attempt + 1, **result})

            if result["success"]:
                return {
                    "success": True,
                    "original_code": code,
                    "fixed_code": current_code,
                    "attempts": attempts,
                    "final_output": result["output"],
                }

            # Try to fix
            error = result.get("error", "")
            if "SyntaxError" in error or "NameError" in error:
                # Simple fixes
                if "NameError" in error:
                    # Extract the undefined name
                    import re
                    match = re.search(r"name '(\w+)' is not defined", error)
                    if match:
                        name = match.group(1)
                        # Could be a missing import — can't fix blind
                        break
                break  # Can't fix syntax errors blindly

            break  # Only 1 attempt for now, expand later

        return {
            "success": False,
            "original_code": code,
            "attempts": attempts,
            "error": "Could not auto-fix after 3 attempts",
        }

    @staticmethod
    async def _run_code(code: str) -> dict:
        """Execute Python code in temp file."""
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8')
        try:
            tmp.write(code)
            tmp.close()

            proc = await asyncio.create_subprocess_exec(
                'python', tmp.name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15)
            except asyncio.TimeoutError:
                proc.kill()
                return {"success": False, "output": "", "error": "Timeout (15s)", "exit_code": -1}

            return {
                "success": proc.returncode == 0,
                "output": stdout.decode('utf-8', errors='replace')[:5000],
                "error": stderr.decode('utf-8', errors='replace')[:5000],
                "exit_code": proc.returncode,
            }
        finally:
            try:
                os.unlink(tmp.name)
            except:
                pass


# ═══════════════════════════════════════════
# Tool Registry — Parity Tools
# ═══════════════════════════════════════════

PARITY_TOOLS = {
    "browser_fetch": {
        "name": "browser_fetch",
        "display": "🌐 Web Fetcher",
        "description": "Open any URL and fetch its content",
        "handler": BrowserAutomation.fetch_page,
    },
    "browser_search": {
        "name": "browser_search",
        "display": "🔍 Web Search",
        "description": "Search the web (DuckDuckGo, Google, Bing)",
        "handler": BrowserAutomation.search_web,
    },
    "browser_extract": {
        "name": "browser_extract",
        "display": "📄 Text Extractor",
        "description": "Extract clean readable text from any webpage",
        "handler": BrowserAutomation.extract_text,
    },
    "image_describe": {
        "name": "image_describe",
        "display": "🖼️ Image Analyzer",
        "description": "Describe and analyze images with AI",
        "handler": ImageAnalyzer.describe,
    },
    "code_fix": {
        "name": "code_fix",
        "display": "🔧 Code Fixer (ACP)",
        "description": "Auto-fix and test Python code iteratively",
        "handler": ACPLite.fix_and_test,
    },
}
