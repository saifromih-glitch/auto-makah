# ═══════════════════════════════════════════════════════
# 🕷️ Web Scraper — Auto Makah v1.0
# Full web scraping: tables, lists, text, structured data
# Export: JSON, CSV. Scheduled scraping. Arabic-compatible.
# ═══════════════════════════════════════════════════════

import urllib.request, json, csv, re, io, os, hashlib, logging
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from html.parser import HTMLParser

log = logging.getLogger("scraper")


# ═══ HTML Parser ═══
class ScraperParser(HTMLParser):
    """Extract structured data from HTML: tables, lists, headings, text."""

    def __init__(self):
        super().__init__()
        self.tables: List[Dict] = []
        self.lists: List[Dict] = []
        self.headings: List[Dict] = []
        self.links: List[Dict] = []
        self.text_blocks: List[str] = []
        self.meta_tags: Dict[str, str] = {}

        # Parser state
        self._current_table = None
        self._current_row = None
        self._current_cell = None
        self._current_list = None
        self._current_tag = None
        self._text_buffer = ""
        self._in_table = False
        self._in_row = False
        self._in_cell = False
        self._in_list = False
        self._in_heading = False
        self._skip_script = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        tag = tag.lower()

        if tag in ("script", "style"):
            self._skip_script = True
            return

        # Tables
        if tag == "table":
            self._current_table = {"headers": [], "rows": [], "caption": ""}
            self._in_table = True
        elif tag == "tr" and self._in_table:
            self._current_row = []
            self._in_row = True
        elif tag in ("td", "th") and self._in_row:
            self._current_cell = ""
            self._in_cell = True
        elif tag == "caption" and self._in_table:
            self._current_tag = "caption"

        # Lists
        elif tag in ("ul", "ol"):
            self._current_list = {"type": tag, "items": []}
            self._in_list = True
        elif tag == "li" and self._in_list:
            self._text_buffer = ""

        # Headings
        elif tag in ("h1", "h2", "h3", "h4"):
            self._in_heading = True
            self._current_tag = tag
            self._text_buffer = ""

        # Links
        elif tag == "a" and "href" in attrs_dict:
            self.links.append({
                "url": attrs_dict["href"],
                "text": attrs_dict.get("title", ""),
            })
            self._current_tag = "a"
            self._text_buffer = ""

        # Meta
        elif tag == "meta":
            name = attrs_dict.get("name") or attrs_dict.get("property", "")
            content = attrs_dict.get("content", "")
            if name and content:
                self.meta_tags[name] = content

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in ("script", "style"):
            self._skip_script = False
            return

        if tag in ("td", "th") and self._in_cell:
            self._current_row.append(self._current_cell.strip())
            self._in_cell = False
        elif tag == "tr" and self._in_row:
            if self._current_table is not None:
                self._current_table["rows"].append(self._current_row)
            self._in_row = False
            self._current_row = None
        elif tag == "table" and self._in_table:
            if self._current_table and self._current_table["rows"]:
                # Auto-detect headers from first row
                if self._current_table["rows"] and not self._current_table["headers"]:
                    self._current_table["headers"] = self._current_table["rows"][0]
                    self._current_table["rows"] = self._current_table["rows"][1:]
                self.tables.append(self._current_table)
            self._current_table = None
            self._in_table = False
        elif tag in ("ul", "ol") and self._in_list:
            if self._current_list and self._current_list["items"]:
                self.lists.append(self._current_list)
            self._current_list = None
            self._in_list = False
        elif tag == "li" and self._in_list:
            if self._current_list is not None:
                self._current_list["items"].append(self._text_buffer.strip())
        elif tag in ("h1", "h2", "h3", "h4") and self._in_heading:
            self.headings.append({"level": tag, "text": self._text_buffer.strip()})
            self._in_heading = False

        if tag == "a" and self._current_tag == "a" and self.links:
            self.links[-1]["text"] = self._text_buffer.strip()
            self._current_tag = None

    def handle_data(self, data):
        if self._skip_script:
            return
        text = data.strip()
        if not text:
            return

        if self._in_cell:
            self._current_cell += " " + text
        elif self._in_heading:
            self._text_buffer += " " + text
        elif self._current_tag == "a":
            self._text_buffer += " " + text
        elif self._in_list:
            self._text_buffer += " " + text
        elif self._current_tag == "caption":
            if self._current_table is not None:
                self._current_table["caption"] = text
            self._current_tag = None
        elif len(text) > 30:
            self.text_blocks.append(text)

    def to_dict(self) -> dict:
        return {
            "tables_count": len(self.tables),
            "tables": self.tables[:10],  # Max 10 tables
            "lists_count": len(self.lists),
            "lists": self.lists[:5],
            "headings": self.headings[:20],
            "links_count": len(self.links),
            "links": self.links[:30],
            "meta": self.meta_tags,
            "text_blocks": len(self.text_blocks),
            "text_preview": " ".join(self.text_blocks[:3])[:500],
        }


# ═══ Core Scraper ═══
@dataclass
class ScrapeResult:
    url: str
    title: str
    status_code: int
    content_size: int
    scraped_at: str
    data: Dict[str, Any]
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None and self.status_code == 200

    def to_dict(self) -> dict:
        d = asdict(self)
        d["ok"] = self.ok
        return d


