"""Field validators. Returns (is_valid, normalized_value_or_error_message)."""
import re
from datetime import datetime
from typing import Tuple


# ---------- nonsense / gibberish detection ----------

_VOWELS = set("aeiouAEIOU")

# Common real words/acronyms that look "gibberish" by consonant rules but are valid.
_KNOWN_TERMS = {
    "mbbs", "bds", "btech", "mtech", "bsc", "msc", "bcom", "mcom", "bba", "mba",
    "bca", "mca", "phd", "llb", "llm", "ca", "cs", "cma", "ias", "ips", "irs",
    "md", "ms", "be", "me", "hr", "it", "bpo", "kpo", "ngo", "cto", "ceo", "cfo",
    "ssc", "hsc", "iti", "pg", "ug", "diploma",
}


def _word_is_gibberish(word: str) -> bool:
    """Check a single word for gibberish characteristics."""
    w = "".join(c for c in word if c.isalpha())
    if len(w) < 3:
        return False  # short tokens like initials, "Mba", "CA" are fine
    if w.lower() in _KNOWN_TERMS:
        return False  # known valid acronym/qualification
    vowels = sum(1 for c in w if c in _VOWELS)
    # Real words of length>=3 almost always have a vowel
    if vowels == 0:
        return True
    # Vowel ratio too low for a pronounceable word
    ratio = vowels / len(w)
    if len(w) >= 5 and ratio < 0.25:
        return True
    # Long consonant run within the word
    run = 0; longest = 0
    for c in w.lower():
        if c not in _VOWELS:
            run += 1; longest = max(longest, run)
        else:
            run = 0
    if longest >= 4:
        return True
    return False


def _looks_like_gibberish(text: str) -> bool:
    """Flag obviously-random text. Conservative: a phrase is gibberish only if
    EVERY word in it looks like gibberish (so real multi-word answers pass)."""
    t = text.strip()
    if len(t) < 2:
        return True
    words = [w for w in re.split(r"[\s.]+", t) if w]
    if not words:
        return True
    # If every word looks like gibberish, the whole thing is gibberish
    return all(_word_is_gibberish(w) for w in words)


# ---------- refusal / non-answer detection ----------

# Phrases that mean "I won't say" / "don't know" — in English and Hinglish.
_REFUSAL_PHRASES = {
    "nhi batana", "nahi batana", "nai batana", "nhi bataunga", "nahi bataunga",
    "nhi bataungi", "nahi bataungi", "nhi btana", "nhibatana",
    "pata nahi", "pata nhi", "pta nahi", "pta nhi", "nahi pata", "nhi pata",
    "dont know", "don't know", "do not know", "dunno", "idk", "no idea",
    "wont tell", "won't tell", "will not tell", "not telling", "wont say", "won't say",
    "none of your business", "why do you need", "no comment",
    "na", "naa", "nai", "nahi", "nhi", "kuch nahi", "kuch nhi",
    "secret", "private", "skip this", "next",
}


def _is_refusal(text: str) -> bool:
    """Detect a refusal / non-answer like 'nhi batana', 'pata nahi', 'idk'."""
    t = text.strip().lower()
    # Remove trailing punctuation
    t = re.sub(r"[.!?,]+$", "", t).strip()
    if t in _REFUSAL_PHRASES:
        return True
    # Short Hinglish refusals starting with nhi/nahi (e.g. "nhi batana yaar")
    if re.match(r"^(nhi|nahi|nai|na)\b", t) and len(t.split()) <= 3:
        return True
    return False


def validate_full_name(value: str) -> Tuple[bool, str]:
    value = value.strip()
    if _is_refusal(value):
        return False, "🙏 Your name is required to create your profile. Please enter your full name."
    if not re.match(r"^[A-Za-z .]+$", value) or len(value) < 2:
        return False, "❌ Invalid name. Please use only alphabets and spaces."
    if _looks_like_gibberish(value):
        return False, "❌ That doesn't look like a real name. Please enter your full name."
    return True, value.title()


def calculate_age(dob: datetime) -> int:
    today = datetime.today()
    age = today.year - dob.year
    if (today.month, today.day) < (dob.month, dob.day):
        age -= 1
    return age


