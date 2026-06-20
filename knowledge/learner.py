# 🕋 Auto Makah — Learning Loop

from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from memory.store import memory


class LearningLoop:
    """Continuous improvement system — learns from every interaction."""

    def __init__(self):
        self.feedback_log: List[Dict] = []
        self.successful_patterns: Dict[str, List[str]] = {}  # domain → [good responses]
        self.improvement_log: List[Dict] = []

    def record_interaction(
        self,
        user_id: str,
        message: str,
        response: str,
        domain: str = "general",
        success: bool = True,
    ):
        """Record a user interaction for learning."""
        entry = {
            "user_id": user_id,
            "message": message[:500],
            "response": response[:500],
            "domain": domain,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.feedback_log.append(entry)

        # Store in memory
        memory.save_fact(user_id, f"last_interaction_{domain}", message[:100])
        memory.save_fact(user_id, "total_interactions", len(self.feedback_log))

        return entry

    def rate_response(self, message: str, response: str) -> Dict[str, Any]:
        """Rate a response quality using heuristic checks."""
        score = 5
        issues = []

        # Check: empty response
        if not response or len(response) < 10:
            score = 1
            issues.append("empty_short")

        # Check: too generic
        generic_phrases = [
            "كيف أقدر أساعدك",
            "أنا مساعد",
            "وش تبي",
            "عذراً",
        ]
        for phrase in generic_phrases:
            if phrase in response:
                score -= 1
                issues.append(f"generic:{phrase}")

        # Check: has numbers/stats (depth)
        has_numbers = any(c.isdigit() for c in response)
        if not has_numbers and len(response) > 100:
            score -= 0.5
            issues.append("no_data")

        # Check: too short for complex question
        if len(message) > 100 and len(response) < 200:
            score -= 1
            issues.append("too_short")

        return {
            "score": max(1, round(score, 1)),
            "issues": issues,
            "quality": "good" if score >= 4 else "needs_improvement" if score >= 3 else "poor",
        }

    def extract_knowledge(self, response: str, domain: str = "general"):
        """Extract reusable knowledge from a good response."""
        if len(response) < 50:
            return None

        self.successful_patterns.setdefault(domain, []).append(response[:500])

        # Keep only top 10 per domain
        if len(self.successful_patterns[domain]) > 10:
            self.successful_patterns[domain] = self.successful_patterns[domain][-10:]

        return {
            "domain": domain,
            "extracted_length": len(response),
            "patterns_count": len(self.successful_patterns[domain]),
        }

    def compile_improvements(self) -> str:
        """Compile learned improvements into a prompt fragment."""
        parts = []
        for domain, patterns in self.successful_patterns.items():
            if patterns:
                parts.append(f"[Learned patterns — {domain}]")
                for i, pattern in enumerate(patterns[-3:]):
                    parts.append(f"  Example {i+1}: {pattern[:200]}")

        return "\n".join(parts) if parts else ""

    def stats(self) -> Dict[str, Any]:
        return {
            "total_interactions": len(self.feedback_log),
            "domains_learned": list(self.successful_patterns.keys()),
            "patterns_stored": sum(len(v) for v in self.successful_patterns.values()),
            "recent_quality": self._recent_quality(),
        }

    def _recent_quality(self) -> Dict[str, Any]:
        recent = self.feedback_log[-10:] if self.feedback_log else []
        if not recent:
            return {"avg_score": 0, "count": 0}
        scores = [self.rate_response(e["message"], e["response"])["score"] for e in recent]
        return {
            "avg_score": round(sum(scores) / len(scores), 1),
            "count": len(scores),
        }


# Global learning loop
learner = LearningLoop()
