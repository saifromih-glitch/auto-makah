# 🕋 Auto Makah — Expert Training Pipeline

from typing import Dict, Any, List
from knowledge.base import knowledge_base, KnowledgeEntry
from knowledge.domains.accounting import ACCOUNTING_PROMPT
from knowledge.domains.marketing import MARKETING_PROMPT
from knowledge.domains.legal import LEGAL_PROMPT
from knowledge.domains.engineering import ENGINEERING_PROMPT


def seed_knowledge_base():
    """Seed knowledge base with comprehensive domain entries."""

    # ─── Accounting ───
    entries = [
        KnowledgeEntry("accounting", "زكاة الشركات السعودية",
            "الزكاة = 2.5% × (الأصول الزكوية - الخصوم الزكوية). "
            "الأصول الزكوية: النقدية + الذمم المدينة + المخزون + الاستثمارات. "
            "الخصوم الزكوية: الذمم الدائنة + القروض قصيرة الأجل. "
            "لا تحسب الزكاة على الأصول الثابتة. الإقرار الزكوي خلال ١٢٠ يوم من نهاية السنة المالية.",
            ["زكاة", "ZATCA", "هيئة الزكاة"]),
        KnowledgeEntry("accounting", "VAT السعودي",
            "ضريبة القيمة المضافة 15%. ضريبة المخرجات - ضريبة المدخلات. "
            "الإقرار ربع سنوي. حد التسجيل الإلزامي 375,000 ريال.",
            ["VAT", "ضريبة", "قيمة مضافة"]),
        KnowledgeEntry("accounting", "النسب المالية الأساسية",
            "السيولة = الأصول المتداولة/الخصوم المتداولة. الربحية = صافي الربح/الإيرادات. "
            "ROA = صافي الربح/إجمالي الأصول. ROE = صافي الربح/حقوق الملكية. "
            "نقطة التعادل = التكاليف الثابتة/(1 - التكاليف المتغيرة/الإيراد).",
            ["نسب", "تحليل", "مالية"]),
        KnowledgeEntry("accounting", "IFRS 15 — الإيراد من العقود",
            "٥ خطوات: 1. تحديد العقد 2. تحديد التزامات الأداء 3. تحديد سعر المعاملة "
            "4. توزيع السعر 5. الاعتراف بالإيراد عند الوفاء بالالتزام.",
            ["IFRS", "إيراد", "عقود"]),
        KnowledgeEntry("accounting", "IAS 16 — الممتلكات والمعدات",
            "التكلفة - الإهلاك المتراكم - خسارة الانخفاض. الإهلاك بطريقة القسط الثابت "
            "أو المتناقص. العمر الإنتاجي التقديري. القيمة المتبقية.",
            ["IAS", "أصول", "إهلاك"]),
    ]

    # ─── Legal ───
    entries += [
        KnowledgeEntry("legal", "نظام العمل — ساعات العمل والإجازات",
            "ساعات العمل: ٨ ساعات/يوم — ٤٨/أسبوع. رمضان: ٦/يوم — ٣٦/أسبوع. "
            "الإجازة السنوية: ٢١ يوم — ٣٠ بعد ٥ سنوات. "
            "مكافأة نهاية الخدمة: نصف شهر عن أول ٥ سنوات — شهر بعدها.",
            ["عمل", "ساعات", "إجازة", "نهاية خدمة"]),
        KnowledgeEntry("legal", "نظام التأمينات الاجتماعية GOSI",
            "الاشتراك: ٢١.٥٪ للسعودي (صاحب العمل ١١.٥٪ + الموظف ١٠٪). "
            "غير السعودي: ٢٪ أخطار مهنية فقط. "
            "ساند: ١.٥٪ للتعطل عن العمل.",
            ["تأمينات", "GOSI", "ساند"]),
        KnowledgeEntry("legal", "نظام الشركات السعودي",
            "شركة ذات مسؤولية محدودة (LLC): الأكثر شيوعاً. شركة مساهمة: للشركات الكبيرة. "
            "عقد التأسيس إلزامي — السجل التجاري من وزارة التجارة.",
            ["شركات", "LLC", "تأسيس"]),
        KnowledgeEntry("legal", "نظام المنافسة",
            "منع الاحتكار — حماية المنافسة العادلة. "
            "يحظر الاتفاقيات التي تحد من المنافسة. المجلس الأعلى للمنافسة.",
            ["منافسة", "احتكار", "تجاري"]),
        KnowledgeEntry("legal", "نطاقات — التوطين",
            "برنامج تحفيز توطين الوظائف. تصنيف: ممتاز — أخضر — أصفر — أحمر. "
            "حسب نسبة السعوديين وحجم المنشأة وقطاعها.",
            ["نطاقات", "توطين", "سعودة"]),
    ]

    # ─── Marketing ───
    entries += [
        KnowledgeEntry("marketing", "GSTIC Framework كامل",
            "Goals: SMART محدد بزمن. Strategy: Positioning + Differentiation. "
            "Tactics: 7Ps. Implementation: جدول + مسؤوليات + ميزانية. "
            "Control: KPIs رقمية — CAC — LTV — Churn — ROI.",
            ["GSTIC", "إطار", "استراتيجية"]),
        KnowledgeEntry("marketing", "AARRR Pirate Metrics",
            "Acquisition → Activation → Retention → Revenue → Referral. "
            "كل مرحلة = KPIs محددة. ركز على المرحلة الأضعف أولاً.",
            ["AARRR", "نمو", "قمع"]),
        KnowledgeEntry("marketing", "تسويق B2B السعودي",
            "LinkedIn: محتوى مهني. Google My Business: ظهور محلي. "
            "WhatsApp Business: تواصل مباشر. المعارض التجارية. الشراكات.",
            ["B2B", "سعودي", "قنوات"]),
        KnowledgeEntry("marketing", "تحليل SWOT",
            "Strengths — Weaknesses — Opportunities — Threats. "
            "داخلي (SW) + خارجي (OT). استخدمه قبل أي خطة استراتيجية.",
            ["SWOT", "تحليل", "منافسة"]),
    ]

    # ─── Engineering ───
    entries += [
        KnowledgeEntry("engineering", "إدارة الورش — FIFO",
            "استقبال ← تشخيص ← إصلاح ← تسليم. نظام FIFO: الأولوية للأقدم. "
            "معدل دوران العمل = السيارات المنجزة/الفترة. كفاءة الفنيين = ساعات فعلية/متاحة.",
            ["ورشة", "FIFO", "إدارة"]),
        KnowledgeEntry("engineering", "الأنظمة الهيدروليكية — مبدأ باسكال",
            "P = F/A — الضغط ينتقل بالتساوي. المضخات: gear — vane — piston. "
            "الصمامات: directional — pressure — flow control. أعطال: تسريب — سخونة — ضوضاء.",
            ["هيدروليك", "باسكال", "مضخات"]),
        KnowledgeEntry("engineering", "تحليل التكلفة في التصنيع",
            "تكلفة ساعة العمل = المصروفات/(عدد الفنيين × الساعات). "
            "نقطة التعادل. هامش الربح = Cost + Markup. "
            "ROI — Payback Period.",
            ["تكلفة", "تصنيع", "تعادل"]),
    ]

    for entry in entries:
        knowledge_base.add(entry)

    return knowledge_base.stats()


def train_expert_prompt(domain: str) -> str:
    """Generate a trained expert prompt with domain knowledge injected."""

    prompts = {
        "accounting": ACCOUNTING_PROMPT,
        "marketing": MARKETING_PROMPT,
        "legal": LEGAL_PROMPT,
        "engineering": ENGINEERING_PROMPT,
    }

    base = prompts.get(domain, "")
    entries = knowledge_base.get_by_domain(domain)

    if entries:
        base += "\n\n📚 المعرفة المخزنة:\n"
        for e in entries[:5]:
            base += f"\n[{e.title}]\n{e.content[:500]}\n"

    return base
