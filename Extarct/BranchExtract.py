import re
NAME_BODY = r"""
    [A-Z][a-zA-Z\-'\. ]{1,25}         # First token
    (?:
        \s+(?:DE|VAN|DU|BIN|AL)\s+    # Optional particle
        [A-Z][a-zA-Z\-'\. ]{1,25}     # Token after particle
    )?
    (?:\s+[A-Z][a-zA-Z\-'\. ]{1,25}){0,3}  # Remaining tokens
"""

TITLE_PREFIX = r"""
    (?:
        Hon['']?ble\s+(?:Mr\.?\s+)?  |
        Mr\.?\s+Justice\s+           |
        Justice\s+                     |
        Chief\s+Justice\s+            |
    )
"""

JUDGE_WITH_TITLE = re.compile(
    TITLE_PREFIX + r"\s*(" + NAME_BODY + r")\s*(?:,?\s*(?:C\.?J\.?|J\.?))?",
    re.VERBOSE | re.IGNORECASE
)

JUDGE_BARE_SUFFIX = re.compile(
    r"\b(" + NAME_BODY + r")\s*,?\s*(?:(?:PC|C\.?J|J)\.?)\b",
    re.VERBOSE
)

# Also match names with PC/CJ/J titles even without "Hon" or "Justice"
JUDGE_WITH_PC_CJ = re.compile(
    r"\b([A-Z][A-Za-z\.\s\-']{2,30})\s*,?\s*(?:PC|C\.?J\.?|J\.)\b",
    re.IGNORECASE
)

BENCH_SEPARATORS = re.compile(r"\bAND\b|,|;|\n", re.IGNORECASE)

def split_bench_line(line):
    # Strip the header keyword
    line = re.sub(r"^(CORAM|BEFORE|PRESENT|SUPREME COURT)[:\s.]*",
                  "", line, flags=re.IGNORECASE).strip()
    
    # Replace separators while keeping names together
    # Split on AND, comma, semicolon
    parts = BENCH_SEPARATORS.split(line)
    
    # Clean each part: remove judge title suffixes and extra whitespace
    cleaned = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        # Remove all "J.", "C.J.", etc. patterns
        p = re.sub(r"C\.?J\.?|J\.\.?|J(?=\s|$)", "", p, flags=re.IGNORECASE)
        # Clean up remaining whitespace
        p = re.sub(r"\s+", " ", p).strip()
        if p and len(p) > 1:  # Filter out single characters
            cleaned.append(p)
    return cleaned

# For: "H. A. G. DE SILVA, J., AMERASINGHE, J. AND DHEERARATNE, J."
# → ["H. A. G. DE SILVA, J.", "AMERASINGHE, J.", "DHEERARATNE, J."]

import spacy

class NameValidator:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")

    def extract_persons(self, text):
        doc = self.nlp(text[:1000])
        return [
            ent.text.strip() for ent in doc.ents
            if ent.label_ == "PERSON" and len(ent.text.split()) >= 2
        ]

    def is_valid_judge_name(self, name):
        name = name.strip()
        if not name or name in (".", "..", "..."):
            return False
            
        parts = name.split()
        
        # Allow 1-6 parts (single words like "AMERASINGHE" or full names like "H. A. G. DE SILVA")
        if not (1 <= len(parts) <= 6):
            return False
        
        # All significant parts must start with uppercase (skip single dots)
        if not all(p[0].isupper() or p == "." for p in parts if len(p) > 1):
            return False
        
        # Check if it looks like a real name: contains at least 3 letters
        letter_count = sum(1 for c in name if c.isalpha())
        if letter_count < 3:
            return False
        
        # Pattern check: real judge names typically have either:
        # 1. All caps surname (e.g., "AMERASINGHE")
        # 2. Full name with initials (e.g., "H. A. G. DE SILVA")
        # Exclude single initial letters followed by surname like "N. Wijeratne"
        if len(parts) == 2 and len(parts[0]) <= 2 and all(c in "." for c in parts[0].replace(parts[0][0], "")):
            # This is likely "N. Surname" - typically lawyers, not judges
            return False
        
        # Exclude common stopwords that appear in legal text but aren't judge names
        stopwords = {
            "the", "and", "or", "court", "above", "versus", "state", 
            "sri", "law", "reports", "lr", "application", "no", 
            "infringement", "fundamental", "rights", "article", 
            "constitution", "bench", "judgment", "order", "delivered", 
            "case", "justice", "june", "july", "august", "may", "april",
            "march", "september", "october", "november", "december",
            "supreme", "appellate", "district", "proceeding", "before",
            "facts", "issues", "held", "appeal", "respondent", "appellant",
            "evidence", "decision", "reasons", "grounds", "agree", "set",
            "that", "petitioner", "submissions", "background", "findings",
            "coram", "ustice"
        }
        for p in parts:
            # Remove trailing punctuation and check if it's a stopword
            p_clean = p.rstrip(':.,;)')
            if p_clean.lower() in stopwords:
                return False
        return True
import re
