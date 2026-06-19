import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=== Auto Makah Integration Test ===\n")

# 1. Core
from core.agent import runtime
agent = runtime.create_agent("romih", {"domain": "b2b"})
print(f"1. Agent: {agent.name} created OK")

# 2. Tools
from core.tools import registry
print(f"2. Tools: {registry.count()} registered OK")

# 3. Connectors
from core.connectors import HybridRouter, FallbackChain, GLM4Connector, GPT4oMiniConnector
router_model = HybridRouter()
print(f"3. Connectors: HybridRouter with {len(router_model.text_chain.models)} text + {len(router_model.file_chain.models)} file OK")

# 4. Route detection
route = router_model.detect_route("احسب الزكاة")
assert route == "accounting", f"Expected accounting, got {route}"
route = router_model.detect_route("اعمل جدول إكسيل")
assert route == "file", f"Expected file, got {route}"
route = router_model.detect_route("كيف حالي")
assert route == "text", f"Expected text, got {route}"
print("4. Route detection: 3/3 OK")

# 5. Knowledge
from knowledge.base import knowledge_base, KnowledgeEntry
knowledge_base.add(KnowledgeEntry("accounting", "Zakat", "الزكاة = 2.5% × الوعاء الزكوي", ["zakat"]))
from knowledge.search import search_engine
domains = search_engine.domain_detect("احسب الزكاة")
assert "accounting" in domains
print("5. Knowledge: domain detection OK")

# 6. Memory
from memory.store import memory
memory.save_fact("user_1", "name", "محمد")
from memory.recall import injector
ctx = injector.for_agent("ما هي الزكاة", user_id="user_1", session_id="s1")
assert ctx["knowledge_domains"], "No domains detected"
print("6. Memory + Context: OK")

# 7. DB Schema
from db.schema import Base
tables = Base.metadata.tables.keys()
assert len(tables) == 9, f"Expected 9 tables, got {len(tables)}"
print(f"7. DB Schema: {len(tables)} tables OK")

# 8. Swarm
from agents.swarm import SwarmOrchestrator, route_to_expert
from agents.experts.orchestrator import ExpertOrchestrator
from agents.experts.profiles import EXPERT_PROFILES
orch = ExpertOrchestrator()
for name, profile in EXPERT_PROFILES.items():
    orch.register_from_profile(profile)
print(f"8. Swarm: {len(orch.list_experts())} experts registered OK")

# 9. API
from api.app import app
routes = [r for r in app.routes if hasattr(r, 'path') and hasattr(r, 'methods')]
api_paths = [r.path for r in routes]
assert "/api/health" in api_paths
assert "/api/tools" in api_paths
print(f"9. API: {len(routes)} routes OK")

# 10. Telegram
from channels.telegram import router as tg_router
assert len(tg_router.routes) >= 1
print(f"10. Telegram: {len(tg_router.routes)} route(s) OK")

print("\n=== ALL 10 COMPONENTS PASSED ===")
print("Milestone 2: Model Connectors + Telegram = Ready")
