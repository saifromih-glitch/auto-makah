# 🕋 Auto Makah — Expert Training Launcher

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Clear knowledge for fresh train
from knowledge.base import knowledge_base
knowledge_base._entries.clear()

from knowledge.trainer import seed_knowledge_base, train_expert_prompt
from agents.experts.profiles import EXPERT_PROFILES
from agents.experts.orchestrator import ExpertOrchestrator

# Seed knowledge
stats = seed_knowledge_base()
print(f"Knowledge: {stats['total_entries']} entries across {stats['domains']}")

# Build orchestrator with trained prompts
orch = ExpertOrchestrator()

for name, profile in EXPERT_PROFILES.items():
    domain = profile.get("domain", "general")
    trained = train_expert_prompt(domain)
    if trained:
        p = dict(profile)
        p["system_prompt"] = p.get("system_prompt", "") + "\n\n" + trained
        orch.register_from_profile(p)
    else:
        orch.register_from_profile(profile)

experts = orch.list_experts()
print(f"\nTrained Experts: {len(experts)}")
for e in experts:
    plen = len(e.system_prompt)
    indicator = "OK" if plen > 500 else "LOW" if plen > 200 else "EMPTY"
    print(f"  [{indicator}] {e.name} ({e.domain}): {plen} chars")
