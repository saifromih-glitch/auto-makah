# ═══════════════════════════════════════════════════════
# 📚 Skill Loader — Lopp Step 7: Reusable Knowledge Files
# v2.0: SKILL.md format (NarratorAI-compatible)
# Supports: .skill (legacy) + SKILL.md + references/
# ═══════════════════════════════════════════════════════

import os, re, logging

log = logging.getLogger("skill_loader")

SKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "skills")


def _parse_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from SKILL.md."""
    meta = {}
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            yaml_lines = parts[1].strip().split('\n')
            for line in yaml_lines:
                line = line.strip()
                if ':' in line:
                    k, v = line.split(':', 1)
                    k = k.strip()
                    v = v.strip()
                    # Convert lists
                    if v.startswith('[') and v.endswith(']'):
                        v = [x.strip() for x in v[1:-1].split(',') if x.strip()]
                    meta[k] = v
    return meta


def load_skill(name: str) -> dict | None:
    """
    Load a skill by name. Returns {content, meta, references, name}.
    Supports: name.skill (legacy), name/SKILL.md (v2.0)
    """
    # Try v2.0 SKILL.md first (case-insensitive for Docker compatibility)
    v2_path = None
    for candidate in [os.path.join(SKILLS_DIR, name, "SKILL.md"), 
                      os.path.join(SKILLS_DIR, name, "skill.md")]:
        if os.path.isfile(candidate):
            v2_path = candidate
            break
    
    if v2_path:
        with open(v2_path, 'r', encoding='utf-8') as f:
            raw = f.read()
        meta = _parse_frontmatter(raw)
        # Strip frontmatter for content
        content = raw
        if raw.startswith('---'):
            parts = raw.split('---', 2)
            content = parts[2].strip() if len(parts) >= 3 else raw
        # Load references
        refs = {}
        refs_dir = os.path.join(SKILLS_DIR, name, "references")
        if os.path.isdir(refs_dir):
            for fn in os.listdir(refs_dir):
                if fn.endswith('.md'):
                    with open(os.path.join(refs_dir, fn), 'r', encoding='utf-8') as rf:
                        refs[fn] = rf.read()
        return {
            "name": name,
            "display": meta.get("display", name),
            "methodology": meta.get("methodology", ""),
            "version": meta.get("version", "1.0.0"),
            "content": content,
            "meta": meta,
            "references": refs,
            "format": "v2.0",
        }

    # Fallback to legacy .skill
    legacy_path = os.path.join(SKILLS_DIR, f"{name}.skill")
    if os.path.isfile(legacy_path):
        with open(legacy_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        lines = [l for l in content.split('\n') if not l.strip().startswith('#')]
        return {
            "name": name,
            "display": name,
            "methodology": "",
            "version": "1.0.0",
            "content": '\n'.join(lines),
            "meta": {},
            "references": {},
            "format": "legacy",
        }

    return None


def list_skills() -> list:
    """List all available skills (v2.0 + legacy)."""
    skills = []
    if not os.path.isdir(SKILLS_DIR):
        return skills

    seen = set()
    # v2.0 SKILL.md directories (case-insensitive)
    for name in os.listdir(SKILLS_DIR):
        skill_path = os.path.join(SKILLS_DIR, name)
        if os.path.isdir(skill_path) and (
            os.path.isfile(os.path.join(skill_path, "SKILL.md")) or
            os.path.isfile(os.path.join(skill_path, "skill.md"))
        ):
            s = load_skill(name)
            if s:
                skills.append({
                    "name": s["name"],
                    "display": s["display"],
                    "methodology": s["methodology"],
                    "version": s["version"],
                    "format": s["format"],
                    "has_references": len(s.get("references", {})) > 0,
                })
                seen.add(name)

    # Legacy .skill files
    for f in os.listdir(SKILLS_DIR):
        if f.endswith('.skill') and f.replace('.skill', '') not in seen:
            name = f.replace('.skill', '')
            s = load_skill(name)
            if s:
                skills.append({
                    "name": s["name"],
                    "display": s["display"],
                    "version": s["version"],
                    "format": s["format"],
                    "has_references": False,
                })

    return skills


def inject_skill(system_prompt: str, skill_name: str) -> str:
    """Inject a skill into a system prompt (using SKILL.md content + key references)."""
    skill = load_skill(skill_name)
    if not skill:
        return system_prompt

    injection = f"\n\n---\n## {skill['display']} (v{skill['version']})\n"
    injection += f"المنهجية: {skill['methodology']}\n\n"

    # Inject agent rules section
    rules_match = re.search(r'## 🤖 Agent Rules.*?(?=##|\Z)', skill['content'], re.DOTALL)
    if rules_match:
        injection += rules_match.group(0).strip() + "\n"

    # Inject core concepts section
    concepts_match = re.search(r'## 🧠 Core Concepts.*?(?=##|\Z)', skill['content'], re.DOTALL)
    if concepts_match:
        injection += "\n" + concepts_match.group(0).strip() + "\n"

    return system_prompt + injection


def inject_best_skill(system_prompt: str, question: str) -> str:
    """Auto-detect and inject the best skill for the question."""
    mapping = {
        "strategy": ["استراتيج", "خطة", "رؤية", "توسع", "منافس", "هدف", "مشروع", "فكرة", "رؤية 2030"],
        "finance": ["مال", "تكلفة", "ربح", "استثمار", "تمويل", "سعر", "ميزانية", "عائد", "زكاة", "ضريبة"],
        "operations": ["عمليات", "انتاج", "جودة", "كفاءة", "سلسلة", "مخزون", "لوجستي", "عنق الزجاجة"],
    }

    question_lower = question.lower()
    for skill_name, keywords in mapping.items():
        if any(kw in question_lower for kw in keywords):
            result = inject_skill(system_prompt, skill_name)
            log.info(f"Injected skill [v2.0]: {skill_name}")
            return result

    return system_prompt
