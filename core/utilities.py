"""
Utility Agents — don't need AI, always work
"""
import math, json, base64, io, qrcode

# ═══ Islamic Calculator ═══

ZAKAT_NISAB_GOLD_GRAMS = 85  # 85 grams of gold
ZAKAT_NISAB_SILVER_GRAMS = 595  # 595 grams of silver
ZAKAT_RATE = 0.025  # 2.5%

def zakat_calculator(wealth: float, gold_price_per_gram: float, debts: float = 0) -> dict:
    """Calculate Zakat on wealth."""
    net_wealth = wealth - debts
    nisab = ZAKAT_NISAB_GOLD_GRAMS * gold_price_per_gram
    if net_wealth < nisab:
        return {
            "wealth": wealth,
            "debts": debts,
            "net_wealth": net_wealth,
            "nisab": round(nisab, 2),
            "nisab_grams": ZAKAT_NISAB_GOLD_GRAMS,
            "gold_price": gold_price_per_gram,
            "zakat_due": 0,
            "zakat_rate": f"{ZAKAT_RATE*100}%",
            "verdict": "لا تجب عليك الزكاة — لم يبلغ النصاب",
        }
    zakat = net_wealth * ZAKAT_RATE
    return {
        "wealth": wealth,
        "debts": debts,
        "net_wealth": net_wealth,
        "nisab": round(nisab, 2),
        "nisab_grams": ZAKAT_NISAB_GOLD_GRAMS,
        "gold_price": gold_price_per_gram,
        "zakat_due": round(zakat, 2),
        "zakat_rate": f"{ZAKAT_RATE*100}%",
        "verdict": f"تجب عليك الزكاة — المبلغ: {round(zakat, 2)}",
    }

# Inheritance shares per Islamic law
INHERITANCE_SHARES = {
    "زوج": 0.25,  # with children
    "زوج_بدون_أبناء": 0.5,
    "زوجة": 0.125,  # with children
    "زوجة_بدون_أبناء": 0.25,
    "بنت": 0.5,  # alone
    "بنتان": 2/3,  # shared
    "أم": 1/3,  # no children
    "أم_مع_أبناء": 1/6,
    "أب": 1/6,  # with children
}

def inheritance_calculator(total: float, heirs: list) -> dict:
    """Calculate Islamic inheritance shares."""
    results = []
    remaining = total
    for h in heirs:
        share_key = h.get("type", "")
        custom_share = h.get("share", 0)
        if custom_share > 0:
            amount = total * custom_share
        else:
            rate = INHERITANCE_SHARES.get(share_key, 0)
            amount = total * rate
        results.append({"heir": h.get("name", ""), "type": share_key, "share": amount})
        remaining -= amount
    return {"total": total, "heirs": results, "remaining": round(remaining, 2), "note": "استشر عالماً شرعياً للتأكد"}

# ═══ Currency & Units ═══

# Approximate rates (would use real API in production)
CURRENCY_RATES = {
    "SAR": 1.0, "USD": 0.2667, "EUR": 0.244, "GBP": 0.209,
    "AED": 0.979, "KWD": 0.082, "EGP": 12.77, "TRY": 8.75,
}

def currency_convert(amount: float, from_cur: str, to_cur: str) -> dict:
    """Convert between currencies."""
    from_rate = CURRENCY_RATES.get(from_cur.upper(), 1)
    to_rate = CURRENCY_RATES.get(to_cur.upper(), 1)
    result = amount * (to_rate / from_rate)
    return {
        "amount": amount, "from": from_cur.upper(), "to": to_cur.upper(),
        "result": round(result, 4), "rate": round(to_rate / from_rate, 6),
    }

UNIT_CONVERSIONS = {
    "km_to_miles": 0.621371, "miles_to_km": 1.60934,
    "kg_to_lbs": 2.20462, "lbs_to_kg": 0.453592,
    "celsius_to_fahrenheit": lambda c: c * 9/5 + 32,
    "fahrenheit_to_celsius": lambda f: (f - 32) * 5/9,
    "liters_to_gallons": 0.264172, "gallons_to_liters": 3.78541,
}

def unit_convert(value: float, conversion: str) -> dict:
    """Convert units."""
    conv = UNIT_CONVERSIONS.get(conversion)
    if conv is None:
        return {"error": f"Unknown conversion: {conversion}"}
    if callable(conv):
        result = conv(value)
    else:
        result = value * conv
    return {"value": value, "conversion": conversion, "result": round(result, 4)}

# ═══ QR Generator ═══

def generate_qr(data: str, size: int = 10) -> dict:
    """Generate QR code as base64 data URL."""
    qr = qrcode.QRCode(version=1, box_size=size, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return {"data": data, "qr_base64": f"data:image/png;base64,{b64}"}

# ═══ Password Generator ═══

import secrets, string

def generate_password(length: int = 16, include_symbols: bool = True) -> dict:
    """Generate secure password."""
    chars = string.ascii_letters + string.digits
    if include_symbols: chars += "!@#$%^&*"
    pw = ''.join(secrets.choice(chars) for _ in range(length))
    strength = "قوية" if length >= 14 and include_symbols else "متوسطة" if length >= 10 else "ضعيفة"
    return {"password": pw, "length": length, "strength": strength}
