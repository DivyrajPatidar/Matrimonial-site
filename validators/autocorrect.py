"""Auto-correct user-typed Nakshatra and Rashi spellings to canonical display names.

Accepts:
  - Numbers 1-27 (Nakshatra) or 1-12 (Rashi)
  - Common spelling variants (lowercase)
  - The full canonical value with Telugu, e.g. 'Rohini (రోహిణి)'
  - Just the English part, e.g. 'Rohini', 'rohini', 'ROHINI'
  - Telugu only, e.g. 'రోహిణి'
"""
from config.constants import NAKSHATRA_LIST, RASHI_LIST
import re


# Map of lowercase aliases -> canonical display value
NAKSHATRA_MAP = {
    "ashwini": "Ashwini (అశ్విని)", "aswini": "Ashwini (అశ్విని)", "asvini": "Ashwini (అశ్విని)",
    "bharani": "Bharani (భరణి)", "barani": "Bharani (భరణి)",
    "krittika": "Krittika (కృతిక)", "kritika": "Krittika (కృతిక)", "karthika": "Krittika (కృతిక)",
    "rohini": "Rohini (రోహిణి)", "rohin": "Rohini (రోహిణి)",
    "mrigashira": "Mrigashira (మృగశిర)", "mrigasira": "Mrigashira (మృగశిర)", "mrigashiram": "Mrigashira (మృగశిర)",
    "ardra": "Ardra (ఆర్ద్ర)", "arudra": "Ardra (ఆర్ద్ర)",
    "punarvasu": "Punarvasu (పునర్వసు)", "punarvas": "Punarvasu (పునర్వసు)",
    "pushya": "Pushya (పుష్యమి)", "pushyami": "Pushya (పుష్యమి)", "poosam": "Pushya (పుష్యమి)",
    "ashlesha": "Ashlesha (ఆశ్లేష)", "aslesha": "Ashlesha (ఆశ్లేష)", "ayilyam": "Ashlesha (ఆశ్లేష)",
    "magha": "Magha (మఘ)", "makha": "Magha (మఘ)", "magam": "Magha (మఘ)",
    "purva phalguni": "Purva Phalguni (పూర్వ ఫల్గుణి)",
    "poorva phalguni": "Purva Phalguni (పూర్వ ఫల్గుణి)",
    "pubba": "Purva Phalguni (పూర్వ ఫల్గుణి)",
    "uttara phalguni": "Uttara Phalguni (ఉత్తర ఫల్గుణి)",
    "uttaraphalguni": "Uttara Phalguni (ఉత్తర ఫల్గుణి)",
    "uttaram": "Uttara Phalguni (ఉత్తర ఫల్గుణి)",
    "hasta": "Hasta (హస్త)", "hastam": "Hasta (హస్త)", "hastha": "Hasta (హస్త)",
    "chitra": "Chitra (చిత్ర)", "chitta": "Chitra (చిత్ర)", "chitrai": "Chitra (చిత్ర)",
    "swati": "Swati (స్వాతి)", "swathi": "Swati (స్వాతి)", "chothi": "Swati (స్వాతి)",
    "vishakha": "Vishakha (విశాఖ)", "visakha": "Vishakha (విశాఖ)", "vishaka": "Vishakha (విశాఖ)",
    "anuradha": "Anuradha (అనూరాధ)", "anusham": "Anuradha (అనూరాధ)",
    "jyeshta": "Jyeshta (జ్యేష్ఠ)", "jyeshtha": "Jyeshta (జ్యేష్ఠ)",
    "jyesta": "Jyeshta (జ్యేష్ఠ)", "kettai": "Jyeshta (జ్యేష్ఠ)",
    "moola": "Moola (మూల)", "mula": "Moola (మూల)", "moolam": "Moola (మూల)",
    "purvashada": "Purvashada (పూర్వాషాఢ)", "purva ashadha": "Purvashada (పూర్వాషాఢ)",
    "pooradam": "Purvashada (పూర్వాషాఢ)",
    "uttarashada": "Uttarashada (ఉత్తరాషాఢ)", "uttara ashadha": "Uttarashada (ఉత్తరాషాఢ)",
    "uthradam": "Uttarashada (ఉత్తరాషాఢ)",
    "shravana": "Shravana (శ్రవణ)", "shravan": "Shravana (శ్రవణ)",
    "thiruvonam": "Shravana (శ్రవణ)", "shravanam": "Shravana (శ్రవణ)",
    "dhanishta": "Dhanishta (ధనిష్ఠ)", "dhanishtha": "Dhanishta (ధనిష్ఠ)",
    "avittam": "Dhanishta (ధనిష్ఠ)",
    "shatabhisha": "Shatabhisha (శతభిష)", "shatabhishak": "Shatabhisha (శతభిష)",
    "sadayam": "Shatabhisha (శతభిష)", "satabhisha": "Shatabhisha (శతభిష)",
    "purvabhadra": "Purvabhadra (పూర్వభాద్ర)", "purva bhadra": "Purvabhadra (పూర్వభాద్ర)",
    "poorattathi": "Purvabhadra (పూర్వభాద్ర)",
    "uttarabhadra": "Uttarabhadra (ఉత్తరభాద్ర)", "uttara bhadra": "Uttarabhadra (ఉత్తరభాద్ర)",
    "uthratathi": "Uttarabhadra (ఉత్తరభాద్ర)",
    "revati": "Revati (రేవతి)", "revathi": "Revati (రేవతి)", "revathy": "Revati (రేవతి)",
}

