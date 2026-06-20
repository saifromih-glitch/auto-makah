# ═══════════════════════════════════════════
# 🕋 Auto Makah — Kimi Tools (Phase 2)
# Slides Generator + Code Runner + Rethink
# ═══════════════════════════════════════════

import asyncio
import subprocess
import tempfile
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SlideDeck:
    """Generated slide deck."""
    title: str
    slides: list = field(default_factory=list)
    html: str = ""


class SlidesGenerator:
    """Generate HTML slides from text/outline — like Kimi Slides."""

    @staticmethod
    def generate(title: str, content: str, theme: str = "professional") -> SlideDeck:
        """Convert text to a polished slide deck."""
        slides = []
        
        # Parse content into slides (split by headings or ---)
        raw_slides = content.split("\n---\n") if "---" in content else content.split("\n## ")
        
        for i, slide_content in enumerate(raw_slides):
            slide_content = slide_content.strip()
            if not slide_content:
                continue
            
            # Extract slide title from first line or heading
            lines = slide_content.split("\n")
            slide_title = lines[0].lstrip("#").strip() if lines else f"Slide {i+1}"
            slide_body = "\n".join(lines[1:]) if len(lines) > 1 else ""
            
            slides.append({
                "title": slide_title,
                "body": slide_body,
                "index": len(slides) + 1,
            })

        html = SlidesGenerator._render_html(title, slides, theme)
        return SlideDeck(title=title, slides=slides, html=html)

    @staticmethod
    def _render_html(title: str, slides: list, theme: str) -> str:
        colors = {
            "professional": {"bg": "#1a1a2e", "accent": "#e94560", "text": "#eee", "card": "#16213e"},
            "dark": {"bg": "#0d1117", "accent": "#58a6ff", "text": "#c9d1d9", "card": "#161b22"},
            "light": {"bg": "#fff", "accent": "#2563eb", "text": "#1f2937", "card": "#f3f4f6"},
            "makkah": {"bg": "#0d4f2e", "accent": "#d4a017", "text": "#f5f0e8", "card": "#1a6b3c"},
        }
        c = colors.get(theme, colors["professional"])
        
        slides_html = ""
        for s in slides:
            body_html = s["body"].replace("\n", "<br>") if s["body"] else ""
            slides_html += f'''
            <div class="slide">
                <div class="slide-number">{s["index"]}/{len(slides)}</div>
                <h2>{s["title"]}</h2>
                <div class="slide-body">{body_html}</div>
            </div>'''

        return f'''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Segoe UI','Tahoma',sans-serif; background:{c["bg"]}; color:{c["text"]}; }}
.container {{ max-width:900px; margin:0 auto; padding:20px; }}
h1 {{ text-align:center; padding:40px 0; color:{c["accent"]}; font-size:2.2em; }}
.slide {{ background:{c["card"]}; border-radius:16px; padding:40px; margin:20px 0; 
         border-right:4px solid {c["accent"]}; page-break-after:always; }}
.slide h2 {{ color:{c["accent"]}; font-size:1.5em; margin-bottom:20px; }}
.slide-number {{ font-size:0.8em; opacity:0.5; margin-bottom:10px; }}
.slide-body {{ font-size:1.1em; line-height:1.8; }}
@media print {{ .slide {{ page-break-after:always; margin:0; border-radius:0; }} }}
</style>
</head>
<body>
<div class="container">
<h1>{title}</h1>
{slides_html}
</div>
</body>
</html>'''


class CodeRunner:
    """Sandboxed code execution — like Kimi Code Runner."""

    TIMEOUT = 30  # seconds
    MAX_OUTPUT = 50000  # chars

    @staticmethod
    async def run_python(code: str) -> dict:
        """Execute Python code in a sandboxed temp file."""
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
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=CodeRunner.TIMEOUT)
            except asyncio.TimeoutError:
                proc.kill()
                return {"success": False, "output": "", "error": f"Timeout ({CodeRunner.TIMEOUT}s)", "exit_code": -1}

            output = stdout.decode('utf-8', errors='replace')[:CodeRunner.MAX_OUTPUT]
            error = stderr.decode('utf-8', errors='replace')[:CodeRunner.MAX_OUTPUT]

            return {
                "success": proc.returncode == 0,
                "output": output,
                "error": error,
                "exit_code": proc.returncode,
            }
        finally:
            try:
                os.unlink(tmp.name)
            except:
                pass

    @staticmethod
    async def run_javascript(code: str) -> dict:
        """Execute JavaScript using Node.js."""
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8')
        try:
            tmp.write(code)
            tmp.close()

            proc = await asyncio.create_subprocess_exec(
                'node', tmp.name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=CodeRunner.TIMEOUT)
            except asyncio.TimeoutError:
                proc.kill()
                return {"success": False, "output": "", "error": f"Timeout ({CodeRunner.TIMEOUT}s)", "exit_code": -1}

            output = stdout.decode('utf-8', errors='replace')[:CodeRunner.MAX_OUTPUT]
            error = stderr.decode('utf-8', errors='replace')[:CodeRunner.MAX_OUTPUT]

            return {
                "success": proc.returncode == 0,
                "output": output,
                "error": error,
                "exit_code": proc.returncode,
            }
        finally:
            try:
                os.unlink(tmp.name)
            except:
                pass