def validate_dob(value: str) -> Tuple[bool, str]:
    """DOB in many formats -> normalized to DD-MM-YYYY. Age must be >= 18.
    Accepts: 15-08-1995, 15/08/1995, 17 march 2002, 17 Mar 2002, March 17 2002,
    2002-03-17, etc."""
    raw = value.strip()
    parsed = None
    formats = [
        "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y",
        "%Y-%m-%d", "%Y/%m/%d",
        "%d %B %Y", "%d %b %Y",
        "%B %d %Y", "%b %d %Y",
        "%B %d, %Y", "%b %d, %Y",
        "%d-%B-%Y", "%d-%b-%Y",
    ]
    cleaned = re.sub(r"\s+", " ", raw.replace(",", " ")).strip()
    for fmt in formats:
        try:
            parsed = datetime.strptime(cleaned, fmt)
            break
        except ValueError:
            continue
    if parsed is None:
        return False, (
            "❌ I couldn't read that date. Please use DD-MM-YYYY "
            "(example: 15-08-1995). You can also write it like 15 Aug 1995."
        )
    age = calculate_age(parsed)
    if age < 18:
        return False, f"❌ Age must be at least 18. Calculated age: {age}."
    if age > 100:
        return False, "❌ Age cannot exceed 100 years. Please check the year."
    return True, parsed.strftime("%d-%m-%Y")


def validate_time_of_birth(value: str) -> Tuple[bool, str]:
    """12-hour format like 08:30 AM. Also accepts 8:30am, 8 30 pm, 8am."""
    v = value.strip().upper().replace(".", "")
    v = re.sub(r"\s+", " ", v)
    # Normalize "8 30 AM" -> "8:30 AM"
    m = re.match(r"^(\d{1,2})\s+(\d{2})\s*(AM|PM)$", v)
    if m:
        v = f"{m.group(1)}:{m.group(2)} {m.group(3)}"
    # "8AM" -> "8:00 AM"
    m = re.match(r"^(\d{1,2})\s*(AM|PM)$", v)
    if m:
        v = f"{m.group(1)}:00 {m.group(2)}"

    # Helpful case: user gave a time but FORGOT AM/PM (e.g. "8:00", "8", "8 30")
    has_ampm = ("AM" in v) or ("PM" in v)
    if not has_ampm:
        # Does it look like they tried to give a time?
        time_like = re.match(r"^\d{1,2}(:\d{2})?$", v) or re.match(r"^\d{1,2}\s+\d{2}$", v)
        if time_like:
            clean = v.replace(" ", ":")
            if ":" not in clean:
                clean = f"{clean}:00"
            return False, (
                f"🕐 Almost! Please tell me if *{clean}* is in the *morning or evening*.\n\n"
                f"👉 Add *AM* or *PM* — for example: *{clean} AM* or *{clean} PM*."
            )

    m = re.match(r"^(0?[1-9]|1[0-2]):([0-5][0-9])\s?(AM|PM)$", v)
    if not m:
        return False, (
            "❌ I couldn't read that time.\n"
            "👉 Please use a 12-hour format with *AM* or *PM*.\n"
            "✅ Examples: *08:30 AM*,  *6:45 PM*,  *11:00 AM*"
        )
    return True, f"{int(m.group(1))}:{m.group(2)} {m.group(3)}"


def validate_place_of_birth(value: str) -> Tuple[bool, str]:
    value = value.strip()
    if _is_refusal(value):
        return False, "🙏 Place of birth is required. Please share your city of birth."
    if len(value) < 2:
        return False, "❌ Please enter a valid place of birth."
    if _looks_like_gibberish(value):
        return False, "❌ That doesn't look like a valid place. Please enter your place of birth."
    return True, value.title()


