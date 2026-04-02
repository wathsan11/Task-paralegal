import re

def normalize(text):
    # 1. Unicode ligatures/quotes
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("\ufb01", "fi").replace("\ufb02", "fl")

    # 2. Collapse whitespace, preserve line breaks
    text = re.sub(r"[ \t]+", " ", text)

    # 3. Remove lone page numbers
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)

    # 4. Normalize dash variants
    text = re.sub(r"[\u2013\u2014\u2012]", "-", text)

    # 5. Fix "J ." / "J .." PDF dot artifacts → "J."
    text = re.sub(r"\bJ\s+\.", "J.", text)
    text = re.sub(r"\bJJ\s+\.", "JJ.", text)

    # 6. Fix "SILVA. J.." (dot as comma artifact)
    text = re.sub(r"([A-Z]{3,})\. J\.", r"\1, J.", text)

    return text.strip()
