import sys, os
sys.path.insert(0, r'C:\Users\saifr\.openclaw-autoclaw\workspace\auto_makah')

errors = []

modules = [
    ('core.agent', 'AgentRuntime'),
    ('core.tools', 'ToolRegistry'),
    ('db.schema', 'Base'),
    ('knowledge.base', 'KnowledgeEntry'),
    ('knowledge.search', 'KnowledgeSearch'),
    ('memory.store', 'MemoryStore'),
    ('memory.recall', 'ContextInjector'),
    ('agents.swarm', 'SwarmOrchestrator'),
    ('agents.experts.orchestrator', 'ExpertOrchestrator'),
    ('agents.experts.profiles', 'EXPERT_PROFILES'),
    ('api.app', 'app'),
]

for mod_name, cls in modules:
    try:
        mod = __import__(mod_name, fromlist=[cls])
        getattr(mod, cls)
        print(f'  OK  {mod_name}')
    except Exception as e:
        print(f'  FAIL  {mod_name}: {e}')
        errors.append(mod_name)

print()
if errors:
    print(f'FAILED: {len(errors)} modules')
else:
    print('ALL 11 MODULES IMPORT SUCCESSFULLY')

root = r'C:\Users\saifr\.openclaw-autoclaw\workspace\auto_makah'
count = 0
for dirpath, dirnames, filenames in os.walk(root):
    for f in filenames:
        if f.endswith('.py') and '__pycache__' not in dirpath:
            count += 1
print(f'Total Python files: {count}')