RASHI_MAP = {
    "mesha": "Mesha (మేషం)", "mesham": "Mesha (మేషం)", "aries": "Mesha (మేషం)",
    "vrishabha": "Vrishabha (వృషభం)", "vrushabha": "Vrishabha (వృషభం)",
    "rishabam": "Vrishabha (వృషభం)", "taurus": "Vrishabha (వృషభం)",
    "vrishabham": "Vrishabha (వృషభం)",
    "mithuna": "Mithuna (మిథునం)", "mithunam": "Mithuna (మిథునం)", "gemini": "Mithuna (మిథునం)",
    "karka": "Karka (కర్కాటకం)", "karkatakam": "Karka (కర్కాటకం)", "cancer": "Karka (కర్కాటకం)",
    "simha": "Simha (సింహం)", "simham": "Simha (సింహం)", "leo": "Simha (సింహం)",
    "kanya": "Kanya (కన్యా)", "virgo": "Kanya (కన్యా)",
    "tula": "Tula (తుల)", "thulam": "Tula (తుల)", "libra": "Tula (తుల)",
    "vrischika": "Vrischika (వృశ్చికం)", "vrishchika": "Vrischika (వృశ్చికం)",
    "vrischikam": "Vrischika (వృశ్చికం)", "scorpio": "Vrischika (వృశ్చికం)",
    "dhanu": "Dhanu (ధనస్సు)", "dhanassu": "Dhanu (ధనస్సు)", "sagittarius": "Dhanu (ధనస్సు)",
    "makara": "Makara (మకరం)", "makaram": "Makara (మకరం)", "capricorn": "Makara (మకరం)",
    "kumbha": "Kumbha (కుంభం)", "kumbham": "Kumbha (కుంభం)", "aquarius": "Kumbha (కుంభం)",
    "meena": "Meena (మీనం)", "meenam": "Meena (మీనం)", "pisces": "Meena (మీనం)",
}


def _strip_to_english_part(text: str) -> str:
    """If user pasted something like 'Rohini (రోహిణి)', return just 'rohini'.
    Removes anything inside parentheses, trims whitespace, lowercases."""
    # Remove anything in parentheses (including the parens themselves)
    cleaned = re.sub(r"\([^)]*\)", "", text)
    return cleaned.strip().lower()


def autocorrect_nakshatra(user_value: str) -> str | None:
    if not user_value:
        return None
    raw = str(user_value).strip()
    # Number 1-27
    if raw.isdigit():
        idx = int(raw) - 1
        if 0 <= idx < len(NAKSHATRA_LIST):
            return NAKSHATRA_LIST[idx]
        return None
    # Exact match against full canonical list (handles paste of "Rohini (రోహిణి)")
    for canonical in NAKSHATRA_LIST:
        if raw == canonical:
            return canonical
    # Strip parentheses content -> compare to map / list
    stripped = _strip_to_english_part(raw)
    if not stripped:
        # Maybe user typed only Telugu - search by Telugu substring
        for canonical in NAKSHATRA_LIST:
            telugu = canonical.split("(")[-1].rstrip(")").strip()
            if raw == telugu:
                return canonical
        return None
    # Direct alias map
    if stripped in NAKSHATRA_MAP:
        return NAKSHATRA_MAP[stripped]
    # Fuzzy: match against English part of canonical list
    for canonical in NAKSHATRA_LIST:
        english = canonical.split("(")[0].strip().lower()
        if stripped == english:
            return canonical
    # Last resort: substring match (in either direction)
    for canonical in NAKSHATRA_LIST:
        english = canonical.split("(")[0].strip().lower()
        if stripped in english or english in stripped:
            return canonical
    return None


def autocorrect_rashi(user_value: str) -> str | None:
    if not user_value:
        return None
    raw = str(user_value).strip()
    if raw.isdigit():
        idx = int(raw) - 1
        if 0 <= idx < len(RASHI_LIST):
            return RASHI_LIST[idx]
        return None
    for canonical in RASHI_LIST:
        if raw == canonical:
            return canonical
    stripped = _strip_to_english_part(raw)
    if not stripped:
        for canonical in RASHI_LIST:
            telugu = canonical.split("(")[-1].rstrip(")").strip()
            if raw == telugu:
                return canonical
        return None
    if stripped in RASHI_MAP:
        return RASHI_MAP[stripped]
    for canonical in RASHI_LIST:
        english = canonical.split("(")[0].strip().lower()
        if stripped == english:
            return canonical
    for canonical in RASHI_LIST:
        english = canonical.split("(")[0].strip().lower()
        if stripped in english or english in stripped:
            return canonical
    return None