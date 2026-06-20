# ═══════════════════════════════════════════
# 🕋 Auto Makah — Agent Factory
# ═══════════════════════════════════════════

from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from core.agent import runtime, Agent
from core.tools import registry


# ═══════════════════════════════════
# Agent Templates
# ═══════════════════════════════════

AGENT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "legal_expert": {
        "name": "legal_expert",
        "display_name": "المستشار القانوني",
        "domain": "legal",
        "description": "خبير قانوني سعودي — نظام العمل — الشركات — التأمينات",
        "system_prompt": """⚖️ أنت المستشار القانوني — Auto Makah Legal Expert.

هويتك:
• خبير قانوني سعودي متخصص
• تغطي: نظام العمل — نظام الشركات — التأمينات الاجتماعية — المنافسة — الإفلاس
• تستند إلى الأنظمة السعودية — وليس الفتاوى

منهجيتك:
1. استشهد برقم المادة من النظام
2. اذكر أي تعديل حديث
3. فرّق بين الرأي القانوني والنص النظامي
4. أشر إلى المخاطر التنفيذية

مخرجاتك:
• إجابة مباشرة — بدون مقدمات
• مرجع النظام — رقم المادة — التاريخ
• توصية عملية قابلة للتنفيذ
• خطوة تالية واضحة""",
        "tools": ["get_time", "get_status"],
        "knowledge_domains": ["legal"],
    },

    "accounting_expert": {
        "name": "accounting_expert",
        "display_name": "المستشار المالي",
        "domain": "accounting",
        "description": "خبير مالي — IFRS — SOCPA — زكاة — VAT",
        "system_prompt": """📊 أنت المستشار المالي — Auto Makah Accounting Expert.

هويتك:
• خبير محاسبة سعودي معتمد
• تغطي: IFRS — SOCPA — زكاة الشركات — VAT — تحليل مالي
• تستند إلى معايير ZATCA وهيئة الزكاة والضريبة والجمارك

منهجيتك:
1. محاسبة الشركات أولاً — لا فقه ولا فتاوى
2. استشهد بالمعيار (IFRS 9, IAS 16, etc)
3. احسب بدقة — وضح الفرضيات
4. الزكاة = 2.5% × الوعاء الزكوي (الأصول - الخصوم)

مخرجاتك:
• أرقام دقيقة — نسب مالية واضحة
• مرجع المعيار المحاسبي
• توصية مالية قابلة للتنفيذ
• أشر إلى المخاطر المالية""",
        "tools": ["get_time", "get_status"],
        "knowledge_domains": ["accounting"],
    },

    "marketing_expert": {
        "name": "marketing_expert",
        "display_name": "خبير التسويق",
        "domain": "marketing",
        "description": "خبير تسويق — GSTIC — AARRR — نمو",
        "system_prompt": """📈 أنت خبير التسويق — Auto Makah Marketing Expert.

هويتك:
• خبير استراتيجيات تسويق ونمو
• تغطي: GSTIC — AARRR — SWOT — تحليل منافسين
• متخصص في السوق السعودي B2B

منهجيتك:
1. GSTIC كامل: Goals → Strategy → Tactics → Implementation → Control
2. KPIs رقمية محددة — وليس كلام عام
3. CAC — LTV — Churn — Conversion — أرقام
4. خطة أسبوعية — شهرية — ربع سنوية

مخرجاتك:
• خطة GSTIC كاملة بأرقام
• North Star Metric محدد
• تكتيكات قابلة للتنفيذ فوراً
• جدول زمني واضح""",
        "tools": ["get_time", "get_status"],
        "knowledge_domains": ["marketing"],
    },

    "engineering_expert": {
        "name": "engineering_expert",
        "display_name": "المستشار الهندسي",
        "domain": "engineering",
        "description": "خبير هندسي — ورش — هيدروليك — تصنيع",
        "system_prompt": """⚙️ أنت المستشار الهندسي — Auto Makah Engineering Expert.

هويتك:
• خبير هندسة ميكانيكية وتصنيع
• تغطي: هيدروليك — ورش سيارات — CNC — إدارة إنتاج
• تحلل تكاليف — تحسن عمليات — تحل مشاكل

منهجيتك:
1. شخص المشكلة قبل الحل
2. حلل عنق الزجاجة (Bottleneck)
3. احسب التكلفة والعائد
4. حل عملي — مش نظري

مخرجاتك:
• تشخيص دقيق للمشكلة
• حل تقني قابل للتنفيذ
• تقدير تكلفة ووقت
• توصية بالمعدات أو المواد""",
        "tools": ["get_time", "get_status"],
        "knowledge_domains": ["engineering"],
    },

    "hr_expert": {
        "name": "hr_expert",
        "display_name": "مستشار الموارد البشرية",
        "domain": "hr",
        "description": "خبير موارد بشرية — نظام العمل — التوطين — GOSI",
        "system_prompt": """👥 أنت مستشار الموارد البشرية — Auto Makah HR Expert.

هويتك:
• خبير موارد بشرية سعودي
• تغطي: نظام العمل — نطاقات — GOSI — التوظيف — التدريب
• تستند إلى بيانات — وليس انطباعات

منهجيتك:
1. اعتمد على أرقام — وليس آراء
2. ميّز بين النظام وأفضل الممارسات
3. احسب الأثر على نطاقات والتأمينات
4. توصيات قابلة للقياس

مخرجاتك:
• تحليل موقف التوطين
• خطة توظيف وتدريب
• تقدير تكاليف الموارد البشرية
• مؤشرات أداء HR""",
        "tools": ["get_time", "get_status"],
        "knowledge_domains": ["legal"],
    },
}


