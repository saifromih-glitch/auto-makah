"""
Global Features — API Keys, Streaming, Multi-language, Embed Widget
"""
import os, json, secrets, hashlib, time, asyncio
from fastapi.responses import StreamingResponse

# ═══ API Key System ═══

# In-memory store (would use DB in production)
_api_keys = {}  # key → {name, created, calls}

def generate_api_key(name: str = "default") -> dict:
    """Generate a unique API key."""
    key = "am-" + secrets.token_hex(24)  # am- prefix for Auto Makah
    _api_keys[key] = {"name": name, "created": time.time(), "calls": 0}
    return {"key": key, "name": name, "prefix": key[:10] + "..."}

def validate_api_key(key: str) -> bool:
    """Check if API key is valid."""
    if key in _api_keys:
        _api_keys[key]["calls"] += 1
        return True
    return False

def list_api_keys() -> list:
    """List all API keys (without revealing full key)."""
    return [{"name": v["name"], "prefix": k[:10]+"...", "calls": v["calls"], "created": v["created"]} for k, v in _api_keys.items()]

# ═══ Real-time Streaming ═══

async def stream_ai_response(prompt: str, system: str = ""):
    """Stream AI response as Server-Sent Events."""
    import httpx
    ZENMUX_URL = "https://zenmux.ai/api/v1/chat/completions"
    ZENMUX_KEY = os.getenv("ZENMUX_API_KEY", "")
    if not ZENMUX_KEY:
        yield "data: {\"error\": \"No API key configured\"}\n\n"
        return
    msgs = []
    if system: msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    try:
        async with httpx.AsyncClient(timeout=120) as c:
            r = await c.post(ZENMUX_URL, headers={
                "Authorization": f"Bearer {ZENMUX_KEY}", "Content-Type": "application/json",
            }, json={"model": "z-ai/glm-5.2-free", "messages": msgs, "max_tokens": 3000, "temperature": 0.5, "stream": True})
            buffer = ""
            async for chunk in r.aiter_bytes():
                buffer += chunk.decode()
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.startswith("data: "):
                        yield f"{line}\n\n"
    except Exception as e:
        yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"

# ═══ Embed Widget Generator ═══

def generate_embed_script(agent_endpoint: str, theme: str = "dark") -> str:
    """Generate JavaScript embed code for any agent."""
    return f"""<!-- Auto Makah Widget -->
<div id="auto-makah-widget"></div>
<script>
(function(){{
  var d=document.getElementById('auto-makah-widget');
  d.innerHTML='<div style="background:{'#1a1a2e' if theme=='dark' else '#fff'};border:1px solid #d4a017;border-radius:12px;padding:24px;max-width:600px;font-family:system-ui;direction:rtl">'+
    '<h3 style="color:#d4a017;margin-bottom:12px">🕋 Auto Makah</h3>'+
    '<textarea id="am-input" style="width:100%;height:80px;background:rgba(30,42,53,.5);border:1px solid rgba(30,42,53,.8);color:#e8e4db;border-radius:8px;padding:12px;font-family:inherit" placeholder="اكتب سؤالك..."></textarea>'+
    '<button id="am-btn" style="margin-top:8px;background:linear-gradient(135deg,#d4a017,#b8860b);color:#0a0f14;border:none;padding:10px 24px;border-radius:8px;cursor:pointer;font-weight:600" onclick="runAM()">▶ تشغيل</button>'+
    '<div id="am-result" style="margin-top:16px;padding:16px;background:rgba(30,42,53,.5);border-radius:8px;display:none;white-space:pre-wrap;max-height:300px;overflow-y:auto;line-height:1.8;font-size:14px"></div>'+
    '</div>';
  window.runAM=async function(){{
    var b=document.getElementById('am-btn'),r=document.getElementById('am-result'),i=document.getElementById('am-input');
    b.disabled=true;b.textContent='⏳...';r.style.display='block';r.textContent='';
    try{{
      var resp=await fetch('https://auto-makah.fly.dev{agent_endpoint}',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{input:i.value}})}});
      var data=await resp.json();
      r.textContent=data.analysis||data.result||JSON.stringify(data,null,2);
    }}catch(e){{r.textContent='Error: '+e.message}}
    b.disabled=false;b.textContent='▶ تشغيل';
  }};
}})();
</script>"""

# ═══ Platform Stats ═══

def platform_stats() -> dict:
    """Get platform statistics."""
    return {
        "name": "Auto Makah",
        "version": "2.0.0",
        "agents": 36,
        "pipelines": 4,
        "api_endpoints": 50,
        "deployment": "Fly.io — Amsterdam",
        "machines": 2,
        "uptime": "99.9%",
        "languages": ["العربية", "English"],
        "api_keys_active": len(_api_keys),
        "features": [
            "Multi-Agent Pipelines",
            "Real-time Streaming",
            "Web Search Integration",
            "Document Export (MD/HTML/PDF)",
            "API Key Authentication",
            "Embeddable Widgets",
            "Arabic-First AI",
            "Islamic Tools (Zakat/Inheritance)",
        ]
    }

# Initialize a demo key on module load
if not _api_keys:
    generate_api_key("demo")
