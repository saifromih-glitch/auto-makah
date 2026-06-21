# ═══════════════════════════════════════════════════════
# 🔍 Self-Verification Engine — v1.0
# Auto Makah tests itself. No external tools needed.
# ═══════════════════════════════════════════════════════

import urllib.request, json, os, re, logging
from dataclasses import dataclass, asdict
from typing import Optional, List

log = logging.getLogger("verifier")

BASE_URL = "https://auto-makah.fly.dev"


@dataclass
class MobileCheck:
    """Single mobile check result."""
    name: str
    passed: bool
    detail: str = ""
    suggestion: str = ""


@dataclass  
class PageReport:
    """Full verification report for a page."""
    url: str
    status_code: int = 0
    load_time_ms: int = 0
    content_size: int = 0
    title: str = ""
    checks: List[MobileCheck] = None
    
    def __post_init__(self):
        if self.checks is None:
            self.checks = []
    
    def passed_count(self) -> int:
        return sum(1 for c in self.checks if c.passed)
    
    def total_count(self) -> int:
        return len(self.checks)
    
    def score(self) -> float:
        return round((self.passed_count() / max(self.total_count(), 1)) * 100, 1)
    
    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "status": self.status_code,
            "load_ms": self.load_time_ms,
            "size_bytes": self.content_size,
            "title": self.title,
            "score": f"{self.score()}%",
            "passed": self.passed_count(),
            "total": self.total_count(),
            "checks": [asdict(c) for c in self.checks],
        }


