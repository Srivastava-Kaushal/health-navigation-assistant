import re

MED_PREFIXES = ["tab", "tablet", "cap", "capsule", "syrup", "inj", "injection"]
FREQ_WORDS = ["OD", "BD", "TDS", "SOS", "HS", "QID"]

IGNORE_PATTERNS = [
    "doctor", "dr.", "clinic", "mbbs", "reg", "age", "date", "ph:",
    "phone", "take plenty", "rest", "follow up", "medicine)", "green park"
]

def clean_line(line: str) -> str:
    line = re.sub(r"\s+", " ", line).strip()
    return line

def should_ignore_line(line: str) -> bool:
    lower = line.lower()
    for pattern in IGNORE_PATTERNS:
        if pattern in lower:
            return True
    return False

def looks_like_medicine_start(line: str) -> bool:
    lower = line.lower().strip()

    if re.match(r"^(\d+[\).\-\s]|[o@]\)?\s*)", lower):
        return True

    for prefix in MED_PREFIXES:
        if prefix in lower:
            return True

    return False

def extract_duration(text: str):
    match = re.search(r"(\d+\s*(day|days|week|weeks|month|months))", text, re.IGNORECASE)
    return match.group(1) if match else None

def extract_frequency(text: str):
    for freq in FREQ_WORDS:
        if re.search(rf"\b{freq}\b", text, re.IGNORECASE):
            return freq.upper()
    return None

def extract_dosage(text: str):
    match = re.search(r"(\d+\s*(mg|ml)?)", text, re.IGNORECASE)
    return match.group(1).strip() if match else None

def extract_medicine_name(text: str):
    text = clean_line(text)

    # remove numbering / bullets
    text = re.sub(r"^(\d+[\).\-\s]*|[o@]\)?\s*)", "", text, flags=re.IGNORECASE)

    words = text.split()
    if not words:
        return None

    if words[0].lower().strip(".") in MED_PREFIXES:
        words = words[1:]

    stop_words = {"OD", "BD", "TDS", "SOS", "HS", "QID", "for", "before", "after", "|", "1", "tablet", "capsule"}

    name_parts = []
    for word in words:
        w = word.strip(",.").upper()
        if w in stop_words:
            break
        if word.lower() in ["tablet", "capsule"]:
            break
        name_parts.append(word)

    name = " ".join(name_parts).strip()

    # remove noisy trailing symbols
    name = re.sub(r"[^a-zA-Z0-9\s\.]", "", name).strip()

    return name if name else None

def combine_medicine_lines(lines):
    combined = []
    i = 0

    while i < len(lines):
        line = clean_line(lines[i])

        if not line or should_ignore_line(line):
            i += 1
            continue

        if looks_like_medicine_start(line):
            merged = line

            if i + 1 < len(lines):
                next_line = clean_line(lines[i + 1])

                if next_line and not should_ignore_line(next_line) and not looks_like_medicine_start(next_line):
                    merged += " " + next_line
                    i += 1

            combined.append(merged)

        i += 1

    return combined

def parse_prescription_text(raw_text: str):
    lines = [clean_line(line) for line in raw_text.splitlines() if clean_line(line)]
    medicine_lines = combine_medicine_lines(lines)

    parsed = []

    for line in medicine_lines:
        med_name = extract_medicine_name(line)
        dosage = extract_dosage(line)
        frequency = extract_frequency(line)
        duration = extract_duration(line)

        if med_name:
            parsed.append({
                "medicine_name": med_name,
                "dosage": dosage,
                "frequency": frequency,
                "duration": duration
            })

    return parsed