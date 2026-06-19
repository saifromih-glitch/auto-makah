# ═══════════════════════════════════════════
# 🕋 Auto Makah — Knowledge Base Core
# ═══════════════════════════════════════════

from typing import Dict, List, Optional, Any
from datetime import datetime
import json


class KnowledgeEntry:
    """A single knowledge entry."""

    def __init__(
        self,
        domain: str,
        title: str,
        content: str,
        tags: List[str] = None,
        source_url: str = None,
    ):
        self.domain = domain
        self.title = title
        self.content = content
        self.tags = tags or []
        self.source_url = source_url
        self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "title": self.title,
            "tags": self.tags,
            "source_url": self.source_url,
            "created_at": self.created_at,
        }

    def summary(self, max_chars: int = 500) -> str:
        return self.content[:max_chars] + ("..." if len(self.content) > max_chars else "")


class KnowledgeBase:
    """Domain-specific knowledge store."""

    def __init__(self):
        self._entries: Dict[str, List[KnowledgeEntry]] = {}  # domain → entries

    def add(self, entry: KnowledgeEntry) -> "KnowledgeBase":
        self._entries.setdefault(entry.domain, []).append(entry)
        return self

    def get_by_domain(self, domain: str) -> List[KnowledgeEntry]:
        return self._entries.get(domain, [])

    def search(self, query: str, domain: str = None) -> List[KnowledgeEntry]:
        results = []
        query_lower = query.lower()
        domains = [domain] if domain else self._entries.keys()

        for dom in domains:
            for entry in self._entries.get(dom, []):
                if (
                    query_lower in entry.content.lower()
                    or query_lower in entry.title.lower()
                    or any(query_lower in tag.lower() for tag in entry.tags)
                ):
                    results.append(entry)

        return results

    def compile_prompt(self, domain: str = None, max_entries: int = 10) -> str:
        """Compile knowledge into an injectable prompt fragment."""
        if domain and domain in self._entries:
            entries = self._entries[domain][:max_entries]
        else:
            entries = []
            for dom_entries in self._entries.values():
                entries.extend(dom_entries[:max_entries])

        if not entries:
            return ""

        lines = [f"\n=== Knowledge: {domain or 'all'} ===\n"]
        for e in entries:
            lines.append(f"[{e.title}] {e.content[:300]}\n")
        return "\n".join(lines)

    def domains(self) -> List[str]:
        return list(self._entries.keys())

    def stats(self) -> Dict[str, Any]:
        return {
            "total_entries": sum(len(v) for v in self._entries.values()),
            "domains": self.domains(),
            "by_domain": {d: len(v) for d, v in self._entries.items()},
        }


def load_knowledge_from_dict(data: Dict[str, List[Dict]], kb: KnowledgeBase = None) -> KnowledgeBase:
    """Load knowledge from dict: {domain: [{title, content, tags, source_url}]}"""
    if kb is None:
        kb = KnowledgeBase()

    for domain, entries in data.items():
        for e in entries:
            kb.add(KnowledgeEntry(
                domain=domain,
                title=e.get("title", ""),
                content=e.get("content", ""),
                tags=e.get("tags", []),
                source_url=e.get("source_url"),
            ))
    return kb


# ═══════════════════════════════
# Global Knowledge Base
# ═══════════════════════════════
knowledge_base = KnowledgeBase()
