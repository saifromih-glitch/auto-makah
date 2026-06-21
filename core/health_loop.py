# ═══════════════════════════════════════════════════════
# 🔁 Auto Health Loop — First Real Lopp Engineering Loop
# Self-waking: checks health every 10 minutes
# Logs state, reports failures, learns from patterns
# ═══════════════════════════════════════════════════════

import asyncio, logging, urllib.request, json, time, os, sys
from datetime import datetime

log = logging.getLogger("health_loop")

# ═══ Add parent to path ═══
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.loop_engineering import load_state, save_state, LoopState

HEALTH_URL = "https://auto-makah.fly.dev/api/health"
CHECK_INTERVAL_SECONDS = 600  # 10 minutes
ALERT_WINDOW_SECONDS = 3600   # Alert if unhealthy for 1 hour
STATE_KEY = "health_check"


class HealthLoop:
    """
    Lopp Step 5: Automation Heartbeat
    - Wakes itself every 10 min
    - Checks health endpoint
    - Logs state (healthy/unhealthy)
    - Alerts on sustained failure (>1hr)
    """

    def __init__(self):
        self.state = load_state(STATE_KEY, "auto_makah")
        self.consecutive_failures = 0
        self.last_healthy = None
        self.running = False

    async def _check_once(self) -> dict:
        """Single health check — returns status."""
        try:
            req = urllib.request.Request(HEALTH_URL, headers={"Accept": "application/json"})
            r = urllib.request.urlopen(req, timeout=10)
            data = json.loads(r.read().decode())
            status = data.get("status", "unknown")
            version = data.get("version", "?")
            agents = data.get("agents", 0)
            tools = data.get("tools", 0)

            return {
                "healthy": status == "operational",
                "status": status,
                "version": version,
                "agents": agents,
                "tools": tools,
                "latency_ms": 0,  # Simplified
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "healthy": False,
                "status": "error",
                "error": str(e)[:200],
                "timestamp": datetime.now().isoformat(),
            }

    async def run_loop(self):
        """Main loop — run forever."""
        self.running = True
        self.state = load_state(STATE_KEY, "auto_makah")

        log.info(f"🫀 Health Loop started — checking every {CHECK_INTERVAL_SECONDS}s")

        while self.running:
            try:
                result = await self._check_once()
                self.state.total_runs += 1
                self.state.last_run = datetime.now().isoformat()

                if result["healthy"]:
                    self.consecutive_failures = 0
                    self.state.successful_runs += 1
                    self.state.last_success = datetime.now().isoformat()
                    self.state.last_error = None
                    self.last_healthy = datetime.now().isoformat()
                    log.debug(f"✅ Health OK — v{result['version']} — {result['agents']} agents")
                else:
                    self.consecutive_failures += 1
                    self.state.failed_runs += 1
                    self.state.last_error = result.get("error", "unknown")
                    
                    # Alert if sustained failure
                    if self.consecutive_failures >= 3:
                        log.error(f"🔴 HEALTH ALERT: {self.consecutive_failures} consecutive failures!")
                        self._record_alert(result)
                    
                    log.warning(f"⚠️ Health check failed (#{self.consecutive_failures}): {self.state.last_error[:100]}")

                save_state(self.state)

            except Exception as e:
                log.error(f"Health loop internal error: {e}")

            # Wait for next check
            await asyncio.sleep(CHECK_INTERVAL_SECONDS)

    def _record_alert(self, result: dict):
        """Record an alert in the learnings."""
        alert = f"🔴 {result['timestamp']}: Health {result.get('status','error')} — {result.get('error','')[:80]}"
        self.state.learnings.append(alert)
        self.state.learnings = self.state.learnings[-50:]  # Keep last 50

    def start(self):
        """Start the health loop in background."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.create_task(self.run_loop())
        log.info("🫀 Health Loop background task created")


# ═══ Standalone runner ═══
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    hl = HealthLoop()
    asyncio.run(hl.run_loop())