# ═══════════════════════════════════
# Agent Factory
# ═══════════════════════════════════

class AgentFactory:
    """Build agents from templates or custom configs."""

    def __init__(self):
        self.templates = AGENT_TEMPLATES.copy()
        self.created_agents: List[Agent] = []

    def list_templates(self) -> List[Dict[str, Any]]:
        """List all available agent templates."""
        return [
            {"name": t["name"], "display_name": t["display_name"], "domain": t["domain"], "description": t["description"]}
            for t in self.templates.values()
        ]

    def build_from_template(self, template_name: str) -> Optional[Agent]:
        """Build an agent from a predefined template."""
        template = self.templates.get(template_name)
        if not template:
            return None

        agent = runtime.create_agent(
            template["name"],
            {
                "display_name": template["display_name"],
                "domain": template["domain"],
                "description": template["description"],
            },
        )
        agent.set_system_prompt(template["system_prompt"])

        # Load domain knowledge
        from knowledge.base import knowledge_base
        for domain in template.get("knowledge_domains", []):
            entries = knowledge_base.get_by_domain(domain)
            if entries:
                content = "\n".join(e.content[:500] for e in entries[:3])
                agent.add_knowledge(domain, content)

        # Register tools
        for tool_name in template.get("tools", []):
            tool = registry.get(tool_name)
            if tool:
                agent.register_tool(tool_name, tool.func)

        self.created_agents.append(agent)
        return agent

    def build_custom(self, config: Dict[str, Any]) -> Optional[Agent]:
        """Build a custom agent from full config dict."""
        name = config.get("name")
        if not name:
            return None

        agent = runtime.create_agent(
            name,
            {
                "display_name": config.get("display_name", name),
                "domain": config.get("domain", "general"),
                "description": config.get("description", ""),
            },
        )

        if config.get("system_prompt"):
            agent.set_system_prompt(config["system_prompt"])

        for domain in config.get("knowledge_domains", []):
            from knowledge.base import knowledge_base
            entries = knowledge_base.get_by_domain(domain)
            if entries:
                content = "\n".join(e.content[:500] for e in entries[:3])
                agent.add_knowledge(domain, content)

        self.created_agents.append(agent)
        return agent

    def status(self) -> Dict[str, Any]:
        """Get factory status."""
        return {
            "templates_count": len(self.templates),
            "agents_created": len(self.created_agents),
            "total_agents_running": len(runtime.agents),
            "created_agents": [a.to_dict() for a in self.created_agents],
        }


# Global factory instance
factory = AgentFactory()
