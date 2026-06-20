import urllib.request, json

BASE = "https://auto-makah.fly.dev"
ok = 0
total = 0

def check(label, url, expect=200):
    global ok, total
    total += 1
    try:
        r = urllib.request.urlopen(url, timeout=15)
        if r.status == expect:
            print(f"  OK  {label}")
            ok += 1
        else:
            print(f"  FAIL  {label} — expected {expect}, got {r.status}")
    except Exception as e:
        print(f"  FAIL  {label} — {e}")

print("=== Auto Makah Smoke Tests ===\n")

check("Health API", f"{BASE}/api/health")
check("Dashboard HTML", f"{BASE}/")
check("Factory Templates", f"{BASE}/api/factory/templates")
check("Factory Status", f"{BASE}/api/factory/status")
check("Agents List", f"{BASE}/api/agents")
check("Tools List", f"{BASE}/api/tools")

# Verify template data
r = urllib.request.urlopen(f"{BASE}/api/factory/templates", timeout=15)
templates = json.loads(r.read())
total += 1
if len(templates) == 5:
    print(f"  OK  Templates count: 5")
    ok += 1
else:
    print(f"  FAIL  Templates count: {len(templates)}")

# Check each template name
for t in templates:
    total += 1
    if "name" in t and "domain" in t:
        print(f"  OK  Template: {t['name']}")
        ok += 1
    else:
        print(f"  FAIL  Template missing fields: {t}")
        break

print(f"\n=== {ok}/{total} passed ===")
if ok == total:
    print("ALL TESTS PASSED")