def fetch_page(path: str) -> tuple:
    """Fetch a page by reading from disk (avoids recursive HTTP call)."""
    import time
    start = time.time()
    
    # Map paths to files
    file_map = {
        "/": "landing.html",
        "/kimi": "kimi-ui.html",
        "/skills": "skills-store.html",
    }
    
    if path in file_map:
        base = os.path.dirname(os.path.dirname(__file__))
        filepath = os.path.join(base, "dashboard", file_map[path])
    elif path.endswith(".html") or path.endswith(".txt"):
        base = os.path.dirname(os.path.dirname(__file__))
        filepath = os.path.join(base, "dashboard", os.path.basename(path))
    else:
        # API endpoint — try HTTP (won't deadlock for small JSON)
        try:
            url = BASE_URL + path
            r = urllib.request.urlopen(url, timeout=5)
            html = r.read().decode('utf-8')
            elapsed = int((time.time() - start) * 1000)
            return r.status, html, elapsed
        except Exception:
            return 0, "", int((time.time() - start) * 1000)
    
    try:
        if os.path.isfile(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                html = f.read()
            elapsed = int((time.time() - start) * 1000)
            return 200, html, elapsed
        return 404, "", int((time.time() - start) * 1000)
    except Exception as e:
        return 500, str(e), int((time.time() - start) * 1000)


def verify_page(path: str) -> PageReport:
    """Run all verification checks on a page."""
    status, html, load_ms = fetch_page(path)
    
    title = ""
    title_match = re.search(r'<title>(.*?)</title>', html)
    if title_match:
        title = title_match.group(1)
    
    report = PageReport(
        url=BASE_URL + path,
        status_code=status,
        load_time_ms=load_ms,
        content_size=len(html),
        title=title,
    )
    
    if status != 200:
        report.checks.append(MobileCheck("http_status", False, f"Status {status}", "Check deployment"))
        return report
    
    report.checks.append(MobileCheck("http_status", True, "200 OK"))
    
    # ─── MOBILE CHECKS ───
    
    # 1. Viewport meta tag
    has_viewport = bool(re.search(r'<meta[^>]*viewport[^>]*>', html, re.IGNORECASE))
    report.checks.append(MobileCheck(
        "viewport_meta", has_viewport,
        "Found" if has_viewport else "Missing",
        "" if has_viewport else "Add: <meta name='viewport' content='width=device-width, initial-scale=1.0'>"
    ))
    
    # 2. RTL direction
    has_rtl = 'dir="rtl"' in html or "dir='rtl'" in html or 'direction:rtl' in html.lower()
    report.checks.append(MobileCheck(
        "rtl_support", has_rtl,
        "RTL detected" if has_rtl else "No RTL",
        "" if has_rtl else "Add dir='rtl' to <html> tag"
    ))
    
    # 3. Responsive CSS
    has_media = '@media' in html
    has_responsive = has_media or 'max-width' in html or 'min-width' in html or 'clamp(' in html
    report.checks.append(MobileCheck(
        "responsive_css", has_responsive,
        "Responsive" if has_responsive else "Not responsive",
        "" if has_responsive else "Add @media queries or clamp() for responsive design"
    ))
    
    # 4. Font size responsive
    has_clamp = 'clamp(' in html
    has_rem = 'rem' in html or 'em' in html
    report.checks.append(MobileCheck(
        "font_scaling", has_clamp or has_rem,
        f"clamp()={'yes' if has_clamp else 'no'}, rem={'yes' if has_rem else 'no'}",
        "" if (has_clamp or has_rem) else "Use clamp() or rem units for font sizes"
    ))
    
    # 5. Grid/Flex layout
    has_flex = 'display:flex' in html or 'display: flex' in html
    has_grid = 'display:grid' in html or 'display: grid' in html
    report.checks.append(MobileCheck(
        "modern_layout", has_flex or has_grid,
        f"flex={'yes' if has_flex else 'no'}, grid={'yes' if has_grid else 'no'}",
        "" if (has_flex or has_grid) else "Use flexbox or grid for layout"
    ))
    
    # 6. Content length
    is_substantial = report.content_size > 2000
    report.checks.append(MobileCheck(
        "content_size", is_substantial,
        f"{report.content_size} bytes",
        "" if is_substantial else "Page too small — may be incomplete"
    ))
    
    # 7. Load time
    is_fast = load_ms < 3000
    report.checks.append(MobileCheck(
        "load_time", is_fast,
        f"{load_ms}ms",
        "" if is_fast else f"Page loads in {load_ms}ms — optimize"
    ))
    
    # 8. Error text detection (broken pages)
    has_errors = 'Error' in html[:200] or 'error' in html[:200].lower() or 'Traceback' in html[:500]
    report.checks.append(MobileCheck(
        "no_errors", not has_errors,
        "Clean" if not has_errors else "Errors detected",
        "" if not has_errors else "Page has error output — needs fixing"
    ))
    
    # 9. Mobile text cutoff check (long words without wrapping)
    has_word_break = 'word-break' in html or 'overflow-wrap' in html or 'white-space' in html
    report.checks.append(MobileCheck(
        "text_wrapping", has_word_break,
        "Wrapping styles found" if has_word_break else "No wrapping",
        "" if has_word_break else "Add word-break or overflow-wrap for long text"
    ))
    
    return report


def verify_all_pages() -> dict:
    """Verify all Auto Makah pages and return combined report."""
    pages = [
        ("/", "Landing Page"),
        ("/kimi", "Kimi UI"),
        ("/skills", "Skill Store"),
        ("/api/health", "Health API"),
    ]
    
    reports = {}
    for path, name in pages:
        reports[name] = verify_page(path).to_dict()
    
    avg_score = sum(r["passed"] / max(r["total"], 1) for r in reports.values()) / max(len(reports), 1)
    
    return {
        "platform": "Auto Makah",
        "timestamp": __import__('datetime').datetime.now().isoformat(),
        "pages_checked": len(reports),
        "average_score": f"{round(avg_score * 100, 1)}%",
        "pages": reports,
    }


def quick_self_test() -> str:
    """Run a 3-second self-verification and return plain text report."""
    results = []
    pages = [("/", "Home"), ("/kimi", "Kimi"), ("/skills", "Skills"), ("/api/health", "Health")]
    
    for path, name in pages:
        status, html, ms = fetch_page(path)
        icon = "✅" if status == 200 else "❌"
        size_kb = len(html) / 1024
        rtl = "RTL" if 'dir="rtl"' in html else "LTR"
        results.append(f"{icon} {name}: {status} | {size_kb:.0f}KB | {ms}ms | {rtl}")
    
    return "\n".join(results)


if __name__ == "__main__":
    print(quick_self_test())
