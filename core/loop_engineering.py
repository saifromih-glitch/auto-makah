# ═══════════════════════════════════════════════════════
# 🔁 Loop Engineering Core — v1.0
# Applied to: Auto Makah + Romih + Doctor Companies
# Based on: Lopp Engineering (14-step roadmap)
# ═══════════════════════════════════════════════════════

import json, os, time, hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Callable
from enum import Enum


# ═══ 1. FOUR CONDITIONS CHECK ═══
class LoopViability(Enum):
    VIABLE = "viable"
    NOT_FREQUENT = "not_frequent"
    NOT_MEASURABLE = "not_measurable"
    NO_RETRY = "no_retry"
    TOO_EXPENSIVE = "too_expensive"

def check_loop_viability(task_frequency_per_week: int, is_measurable: bool, 
                         can_retry: bool, cost_per_run_usd: float, 
                         value_per_run_usd: float) -> LoopViability:
    """The 4-conditions test before building any loop."""
    if task_frequency_per_week < 1:
        return LoopViability.NOT_FREQUENT
    if not is_measurable:
        return LoopViability.NOT_MEASURABLE
    if not can_retry:
        return LoopViability.NO_RETRY
    if cost_per_run_usd > value_per_run_usd:
        return LoopViability.TOO_EXPENSIVE
    return LoopViability.VIABLE


# ═══ 2. FIVE SECOND TEST ═══
def five_second_test(task: str) -> Dict[str, bool]:
    """Ask 5 questions before converting any workflow to autonomous loop."""
    return {
        "weekly_or_more": False,  # User must answer
        "auto_reject_bad": False,
        "agent_can_run_code": False,
        "clear_stop_point": False,
        "human_review_decisions": False,
    }


# ═══ 3. STATE FILE (Memory Layer) ═══
@dataclass
class LoopState:
    """Persistent state that survives between runs."""
    loop_id: str
    project: str
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    last_run: Optional[str] = None
    last_success: Optional[str] = None
    last_error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    learnings: List[str] = field(default_factory=list)
    blocked_tasks: List[str] = field(default_factory=list)
    context_snapshot: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, d: dict) -> "LoopState":
        return cls(**d)


STATE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "loop_states")
os.makedirs(STATE_DIR, exist_ok=True)

def load_state(loop_id: str, project: str = "default") -> LoopState:
    """Load persistent state for a loop."""
    path = os.path.join(STATE_DIR, f"{project}_{loop_id}.json")
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return LoopState.from_dict(json.load(f))
    return LoopState(loop_id=loop_id, project=project)

def save_state(state: LoopState):
    """Save loop state to disk."""
    path = os.path.join(STATE_DIR, f"{state.project}_{state.loop_id}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)


# ═══ 4. RETRY LOOP WITH VERIFICATION ═══
def run_with_retry(loop_id: str, project: str, action: Callable, 
                   verify: Optional[Callable[[Any], bool]] = None,
                   max_retries: int = 3) -> Dict[str, Any]:
    """
    Builder-Verifier loop:
    1. Execute action
    2. Verify result (if verifier provided)
    3. Retry on failure
    """
    state = load_state(loop_id, project)
    
    for attempt in range(1, max_retries + 1):
        state.retry_count = attempt
        state.total_runs += 1
        state.last_run = datetime.now().isoformat()
        
        try:
            result = action()
            
            # Verification gate
            if verify and not verify(result):
                state.last_error = f"Verification failed (attempt {attempt})"
                state.failed_runs += 1
                save_state(state)
                if attempt < max_retries:
                    continue
                return {"success": False, "error": state.last_error, "attempts": attempt}
            
            # Success
            state.successful_runs += 1
            state.last_success = datetime.now().isoformat()
            state.retry_count = 0
            state.last_error = None
            save_state(state)
            return {"success": True, "result": result, "attempts": attempt}
            
        except Exception as e:
            state.last_error = str(e)
            state.failed_runs += 1
            save_state(state)
            if attempt >= max_retries:
                return {"success": False, "error": str(e), "attempts": attempt}
    
    return {"success": False, "error": "Max retries exceeded"}


# ═══ 5. FALSE COMPLETION GUARD ═══
class CompletionGuard:
    """Prevents agents from saying 'done' when not really done."""
    
    CHECKS = ["tests_pass", "build_succeeds", "type_checks_pass", "api_returns_200", "arabic_intact"]
    
    @staticmethod
    def verify(result: Any, required_checks: List[str] = None) -> bool:
        """Run objective checks before accepting completion."""
        checks = required_checks or CompletionGuard.CHECKS
        results = {}
        for check in checks:
            results[check] = False  # Default: not verified
        return all(results.values())  # Only true if ALL checks pass


# ═══ 6. COMPREHENSION DEBT TRACKER ═══
@dataclass
class ComprehensionEntry:
    """Track every accepted change that wasn't fully understood."""
    timestamp: str
    file_path: str
    change_description: str
    understood: bool
    risk_level: str  # low, medium, high
    review_deadline: str  # Must review within X days

DEBT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "comprehension_debt")
os.makedirs(DEBT_DIR, exist_ok=True)

