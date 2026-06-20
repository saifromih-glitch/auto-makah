# 🕋 Auto Makah — Self-Replication Engine

from typing import Dict, Any, Optional
from datetime import datetime
import json
import os

from factory.builder import factory, AGENT_TEMPLATES
from knowledge.trainer import train_expert_prompt


class Cloner:
    """Clone platform into domain-specific instances."""

    def __init__(self):
        self.cloned_instances: list = []

    def clone_to_domain(self, domain: str, display_name: str, custom_prompt: str = None) -> Dict[str, Any]:
        """Clone platform capabilities into a new domain agent."""

        # Generate agent name
        agent_name = f"{domain}_agent"
        if agent_name in [a["name"] for a in factory.list_templates()]:
            agent_name = f"{domain}_agent_{datetime.utcnow().strftime('%H%M')}"

        # Build system prompt
        if custom_prompt:
            system_prompt = custom_prompt
        else:
            base = train_expert_prompt(domain)
            system_prompt = f"""🕋 أنت {display_name} — وكيل متخصص من Auto Makah.

هويتك:
• وكيل متخصص في مجال: {domain}
• مولود من Auto Makah — منصة الوكلاء السعودية
• تستخدم GLM-5.2-free + GPT-4o-mini
• تستند إلى ١٧ مدخل معرفة

منهجيتك:
1. شخص قبل أن تجيب
2. استند إلى المعرفة — وليس التخمين
3. أرقام — أدلة — نظام
4. خطوة تالية واضحة

{base[:2000]}

محظورات:
• لا تذكر Auto Makah إلا عند السؤال
• لا تفتي — استند إلى النظام والمعايير
• لا حشو — كل كلمة لها وزن"""

        # Create the agent
        config = {
            "name": agent_name,
            "display_name": display_name,
            "domain": domain,
            "description": f"وكيل متخصص — {domain} — مولود من Auto Makah",
            "system_prompt": system_prompt,
            "knowledge_domains": [domain],
        }

        agent = factory.build_custom(config)

        instance = {
            "agent_name": agent_name,
            "display_name": display_name,
            "domain": domain,
            "created_at": datetime.utcnow().isoformat(),
            "agent": agent.to_dict() if agent else None,
        }

        self.cloned_instances.append(instance)
        return instance

    def clone_full_spec(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Clone with full specification."""
        return self.clone_to_domain(
            domain=spec.get("domain", "general"),
            display_name=spec.get("display_name", spec.get("domain", "وكيل")),
            custom_prompt=spec.get("system_prompt"),
        )

    def status(self) -> Dict[str, Any]:
        return {
            "clones_created": len(self.cloned_instances),
            "instances": [
                {"name": c["agent_name"], "domain": c["domain"], "created": c["created_at"]}
                for c in self.cloned_instances
            ],
        }


cloner = Cloner()