def scrape_url(url: str, extract_tables: bool = True, extract_lists: bool = True,
               extract_links: bool = True, max_size: int = 500000) -> ScrapeResult:
    """Scrape a URL and extract structured data."""

    try:
        # Request with proper headers (avoid blocks)
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ar,en;q=0.9",
        })

        with urllib.request.urlopen(req, timeout=20) as resp:
            status = resp.status
            # Auto-detect encoding
            content_type = resp.headers.get("Content-Type", "")
            charset = "utf-8"
            if "charset=" in content_type:
                charset = content_type.split("charset=")[-1].split(";")[0].strip()

            raw = resp.read(max_size)
            html = raw.decode(charset, errors="replace")

        # Parse HTML
        parser = ScraperParser()
        parser.feed(html)

        # Extract title
        title_match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else url

        # Build result
        data = parser.to_dict()

        # Add raw text for LLM processing
        clean_text = " ".join(parser.text_blocks[:50])

        return ScrapeResult(
            url=url,
            title=title,
            status_code=status,
            content_size=len(html),
            scraped_at=datetime.now().isoformat(),
            data={
                **data,
                "full_text": clean_text[:5000],
                "url": url,
                "title": title,
            },
        )

    except urllib.error.HTTPError as e:
        return ScrapeResult(url=url, title="", status_code=e.code, content_size=0,
                           scraped_at=datetime.now().isoformat(), data={},
                           error=f"HTTP {e.code}")
    except Exception as e:
        return ScrapeResult(url=url, title="", status_code=0, content_size=0,
                           scraped_at=datetime.now().isoformat(), data={},
                           error=str(e)[:200])


# ═══ Export Functions ═══
def export_to_csv(scrape_result: ScrapeResult) -> str:
    """Export scraped tables to CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)

    tables = scrape_result.data.get("tables", [])
    for i, table in enumerate(tables):
        writer.writerow([f"--- Table {i+1}: {table.get('caption', '')} ---"])
        if table.get("headers"):
            writer.writerow(table["headers"])
        for row in table.get("rows", []):
            writer.writerow(row)
        writer.writerow([])

    return output.getvalue()


def export_to_json(scrape_result: ScrapeResult) -> str:
    """Export full scrape result to formatted JSON."""
    return json.dumps(scrape_result.to_dict(), ensure_ascii=False, indent=2)


# ═══ Scheduled Scraping ═══
SCRAPE_SCHEDULE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "scrapes")
os.makedirs(SCRAPE_SCHEDULE_DIR, exist_ok=True)


def schedule_scrape(url: str, name: str, interval_hours: int = 24) -> str:
    """Schedule a periodic scrape. Returns schedule ID."""
    schedule_id = hashlib.md5(f"{name}{url}".encode()).hexdigest()[:12]

    schedule = {
        "id": schedule_id,
        "name": name,
        "url": url,
        "interval_hours": interval_hours,
        "created_at": datetime.now().isoformat(),
        "last_scrape": None,
        "total_scrapes": 0,
    }

    path = os.path.join(SCRAPE_SCHEDULE_DIR, f"{schedule_id}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)

    return schedule_id


def run_scheduled_scrape(schedule_id: str) -> ScrapeResult:
    """Run a scheduled scrape and save results."""
    path = os.path.join(SCRAPE_SCHEDULE_DIR, f"{schedule_id}.json")
    if not os.path.isfile(path):
        return ScrapeResult(url="", title="", status_code=404, content_size=0,
                           scraped_at="", data={}, error="Schedule not found")

    with open(path, 'r', encoding='utf-8') as f:
        schedule = json.load(f)

    result = scrape_url(schedule["url"])

    # Update schedule
    schedule["last_scrape"] = datetime.now().isoformat()
    schedule["total_scrapes"] += 1
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)

    # Save result
    result_path = os.path.join(SCRAPE_SCHEDULE_DIR, f"{schedule_id}_result_{schedule['total_scrapes']}.json")
    with open(result_path, 'w', encoding='utf-8') as f:
        f.write(export_to_json(result))

    return result


def list_schedules() -> list:
    """List all scheduled scrapes."""
    schedules = []
    if not os.path.isdir(SCRAPE_SCHEDULE_DIR):
        return schedules
    for fn in os.listdir(SCRAPE_SCHEDULE_DIR):
        if fn.endswith('.json') and '_result_' not in fn:
            with open(os.path.join(SCRAPE_SCHEDULE_DIR, fn), 'r', encoding='utf-8') as f:
                schedules.append(json.load(f))
    return schedules


# ═══ Quick Integration ═══
def scrape_and_summarize(url: str) -> dict:
    """Scrape a URL + return a summary suitable for AI chat."""
    result = scrape_url(url)
    if not result.ok:
        return {"error": result.error, "url": url}

    return {
        "url": url,
        "title": result.data.get("title", ""),
        "tables_found": result.data.get("tables_count", 0),
        "lists_found": result.data.get("lists_count", 0),
        "links_found": result.data.get("links_count", 0),
        "headings": [h["text"] for h in result.data.get("headings", [])[:10]],
        "meta_description": result.data.get("meta", {}).get("description", ""),
        "text_snippet": result.data.get("text_preview", "")[:500],
        "full_data": result.data,
    }
