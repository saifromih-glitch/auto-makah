# ═══════════════════════════════════════════════════════
# 📚 Skill Loader — Lopp Step 7: Reusable Knowledge Files
# Loads .skill files from skills/ directory
# ═══════════════════════════════════════════════════════

import os, logging

log = logging.getLogger("skill_loader")

SKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "skills")

def load_skill(name: str) -> str | None:
    """Load a skill file by name (without .skill extension)."""
    path = os.path.join(SKILLS_DIR, f"{name}.skill")
    if not os.path.isfile(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        # Strip comments
        lines = [l for l in content.split('\n') if not l.strip().startswith('#')]
        return '\n'.join(lines)

def list_skills() -> list:
    """List all available skills."""
    skills = []
    if not os.path.isdir(SKILLS_DIR):
        return skills
    for f in os.listdir(SKILLS_DIR):
        if f.endswith('.skill'):
            name = f.replace('.skill', '')
            path = os.path.join(SKILLS_DIR, f)
            with open(path, 'r', encoding='utf-8') as fh:
                first_line = fh.readline().strip('# \n')
            skills.append({"name": name, "title": first_line})
    return skills

def inject_skill(system_prompt: str, skill_name: str) -> str:
    """Inject a skill into a system prompt."""
    skill = load_skill(skill_name)
    if not skill:
        return system_prompt
    return system_prompt + "\n\n" + skill

def inject_best_skill(system_prompt: str, question: str) -> str:
    """Auto-detect and inject the best skill for the question."""
    mapping = {
        "strategy": ["استراتيج", "خطة", "رؤية", "توسع", "منافس", "هدف", "مشروع", "فكرة"],
        "finance": ["مال", "تكلفة", "ربح", "استثمار", "تمويل", "سعر", "ميزانية", "عائد"],
        "operations": ["عمليات", "انتاج", "جودة", "كفاءة", "سلسلة", "مخزون", "لوجستي"],
    }
    
    question_lower = question.lower()
    for skill_name, keywords in mapping.items():
        if any(kw in question_lower for kw in keywords):
            result = inject_skill(system_prompt, skill_name)
            log.info(f"Injected skill: {skill_name}")
            return result
    
    return system_prompt
