import re

# Matches: "AMERASINGHE, J." as a standalone line
AUTHOR_STANDALONE = re.compile(
    r"(?:^|\n)\s*([A-Z]{3,}(?:[\s\.][A-Z]{1,4})*),?\s*J\.?\s*(?:\n|$)",
    re.MULTILINE
)

# Additional pattern for "J. NAME, J." format on separate lines
AUTHOR_JUDGE_PREFIX = re.compile(
    r"(?:^|\n)\s*J\.?\s+([A-Z][a-zA-Z\s]+?),?\s*J\.?\s*(?:\n|$)",
    re.MULTILINE | re.IGNORECASE
)

AUTHOR_PATTERNS = [
    # "Justice Singh delivered the judgment"
    re.compile(
        r"(?:Justice|J\.?)\s+([A-Z][a-zA-Z\s\.]+?)\s*"
        r"(?:delivered|authored|pronounced|dictated)\b",
        re.IGNORECASE
    ),
    # "judgment delivered by Justice Singh"
    re.compile(
        r"(?:judgment|order).*?(?:delivered|written)\s+by\s+"
        r"(?:Justice|J\.?)\s+([A-Z][a-zA-Z\s\.]+?)\b",
        re.IGNORECASE
    ),
    # "For the reasons stated in my judgment I pronounce the order accordingly."
    # followed by judge name on next line
    re.compile(
        r"in\s+my\s+judgment\s+I\s+(?:pronounce|make).*?\n\s*"
        r"(?:J\.?\s+)?([A-Z][a-zA-Z\s\.]+?)\s*,?\s*(?:J\.?\s*)?(?:\n|$)",
        re.IGNORECASE | re.MULTILINE
    ),
    # Chief Justice indicator: "NAME, PC, CJ" in CORAM section
    re.compile(
        r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\s*,\s*PC\s*,\s*CJ",
        re.IGNORECASE
    ),
]

CONCURRENCE = re.compile(
    r"(?:^|\n)\s*(?:J\.?\s+)?([A-Z][A-Za-z\s\.]+?)(?:,?\s*J\.?)?(?:\n[^\n]{0,100})?\n\s*I\s+(?:agree|concur)",
    re.IGNORECASE | re.MULTILINE | re.DOTALL
)

def filter_concurrences(text, candidates):
    concurring_surnames = set()
    for m in CONCURRENCE.finditer(text):
        name = m.group(1).strip()
        # Remove "J.", "C.J.", etc. prefixes/suffixes
        name = re.sub(r"^J\.?\s+|,?\s*J\.?\s*$", "", name, flags=re.IGNORECASE).strip()
        # Extract surname (last token)
        surname = name.strip().split()[-1].lower() if name else ""
        if surname:
            concurring_surnames.add(surname)
    
    filtered = []
    for c in candidates:
        # Clean the candidate name: remove "J." prefix/suffix
        c_clean = re.sub(r"^J\.?\s+|,?\s*J\.?\s*$", "", c, flags=re.IGNORECASE).strip()
        surname = c_clean.split()[-1].lower()
        if surname not in concurring_surnames:
            filtered.append(c)
    return filtered

# From sample:
# "H.A.G. DE SILVA, J. - I agree."   → De Silva = bench, not author
# "R.N.M. DHEERARATNE, J - I agree." → Dheeraratne = bench, not author

def cross_validate(candidates, bench):
    """Keep only candidates whose surname matches a bench member."""
    bench_surnames = {n.split()[-1].lower() for n in bench}
    validated = []
    for c in candidates:
        # Clean candidate: remove "J." prefix/suffix for matching
        c_clean = re.sub(r"^J\.?\s+|,?\s*J\.?\s*$", "", c, flags=re.IGNORECASE).strip()
        surname = c_clean.split()[-1].lower() if c_clean else ""
        if surname in bench_surnames:
            validated.append(c_clean if c_clean else c)
    return validated if validated else candidates


# Deduplicate candidate list by normalizing case and removing J. prefixes
def deduplicate_candidates(candidates):
    """Remove case-insensitive duplicates, keeping clean versions without J. prefix."""
    seen = {}  # Maps normalized names to their clean versions
    for c in candidates:
        # Normalize: remove J. prefix and convert to lowercase
        c_normalized = re.sub(r"^J\.?\s+|,?\s*J\.?\s*$", "", c, flags=re.IGNORECASE).strip().lower()
        if c_normalized and c_normalized not in seen:
            # Store the clean, properly-cased version
            c_clean = re.sub(r"^J\.?\s+|,?\s*J\.?\s*$", "", c, flags=re.IGNORECASE).strip()
            seen[c_normalized] = c_clean if c_clean else c
    return list(seen.values())


import re
