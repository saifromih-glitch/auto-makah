import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test all modules
from core.agent import runtime, AgentRuntime
from core.tools import registry, Tool, ToolCategory
from knowledge.base import knowledge_base, KnowledgeEntry, load_knowledge_from_dict
from knowledge.search import search_engine, KnowledgeSearch
from knowledge.domains.accounting import ACCOUNTING_PROMPT
from knowledge.domains.marketing import MARKETING_PROMPT
from knowledge.domains.legal import LEGAL_PROMPT
from knowledge.domains.engineering import ENGINEERING_PROMPT
from memory.store import memory, MemoryStore
from memory.recall import injector, ContextInjector

# Test knowledge base
knowledge_base.add(KnowledgeEntry(
    domain="accounting",
    title="IFRS Overview",
    content=ACCOUNTING_PROMPT[:500],
    tags=["ifrs", "socpa"]
))
knowledge_base.add(KnowledgeEntry(
    domain="marketing",
    title="GSTIC Framework",
    content=MARKETING_PROMPT[:500],
    tags=["gstic", "strategy"]
))

# Check domain detection
domains = search_engine.domain_detect("احسب الزكاة المستحقة على شركتي")
assert "accounting" in domains, f"Expected accounting, got {domains}"

# Create test agent
agent = runtime.create_agent("romih", {"domain": "b2b", "language": "ar"})
assert runtime.get_agent("romih") is not None

# Memory test
memory.save_fact("user_1", "industry", "ورشة سيارات")
memory.save_fact("user_1", "location", "جدة")
facts = memory.get_all_facts("user_1")
assert facts["industry"] == "ورشة سيارات"

# Knowledge stats
stats = knowledge_base.stats()
assert stats["total_entries"] == 2

results = []
results.append(f"Agents: {len(runtime.agents)}")
results.append(f"Tools: {registry.count()}")
results.append(f"Knowledge domains: {knowledge_base.domains()}")
results.append(f"Memory users: {len(memory._long_term)}")
results.append(f"Legal prompt length: {len(LEGAL_PROMPT)} chars")
results.append(f"Engineering prompt length: {len(ENGINEERING_PROMPT)} chars")
results.append("")
results.append("ALL TESTS PASSED")
results.append("Milestone 1: Foundation Complete")

for r in results:
    print(r)
