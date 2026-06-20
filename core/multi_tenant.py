"""
Multi-Tenant Isolation Manager for Auto Makah.

Each tenant gets an isolated namespace: own agents, knowledge base shard,
memory partition, and plan-based quotas.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# ── global stubs (provided by core runtime) ──────────────────────────
# In production these are imported from auto_makah.core; for now we
# define lightweight stand-ins so the module stays self-consistent.
try:
    from auto_makah.core.runtime import knowledge_base, runtime  # type: ignore[import-untyped]
except ImportError:
    knowledge_base: Dict[str, Any] = {}   # type: ignore[no-redef]
    runtime: Dict[str, Any] = {}          # type: ignore[no-redef]


# ── plan definitions ─────────────────────────────────────────────────

class Plan(str, Enum):
    """Subscription tiers."""
    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"


PLAN_LIMITS: Dict[Plan, Dict[str, Optional[int]]] = {
    Plan.FREE:     {"max_agents": 5,    "max_req_per_day": 100},
    Plan.PRO:      {"max_agents": 20,   "max_req_per_day": 1000},
    Plan.BUSINESS: {"max_agents": None, "max_req_per_day": None},
}


# ── data structures ──────────────────────────────────────────────────

@dataclass
class TenantContext:
    """Isolated context for a single tenant."""
    tenant_id: str
    name: str
    email: str
    plan: Plan
    agents: Dict[str, Any] = field(default_factory=dict)
    knowledge: Dict[str, Any] = field(default_factory=dict)
    memory: List[Dict[str, Any]] = field(default_factory=list)
    usage: Dict[str, int] = field(default_factory=lambda: {"req_today": 0})

    @property
    def agent_count(self) -> int:
        return len(self.agents)

    @property
    def max_agents(self) -> Optional[int]:
        return PLAN_LIMITS[self.plan]["max_agents"]

    @property
    def max_req_per_day(self) -> Optional[int]:
        return PLAN_LIMITS[self.plan]["max_req_per_day"]

    def can_add_agent(self) -> bool:
        limit = self.max_agents
        return limit is None or self.agent_count < limit

    def can_make_request(self) -> bool:
        limit = self.max_req_per_day
        return limit is None or self.usage["req_today"] < limit

    def record_request(self) -> None:
        self.usage["req_today"] += 1


# ── manager ──────────────────────────────────────────────────────────

class TenantManager:
    """
    Multi-tenant isolation manager.

    Each tenant operates in a strictly isolated namespace — agents,
    knowledge, and memory are never shared across tenants.  Quotas are
    enforced according to the subscription plan.

    Usage::

        tm = TenantManager()
        ctx = tm.create_tenant("Acme", "acme@example.com", Plan.PRO)
        ctx.agents["weather"] = WeatherAgent()
    """

    def __init__(self) -> None:
        self._tenants: Dict[str, TenantContext] = {}

    # ── public API ───────────────────────────────────────────────────

    def create_tenant(self, name: str, email: str, plan: Plan | str = Plan.FREE) -> TenantContext:
        """Create a new tenant with an isolated namespace.

        Args:
            name: Human-readable tenant name.
            email: Contact email for the tenant owner.
            plan: Subscription plan (``free``, ``pro``, or ``business``).

        Returns:
            The newly created ``TenantContext``.
        """
        if isinstance(plan, str):
            plan = Plan(plan)

        tenant_id = uuid.uuid4().hex[:12]
        ctx = TenantContext(
            tenant_id=tenant_id,
            name=name,
            email=email,
            plan=plan,
        )

        # Seed an isolated knowledge shard inside the global store.
        knowledge_base.setdefault("tenants", {})[tenant_id] = ctx.knowledge
        runtime.setdefault("tenants", {})[tenant_id] = {
            "name": name,
            "plan": plan.value,
        }

        self._tenants[tenant_id] = ctx
        return ctx

    def get_tenant_context(self, tenant_id: str) -> TenantContext:
        """Return the isolated context for *tenant_id*.

        Raises:
            KeyError: If *tenant_id* is unknown.
        """
        return self._tenants[tenant_id]

    def list_tenants(self) -> List[TenantContext]:
        """Return every tenant's context, newest last."""
        return list(self._tenants.values())

    def get_tenant(self, tenant_id: str) -> Optional[TenantContext]:
        """Safe lookup — returns ``None`` instead of raising."""
        return self._tenants.get(tenant_id)

    def delete_tenant(self, tenant_id: str) -> bool:
        """Remove a tenant and scrub its isolated data.

        Returns:
            ``True`` if the tenant existed, ``False`` otherwise.
        """
        if tenant_id not in self._tenants:
            return False

        knowledge_base.get("tenants", {}).pop(tenant_id, None)
        runtime.get("tenants", {}).pop(tenant_id, None)
        del self._tenants[tenant_id]
        return True

    # ── helpers ──────────────────────────────────────────────────────

    def quota_ok(self, tenant_id: str) -> bool:
        """Check whether *tenant_id* has not exhausted its daily quota."""
        ctx = self._tenants.get(tenant_id)
        if ctx is None:
            return False
        return ctx.can_make_request()

    def record_usage(self, tenant_id: str) -> None:
        """Bump the daily request counter for *tenant_id*."""
        ctx = self._tenants.get(tenant_id)
        if ctx is not None:
            ctx.record_request()
