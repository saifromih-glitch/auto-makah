# ═══════════════════════════════════════════════════════
# 🛡️ Controlled Autonomy — Lopp Step 14: Security Gate
# Human approval required for critical actions
# Purpose: Autonomy is controlled, not uncontrolled
# ═══════════════════════════════════════════════════════

import json, os, hashlib, logging, time
from datetime import datetime, timedelta
from enum import Enum

log = logging.getLogger("autonomy")


class ActionRisk(Enum):
    LOW = "low"           # Read-only, no side effects
    MEDIUM = "medium"     # Write/modify with audit trail
    HIGH = "high"         # Infrastructure, secrets, payments
    CRITICAL = "critical" # Delete data, deploy to production, billing


CRITICAL_ACTIONS = {
    "deploy": ActionRisk.CRITICAL,
    "delete": ActionRisk.CRITICAL,
    "billing": ActionRisk.CRITICAL,
    "payment": ActionRisk.CRITICAL,
    "config_change": ActionRisk.HIGH,
    "secret_rotate": ActionRisk.HIGH,
    "domain_update": ActionRisk.HIGH,
    "user_data_delete": ActionRisk.CRITICAL,
    "database_migrate": ActionRisk.HIGH,
    "api_key_create": ActionRisk.HIGH,
    "webhook_update": ActionRisk.MEDIUM,
    "file_write": ActionRisk.LOW,
    "read": ActionRisk.LOW,
    "chat": ActionRisk.LOW,
    "search": ActionRisk.LOW,
    "analyze": ActionRisk.LOW,
}


class AutonomyGate:
    """
    Lopp Step 14: Controlled Autonomy Gate.
    
    Rule: The more power the loop has, the more responsibility it carries.
    Critical actions require human approval. Low-risk actions are auto-approved.
    """

    def __init__(self, approval_dir: str = None):
        self.approval_dir = approval_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "approvals"
        )
        os.makedirs(self.approval_dir, exist_ok=True)
        self.auto_approved_count = 0
        self.blocked_count = 0

    def classify(self, action: str) -> ActionRisk:
        """Classify an action's risk level."""
        return CRITICAL_ACTIONS.get(action.lower(), ActionRisk.MEDIUM)

    def needs_approval(self, action: str, details: dict = None) -> dict:
        """
        Check if an action needs human approval.
        Returns: {"needs_approval": bool, "risk": str, "reason": str}
        """
        risk = self.classify(action)
        
        result = {
            "needs_approval": False,
            "risk": risk.value,
            "reason": "",
            "action": action,
            "details": details,
        }

        if risk in (ActionRisk.CRITICAL, ActionRisk.HIGH):
            result["needs_approval"] = True
            result["reason"] = f"Action '{action}' is {risk.value} risk — requires human approval"
            self.blocked_count += 1
        elif risk == ActionRisk.MEDIUM:
            result["needs_approval"] = True
            result["reason"] = f"Action '{action}' is {risk.value} risk — approval recommended"
        else:
            self.auto_approved_count += 1
            result["reason"] = f"Action '{action}' is {risk.value} risk — auto-approved"

        return result

    def request_approval(self, action: str, requested_by: str, details: dict = None) -> str:
        """
        Create an approval request.
        Returns approval_id — human must confirm to proceed.
        """
        approval_id = hashlib.md5(
            f"{action}{details}{time.time()}".encode()
        ).hexdigest()[:12]

        approval = {
            "approval_id": approval_id,
            "action": action,
            "requested_by": requested_by,
            "details": details or {},
            "risk": self.classify(action).value,
            "status": "pending",
            "requested_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
            "approved_by": None,
            "approved_at": None,
        }

        path = os.path.join(self.approval_dir, f"{approval_id}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(approval, f, ensure_ascii=False, indent=2)

        log.warning(f"🛡️ Approval requested: {action} (risk={approval['risk']}, id={approval_id})")
        return approval_id

    def approve(self, approval_id: str, approved_by: str) -> bool:
        """Approve an action. Returns True if successful."""
        path = os.path.join(self.approval_dir, f"{approval_id}.json")
        if not os.path.isfile(path):
            return False

        with open(path, 'r', encoding='utf-8') as f:
            approval = json.load(f)

        if approval["status"] != "pending":
            return False

        approval["status"] = "approved"
        approval["approved_by"] = approved_by
        approval["approved_at"] = datetime.now().isoformat()

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(approval, f, ensure_ascii=False, indent=2)

        log.info(f"✅ Approval granted: {approval_id} by {approved_by}")
        return True

    def deny(self, approval_id: str, denied_by: str, reason: str = "") -> bool:
        """Deny an approval request."""
        path = os.path.join(self.approval_dir, f"{approval_id}.json")
        if not os.path.isfile(path):
            return False

        with open(path, 'r', encoding='utf-8') as f:
            approval = json.load(f)

        approval["status"] = "denied"
        approval["denied_by"] = denied_by
        approval["denied_at"] = datetime.now().isoformat()
        approval["deny_reason"] = reason

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(approval, f, ensure_ascii=False, indent=2)

        log.warning(f"❌ Approval denied: {approval_id} by {denied_by}: {reason}")
        return True

    def get_pending(self) -> list:
        """Get all pending approvals."""
        pending = []
        if not os.path.isdir(self.approval_dir):
            return pending
        for fn in os.listdir(self.approval_dir):
            if fn.endswith('.json'):
                with open(os.path.join(self.approval_dir, fn), 'r', encoding='utf-8') as f:
                    approval = json.load(f)
                    if approval.get("status") == "pending":
                        pending.append(approval)
        return sorted(pending, key=lambda a: a["requested_at"], reverse=True)

    def get_stats(self) -> dict:
        """Get autonomy gate statistics."""
        pending = self.get_pending()
        return {
            "auto_approved": self.auto_approved_count,
            "blocked": self.blocked_count,
            "pending_approvals": len(pending),
            "pending_actions": [a["action"] for a in pending],
        }

    def cleanup_expired(self):
        """Deny all expired approval requests."""
        now = datetime.now()
        for fn in os.listdir(self.approval_dir):
            if not fn.endswith('.json'):
                continue
            path = os.path.join(self.approval_dir, fn)
            with open(path, 'r', encoding='utf-8') as f:
                approval = json.load(f)
            if approval.get("status") == "pending":
                expires = datetime.fromisoformat(approval["expires_at"])
                if now > expires:
                    self.deny(approval["approval_id"], "system", "Expired")


# ═══ Quick integration ═══
_global_gate = None

def get_autonomy_gate() -> AutonomyGate:
    """Get or create the global autonomy gate."""
    global _global_gate
    if _global_gate is None:
        _global_gate = AutonomyGate()
    return _global_gate