def validate_height(value: str) -> Tuple[bool, str]:
    """Accept: 5'8", 5'8, 5 8, 5ft 8in, 5 feet 8, 5 foot 8, 5', 5ft, 5 feet.
    Feet 3-7, inches 0-11."""
    value = value.strip().lower()
    value = value.replace("inches", "in").replace("inch", "in")
    patterns = [
        r"^(\d)\s*['\u2032]\s*(\d{1,2})\s*[\"\u2033]?$",
        r"^(\d)\s+(\d{1,2})$",
        r"^(\d)\s*ft\s*(\d{1,2})\s*(?:in)?$",
        r"^(\d)\s*feet\s*(\d{1,2})\s*(?:in)?$",
        r"^(\d)\s*foot\s*(\d{1,2})\s*(?:in)?$",
        r"^(\d)\s*['\u2032]$",
        r"^(\d)\s*ft$",
        r"^(\d)\s*feet$",
        r"^(\d)\s*foot$",
    ]
    feet, inches = None, 0
    for p in patterns:
        m = re.match(p, value)
        if m:
            feet = int(m.group(1))
            inches = int(m.group(2)) if len(m.groups()) > 1 and m.group(2) else 0
            break
    if feet is None:
        return False, (
            "❌ I couldn't read that height. Use a format like 5'8\" "
            "or '5 feet 8 inches' (feet 3-7, inches 0-11)."
        )
    if not (3 <= feet <= 7):
        return False, "❌ Height seems unrealistic. Feet must be between 3 and 7."
    if not (0 <= inches <= 11):
        return False, "❌ Inches must be between 0 and 11."
    return True, f"{feet}'{inches}\""


def validate_gothram(value: str) -> Tuple[bool, str]:
    value = value.strip()
    if _is_refusal(value):
        return False, "🙏 Gothram is required for matrimony matching. Please share it."
    if len(value) < 2:
        return False, "❌ Please enter a valid Gothram."
    if _looks_like_gibberish(value):
        return False, "❌ That doesn't look like a valid Gothram. Please enter it again."
    return True, value.title()


def validate_maternal_gothram(value: str, swa_gothram: str) -> Tuple[bool, str]:
    ok, normalized = validate_gothram(value)
    if not ok:
        return False, normalized
    if swa_gothram and normalized.strip().lower() == swa_gothram.strip().lower():
        return False, (
            "❌ Maternal Gothram cannot be the same as Swa Gothram. "
            "Please enter a different Maternal Gothram."
        )
    return True, normalized


def validate_text_min_2(value: str) -> Tuple[bool, str]:
    """Generic text (qualification, profession, occupation). Rejects gibberish
    and refusals like 'nhi batana' / 'pata nahi'."""
    value = value.strip()
    if len(value) < 2:
        return False, "❌ Please enter at least 2 characters."
    if _is_refusal(value):
        return False, (
            "🙏 This information is required to complete your profile.\n"
            "Please share a genuine answer — it helps families find the right match."
        )
    if _looks_like_gibberish(value):
        return False, "❌ That doesn't look like a valid answer. Please enter a real response."
    return True, value.title()


def validate_alpha_name(value: str) -> Tuple[bool, str]:
    """For father/mother name — letters and spaces only."""
    value = value.strip()
    if _is_refusal(value):
        return False, "🙏 This is required. Please share the name to continue."
    if not re.match(r"^[A-Za-z .]+$", value) or len(value) < 2:
        return False, "❌ Invalid name. Use only alphabets and spaces."
    if _looks_like_gibberish(value):
        return False, "❌ That doesn't look like a real name. Please enter it again."
    return True, value.title()


def validate_contact_number(value: str) -> Tuple[bool, str]:
    value = value.strip().replace(" ", "").replace("-", "")
    if not re.match(r"^\+?[1-9]\d{9,14}$", value):
        return False, "❌ Invalid phone number. Include country code (e.g. +919876543210)."
    if not value.startswith("+"):
        value = "+" + value
    return True, value


def validate_menu_choice(value: str, num_options: int) -> Tuple[bool, int]:
    value = value.strip()
    if not value.isdigit():
        return False, 0
    choice = int(value)
    if not (1 <= choice <= num_options):
        return False, 0
    return True, choice


def validate_age_range(value: str) -> Tuple[bool, tuple]:
    """Parse '25-30' or '25 to 30' into (25, 30). Swaps if reversed."""
    value = value.strip().lower().replace(" to ", "-").replace("–", "-").replace("—", "-")
    value = re.sub(r"\s*-\s*", "-", value)
    m = re.match(r"^(\d{2})-(\d{2})$", value)
    if not m:
        return False, (0, 0)
    lo, hi = int(m.group(1)), int(m.group(2))
    if lo > hi:
        lo, hi = hi, lo  # swap reversed range
    if lo < 18 or hi > 100 or lo == hi:
        return False, (0, 0)
    return True, (lo, hi)