def record_comprehension_debt(project: str, file_path: str, 
                              change_description: str, understood: bool,
                              risk_level: str = "medium", review_days: int = 7):
    """Log comprehension debt — changes accepted without full understanding."""
    entry = ComprehensionEntry(
        timestamp=datetime.now().isoformat(),
        file_path=file_path,
        change_description=change_description,
        understood=understood,
        risk_level=risk_level,
        review_deadline=(datetime.now() + timedelta(days=review_days)).isoformat()
    )
    path = os.path.join(DEBT_DIR, f"{project}_debt.jsonl")
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(asdict(entry), ensure_ascii=False) + '\n')
    
    if not understood:
        return f"⚠️ دين فهم مُسجل: {change_description[:80]}..."

def get_comprehension_debt(project: str) -> List[ComprehensionEntry]:
    """Get all unpaid comprehension debt for a project."""
    path = os.path.join(DEBT_DIR, f"{project}_debt.jsonl")
    if not os.path.exists(path):
        return []
    entries = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            entries.append(ComprehensionEntry(**json.loads(line)))
    return entries


# ═══ 7. BUILDER / REVIEWER / VERIFIER SPLIT ═══
class AgentRole(Enum):
    BUILDER = "builder"     # Generates/creates
    REVIEWER = "reviewer"   # Evaluates quality
    VERIFIER = "verifier"   # Checks correctness

def three_agent_pipeline(task: str, builder_fn: Callable, 
                         reviewer_fn: Callable, verifier_fn: Callable) -> Dict:
    """
    Generator → Evaluator → Verifier pattern.
    Each agent has different goal, challenges others' assumptions.
    """
    # Step 1: Builder generates
    generation = builder_fn(task)
    
    # Step 2: Reviewer evaluates
    review = reviewer_fn(generation)
    
    # Step 3: Verifier checks
    verification = verifier_fn(generation, review)
    
    return {
        "generation": generation,
        "review": review,
        "verification": verification,
        "accepted": verification.get("passed", False)
    }


# ═══ 8. LOOP ORCHESTRATOR ═══
class LoopOrchestrator:
    """Main orchestrator that ties all Loop Engineering components together."""
    
    def __init__(self, project: str):
        self.project = project
        self.state = load_state("orchestrator", project)
    
    def should_loop_run(self, loop_id: str) -> bool:
        """Check if a loop should run based on its schedule and state."""
        state = load_state(loop_id, self.project)
        # Always run if never run before
        if not state.last_run:
            return True
        # Don't run if last run was within 1 minute (debounce)
        last = datetime.fromisoformat(state.last_run)
        if datetime.now() - last < timedelta(minutes=1):
            return False
        return True
    
    def run_loop(self, loop_id: str, action: Callable, verify: Callable = None):
        """Execute a full loop cycle with all guards."""
        if not self.should_loop_run(loop_id):
            return {"success": False, "reason": "debounced"}
        
        result = run_with_retry(loop_id, self.project, action, verify)
        return result
    
    def get_project_health(self) -> Dict:
        """Overall health dashboard for all loops in a project."""
        loops = []
        for f in os.listdir(STATE_DIR):
            if f.startswith(self.project) and f.endswith('.json'):
                with open(os.path.join(STATE_DIR, f), 'r', encoding='utf-8') as fp:
                    s = json.load(fp)
                    success_rate = (s['successful_runs'] / max(s['total_runs'], 1)) * 100
                    loops.append({
                        "loop_id": s['loop_id'],
                        "success_rate": round(success_rate, 1),
                        "total_runs": s['total_runs'],
                        "last_error": s['last_error'],
                        "learnings": len(s['learnings'])
                    })
        
        debt = get_comprehension_debt(self.project)
        unpaid = [d for d in debt if not d.understood]
        
        return {
            "project": self.project,
            "loops": loops,
            "active_loops": len(loops),
            "comprehension_debt_count": len(unpaid),
            "comprehension_debt_high_risk": len([d for d in unpaid if d.risk_level == "high"])
        }


# ═══ 9. QUICK INTEGRATION ═══
def apply_to_romih():
    """Apply Loop Engineering to Romih (Doctor Companies agent)."""
    orch = LoopOrchestrator("romih")
    return orch

def apply_to_auto_makah():
    """Apply Loop Engineering to Auto Makah platform."""
    orch = LoopOrchestrator("auto_makah")
    return orch

def apply_to_doctor_companies():
    """Apply Loop Engineering to Doctor Companies (Hospital)."""
    orch = LoopOrchestrator("doctor_companies")
    return orch


print("🔁 Loop Engineering Core loaded — v1.0")
print("   4-Conditions Check | 5-Second Test | State Files")
print("   Retry Loop | False Completion Guard | Comprehension Debt")
print("   Builder/Reviewer/Verifier | Loop Orchestrator")
