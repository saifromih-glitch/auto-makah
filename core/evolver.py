"""
Self-Evolving Agent — reads Auto Makah code, finds issues, reports improvements
"""
import os, httpx, asyncio, json
from pathlib import Path
from datetime import datetime

ZENMUX_URL = "https://zenmux.ai/api/v1/chat/completions"
ZENMUX_KEY = os.getenv("ZENMUX_API_KEY", "")

async def _call_ai(prompt: str, max_tokens: int = 3000) -> str:
    if not ZENMUX_KEY:
        return "Error: No ZENMUX_API_KEY configured"
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(ZENMUX_URL, headers={
                "Authorization": f"Bearer {ZENMUX_KEY}",
                "Content-Type": "application/json",
            }, json={
                "model": "z-ai/glm-5.2-free",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens, "temperature": 0.3,
            })
            data = resp.json()
            if "choices" in data:
                return data["choices"][0]["message"]["content"]
            return f"API error: {data}"
    except Exception as e:
        return f"Error: {str(e)}"

def _read_code_files(root: str, max_files: int = 50) -> dict:
    """Read Python files from the project, skip tests/backups."""
    files = {}
    skip = ['__pycache__', 'tests', '.git', 'node_modules', 'output', 'data', 'backups']
    for r, dirs, fnames in os.walk(root):
        dirs[:] = [d for d in dirs if d not in skip]
        for f in fnames:
            if f.endswith('.py') and len(files) < max_files:
                path = os.path.join(r, f)
                try:
                    with open(path, encoding='utf-8') as fh:
                        content = fh.read()
                    rel = os.path.relpath(path, root)
                    files[rel] = content[:3000]  # First 3000 chars each
                except Exception:
                    pass
    return files

async def analyze_code(project_root: str = None) -> dict:
    """Read Auto Makah code and analyze for issues."""
    if not project_root:
        project_root = os.path.dirname(os.path.dirname(__file__))
    
    files = _read_code_files(project_root, max_files=40)
    
    # Build a summary for the AI
    file_list = "\n".join(f"- {name} ({len(content)} chars)" for name, content in files.items())
    
    prompt = f"""أنت مهندس برمجيات خبير. حلل الكود التالي لمشروع "Auto Makah" - منصة ذكاء اصطناعي عربية.

الملفات المتاحة للتحليل:
{file_list}

حلل الكود من حيث:
1. التكرار (نفس الكود موجود في أكثر من مكان)
2. مشاكل محتملة (bugs, errors, edge cases)
3. تحسينات معمارية (architecture improvements)
4. أمان (security issues)
5. أداء (performance issues)

لكل مشكلة:
- حدد الملف
- صف المشكلة بوضوح
- اقترح حلاً محدداً

الإخراج بالعربية."""

    analysis = await _call_ai(prompt, max_tokens=4000)
    
    return {
        "project": "Auto Makah",
        "files_analyzed": len(files),
        "timestamp": datetime.now().isoformat(),
        "analysis": analysis,
        "files": list(files.keys()),
    }

async def analyze_config_files(workspace_root: str) -> dict:
    """Analyze workspace config files for redundancy and stale data."""
    config_files = ["AGENTS.md", "TOOLS.md", "MEMORY.md", "HEARTBEAT.md", "SOUL.md", "USER.md"]
    contents = {}
    
    for fname in config_files:
        path = os.path.join(workspace_root, fname)
        if os.path.exists(path):
            try:
                with open(path, encoding='utf-8') as f:
                    contents[fname] = f.read()[:5000]
            except Exception:
                pass
    
    prompt_parts = []
    prompt_parts.append("أنت منظم ومعقب على ملفات workspace. حلل الملفات التالية:")
    
    for fname, content in contents.items():
        prompt_parts.append(f"\n### {fname}")
        prompt_parts.append(content[:2000])
    
    prompt_parts.append("""
حلل:
1. التكرار بين الملفات (نفس المعلومة في أكثر من مكان)
2. المعلومات القديمة التي تحتاج تحديث
3. التناقضات بين الملفات
4. القواعد الميتة (ما عادتش تنطبق)

قدم تقريراً منظماً بالإصلاحات المطلوبة. الإخراج بالعربية.""")
    
    analysis = await _call_ai("\n".join(prompt_parts), max_tokens=3000)
    
    return {
        "files_analyzed": list(contents.keys()),
        "timestamp": datetime.now().isoformat(),
        "analysis": analysis,
    }