class RethinkEngine:
    """Intelligent idea organization — like Kimi Rethink."""

    @staticmethod
    def organize(notes: str, method: str = "mindmap") -> dict:
        """Organize scattered thoughts into structured format.
        
        Methods: mindmap, outline, categories, swot, pros-cons
        """
        lines = [l.strip() for l in notes.split("\n") if l.strip()]
        
        if method == "mindmap":
            return RethinkEngine._mindmap(lines)
        elif method == "outline":
            return RethinkEngine._outline(lines)
        elif method == "categories":
            return RethinkEngine._categories(lines)
        elif method == "swot":
            return RethinkEngine._swot(lines)
        elif method == "pros-cons":
            return RethinkEngine._pros_cons(lines)
        else:
            return {"method": method, "error": "Unknown method", "input": notes}

    @staticmethod
    def _mindmap(lines: list) -> dict:
        """Simple mind map from bullet points."""
        if not lines:
            return {"method": "mindmap", "central": "", "branches": []}
        
        central = lines[0].lstrip("•-*#").strip()
        branches = []
        current_branch = None
        
        for line in lines[1:]:
            clean = line.lstrip("•-*#").strip()
            if line.startswith("#") or line.startswith("##"):
                if current_branch:
                    branches.append(current_branch)
                current_branch = {"title": clean, "items": []}
            elif current_branch:
                current_branch["items"].append(clean)
            else:
                if not current_branch:
                    current_branch = {"title": "أفكار", "items": []}
                current_branch["items"].append(clean)
        
        if current_branch:
            branches.append(current_branch)
        
        return {"method": "mindmap", "central": central, "branches": branches}

    @staticmethod
    def _outline(lines: list) -> dict:
        """Hierarchical outline."""
        outline = []
        for line in lines:
            depth = 0
            clean = line
            for prefix in ["#### ", "### ", "## ", "# ", "    - ", "  - ", "- "]:
                if clean.startswith(prefix):
                    depth = {"#### ": 4, "### ": 3, "## ": 2, "# ": 1, "    - ": 3, "  - ": 2, "- ": 1}.get(prefix, 0)
                    clean = clean[len(prefix):]
                    break
            outline.append({"depth": depth, "text": clean})
        return {"method": "outline", "items": outline}

    @staticmethod
    def _categories(lines: list) -> dict:
        """Group ideas into categories."""
        categories = {}
        current_cat = "عام"
        
        for line in lines:
            clean = line.lstrip("•-*#").strip()
            if ":" in clean and len(clean.split(":")[0]) < 30:
                cat, rest = clean.split(":", 1)
                current_cat = cat.strip()
                if rest.strip():
                    categories.setdefault(current_cat, []).append(rest.strip())
            else:
                categories.setdefault(current_cat, []).append(clean)
        
        return {"method": "categories", "categories": categories}

    @staticmethod
    def _swot(lines: list) -> dict:
        """SWOT analysis from notes."""
        result = {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []}
        current = None
        
        swot_map = {
            "قوة": "strengths", "نقاط القوة": "strengths", "القوة": "strengths", "strengths": "strengths", "s": "strengths",
            "ضعف": "weaknesses", "نقاط الضعف": "weaknesses", "الضعف": "weaknesses", "weaknesses": "weaknesses", "w": "weaknesses",
            "فرص": "opportunities", "الفرص": "opportunities", "فرصة": "opportunities", "opportunities": "opportunities", "o": "opportunities",
            "تهديد": "threats", "التهديدات": "threats", "تهديدات": "threats", "threats": "threats", "t": "threats",
        }
        
        for line in lines:
            clean = line.lstrip("•-*#").strip().lower()
            # Check if line ends with colon (category marker)
            matched = None
            for kw, cat in swot_map.items():
                # Match: "قوة: ..." or just "قوة"
                if clean == kw or clean.startswith(kw + ":") or clean.startswith(kw + " :"):
                    matched = cat
                    # Check if there's content after colon
                    rest = clean[len(kw):].lstrip(" :").strip()
                    if rest and matched:
                        result[matched].append(rest)
                    break
            if matched:
                current = matched
                if not rest:  # skip adding if we already added the rest
                    continue
            elif current and clean:
                result[current].append(line.lstrip("•-*#").strip())
        
        return {"method": "swot", "analysis": result}

    @staticmethod
    def _pros_cons(lines: list) -> dict:
        """Pros and Cons analysis."""
        result = {"pros": [], "cons": []}
        current = None
        
        for line in lines:
            clean = line.lstrip("•-*#").strip()
            if any(clean.startswith(w) for w in ["إيجابيات", "مزايا", "+", "Pros"]):
                current = "pros"
            elif any(clean.startswith(w) for w in ["سلبيات", "عيوب", "-", "Cons"]):
                current = "cons"
            elif current and clean:
                result[current].append(clean)
        
        return {"method": "pros-cons", "analysis": result}


# ═══════════════════════════════════════════
# Tool Registry — register these as tools
# ═══════════════════════════════════════════

KIMI_TOOLS = {
    "slides": {
        "name": "slides",
        "display": "🎨 Slides Generator",
        "description": "تحويل النص إلى شرائح عرض احترافية",
        "handler": SlidesGenerator.generate,
        "params": ["title", "content", "theme"],
    },
    "code_run": {
        "name": "code_run",
        "display": "💻 Code Runner",
        "description": "تشغيل كود Python/JavaScript في بيئة آمنة",
        "handler": CodeRunner.run_python,
        "params": ["code"],
    },
    "rethink": {
        "name": "rethink",
        "display": "🧠 Rethink",
        "description": "تنظيم الأفكار المبعثرة (خرائط ذهنية، SWOT، تصنيف)",
        "handler": RethinkEngine.organize,
        "params": ["notes", "method"],
    },
}
