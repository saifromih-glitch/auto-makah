# 🕋 Auto Makah — Skills/Plugin Marketplace

from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass, field


@dataclass
class Skill:
    """A skill/plugin that can be attached to any agent."""
    name: str
    description: str
    domain: str
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    execute: Optional[Callable] = None
    prompt_fragment: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "domain": self.domain,
            "version": self.version,
            "tags": self.tags,
        }


class SkillMarketplace:
    """Register, discover, and attach skills to agents."""

    def __init__(self):
        self._skills: Dict[str, Skill] = {}
        self._installed: Dict[str, List[str]] = {}  # agent_name → [skill_names]

    def register(self, skill: Skill) -> "SkillMarketplace":
        self._skills[skill.name] = skill
        return self

    def get(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def list_all(self) -> List[Dict[str, Any]]:
        return [s.to_dict() for s in self._skills.values()]

    def search(self, query: str) -> List[Dict[str, Any]]:
        q = query.lower()
        return [
            s.to_dict()
            for s in self._skills.values()
            if q in s.name.lower() or q in s.description.lower() or any(q in t.lower() for t in s.tags)
        ]

    def list_by_domain(self, domain: str) -> List[Dict[str, Any]]:
        return [s.to_dict() for s in self._skills.values() if s.domain == domain]

    def install(self, agent_name: str, skill_name: str) -> bool:
        """Attach a skill to an agent."""
        if skill_name not in self._skills:
            return False

        from core.agent import runtime
        agent = runtime.get_agent(agent_name)
        if not agent:
            return False

        self._installed.setdefault(agent_name, []).append(skill_name)

        skill = self._skills[skill_name]
        if skill.execute:
            agent.register_tool(f"skill_{skill_name}", skill.execute, skill.description)
        if skill.prompt_fragment:
            current = agent.system_prompt or ""
            agent.set_system_prompt(current + f"\n\n[Skill: {skill.name}]\n{skill.prompt_fragment}")

        return True

    def uninstall(self, agent_name: str, skill_name: str):
        self._installed.get(agent_name, []).remove(skill_name)

    def get_installed(self, agent_name: str) -> List[str]:
        return self._installed.get(agent_name, [])

    def count(self) -> int:
        return len(self._skills)


# ═══════════════════════════════
# Global marketplace
# ═══════════════════════════════
marketplace = SkillMarketplace()


# ═══════════════════════════════
# Pre-built skills
# ═══════════════════════════════

marketplace.register(Skill(
    name="zakat_calculator",
    description="حساب زكاة الشركات السعودية",
    domain="accounting",
    tags=["زكاة", "مالية", "سعودي"],
    prompt_fragment="أنت خبير زكاة شركات. الزكاة = 2.5% × (الأصول الزكوية - الخصوم).",
))

marketplace.register(Skill(
    name="gstic_planner",
    description="خطة GSTIC كاملة للنمو",
    domain="marketing",
    tags=["تسويق", "استراتيجية", "نمو"],
    prompt_fragment="استخدم GSTIC: Goals → Strategy → Tactics → Implementation → Control.",
))

marketplace.register(Skill(
    name="legal_advisor",
    description="مستشار قانوني سعودي",
    domain="legal",
    tags=["قانون", "نظام", "سعودي"],
    prompt_fragment="استند إلى الأنظمة السعودية. استشهد برقم المادة. فرق بين الرأي والنص.",
))

marketplace.register(Skill(
    name="workshop_analyzer",
    description="تحليل ورشة — تكاليف — هيدروليك",
    domain="engineering",
    tags=["ورشة", "هيدروليك", "تصنيع"],
    prompt_fragment="شخص المشكلة. حلل عنق الزجاجة. احسب التكلفة والعائد.",
))

marketplace.register(Skill(
    name="vision_2030_insight",
    description="رؤية 2030 — فرص — مشاريع",
    domain="strategy",
    tags=["رؤية 2030", "PIF", "نيوم"],
    prompt_fragment="اربط برؤية 2030. اذكر الجهة الحكومية. حدد الحافز المتاح.",
))
