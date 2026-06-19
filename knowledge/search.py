# ═══════════════════════════════════════════
# 🕋 Auto Makah — Knowledge Search
# ═══════════════════════════════════════════

from typing import List, Dict, Any
from .base import KnowledgeEntry, knowledge_base


class KnowledgeSearch:
    """Search engine over knowledge base — keyword + optional semantic."""

    def __init__(self, kb=None):
        self.kb = kb or knowledge_base
        self._embedding_model = None  # Lazy loading

    def keyword_search(self, query: str, domain: str = None, limit: int = 5) -> List[KnowledgeEntry]:
        """Fast keyword-based search."""
        results = self.kb.search(query, domain)
        # Sort by relevance (more hits = higher rank)
        query_terms = query.lower().split()
        scored = []
        for entry in results:
            score = sum(
                1 for term in query_terms
                if term in entry.title.lower() or term in entry.content.lower()
            )
            scored.append((score, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:limit]]

    def semantic_search(self, query: str, domain: str = None, limit: int = 5) -> List[KnowledgeEntry]:
        """Semantic search — falls back to keyword if no embedding model."""
        # TODO: Add sentence-transformers integration
        return self.keyword_search(query, domain, limit)

    def domain_detect(self, text: str) -> List[str]:
        """Detect relevant knowledge domains from text keywords."""
        domain_keywords = {
            "accounting": ["محاسبة", "ضريبة", "زكاة", "قيد", "ميزانية", "إيراد", "مصروف", "ميزان", "مراجعة"],
            "legal": ["قانون", "نظام", "محامي", "عقد", "دعوى", "لائحة", "تشريع", "محكمة"],
            "marketing": ["تسويق", "عميل", "حملة", "إعلان", "علامة", "سوق", "منافس", "تسعير"],
            "engineering": ["ورشة", "هيدروليك", "تصنيع", "صيانة", "معدات", "إنتاج"],
            "hr": ["موظف", "راتب", "تأمين", "عقد عمل", "موارد", "تدريب"],
        }
        text_lower = text.lower()
        detected = []
        for domain, keywords in domain_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score >= 1:
                detected.append(domain)
        return detected[:2]  # Max 2 domains

    def search_and_compile(self, query: str, max_chars: int = 2000) -> str:
        """Search knowledge, compile into prompt-ready string."""
        domains = self.domain_detect(query)
        if not domains:
            return ""

        parts = []
        total_chars = 0
        for domain in domains:
            entries = self.keyword_search(query, domain, limit=3)
            if entries:
                domain_text = f"\n=== {domain} ===\n"
                for e in entries:
                    snippet = e.content[:300]
                    domain_text += f"[{e.title}] {snippet}\n"
                    total_chars += len(snippet)
                parts.append(domain_text)
                if total_chars >= max_chars:
                    break

        return "\n".join(parts) if parts else ""


# Global search instance
search_engine = KnowledgeSearch()
