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


# ═══ 🏥 Self-Healing Engine ═══
# Automatically fixes detected issues without human intervention

AUTO_FIXES = {
    "text_wrapping": {
        "selector": "body{",
        "css_rule": "body{word-break:break-word;overflow-wrap:break-word;",
        "description": "Added word-break and overflow-wrap for mobile text",
    },
    "viewport_meta": {
        "selector": "<head>",
        "css_rule": '<head>\n<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        "description": "Added viewport meta tag",
    },
}


def auto_fix_page(page_name: str) -> dict:
    """
    Detect issues → Auto-fix what we can → Re-verify.
    Returns: {page, fixes_applied, before_score, after_score}
    """
    file_map = {
        "/": "landing.html",
        "/kimi": "kimi-ui.html", 
        "/skills": "skills-store.html",
    }
    
    path = None
    filename = None
    for p, f in file_map.items():
        if p == page_name or f == page_name:
            path = p
            filename = f
            break
    
    if not filename:
        return {"error": f"Unknown page: {page_name}"}
    
    base = os.path.dirname(os.path.dirname(__file__))
    filepath = os.path.join(base, "dashboard", filename)
    
    if not os.path.isfile(filepath):
        return {"error": f"File not found: {filepath}"}
    
    # Step 1: Verify before
    before = verify_page(path)
    
    # Step 2: Read the file
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()
    
    original = html
    fixes_applied = []
    
    # Step 3: Apply auto-fixes
    for check in before.checks:
        if not check.passed and check.name in AUTO_FIXES:
            fix = AUTO_FIXES[check.name]
            old = fix["selector"]
            new = fix["css_rule"]
            if old in html:
                html = html.replace(old, new, 1)
                fixes_applied.append({
                    "issue": check.name,
                    "old": old[:60],
                    "new": new[:60],
                    "description": fix["description"],
                })
    
    # Step 4: Write fixed file
    if html != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
    
    # Step 5: Re-verify
    after = verify_page(path)
    
    return {
        "page": filename,
        "fixes_applied": len(fixes_applied),
        "fixes": fixes_applied,
        "before_score": before.score(),
        "after_score": after.score(),
        "healed": after.score() > before.score(),
    }


def heal_all_pages() -> dict:
    """Auto-fix all pages and return healing report."""
    results = []
    for page in ["/", "/kimi", "/skills"]:
        result = auto_fix_page(page)
        results.append(result)
    
    healed = sum(1 for r in results if r.get("healed"))
    total_fixes = sum(r.get("fixes_applied", 0) for r in results)
    
    return {
        "platform": "Auto Makah",
        "action": "heal_all",
        "pages_healed": healed,
        "total_fixes_applied": total_fixes,
        "results": results,
    }


# ═══ 📲 Mohammed Notification ═══
def notify_mohammed(message: str) -> bool:
    """Send Telegram notification to Mohammed when platform needs attention."""
    import os
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        log.warning("No TELEGRAM_BOT_TOKEN — can't notify Mohammed")
        return False
    
    mohammed_chat_id = "5660460079"  # Mohammed's Telegram ID
    
    try:
        body = json.dumps({
            "chat_id": mohammed_chat_id,
            "text": message,
            "parse_mode": "HTML",
        }).encode('utf-8')
        
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=5)
        return True
    except Exception as e:
        log.error(f"Failed to notify Mohammed: {e}")
        return False


def heal_and_notify() -> dict:
    """
    Full cycle: Verify → Heal → Re-verify → Notify Mohammed if needed.
    This is the autonomous loop that runs periodically.
    """
    # Step 1: Verify all pages
    before = verify_all_pages()
    
    # Step 2: Heal what we can
    heal_result = heal_all_pages()
    
    # Step 3: Re-verify
    after = verify_all_pages()
    
    # Step 4: Build notification
    alerts = []
    for page_name, report in after.get("pages", {}).items():
        if report.get("score", "0%") != "100.0%":
            failures = [c for c in report.get("checks", []) if not c.get("passed")]
            for f in failures:
                if f["name"] not in AUTO_FIXES:
                    alerts.append(f"{page_name}: {f['name']} — {f.get('suggestion', 'يحتاج تدخل يدوي')}")
    
    # Step 5: Notify Mohammed if unfixable issues remain
    if alerts:
        message = "🕋 <b>Auto Makah — مشاكل تحتاج تدخلك</b>\n\n"
        message += "\n".join(f"• {a}" for a in alerts[:5])
        message += f"\n\n🔗 <a href='https://auto-makah.fly.dev'>افتح المنصة</a>"
        notify_mohammed(message)
    
    return {
        "before_score": before.get("average_score"),
        "after_score": after.get("average_score"),
        "healed": heal_result.get("pages_healed", 0),
        "unfixable_alerts": len(alerts),
        "mohammed_notified": bool(alerts),
    }
