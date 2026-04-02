import re

CORAM_HEADERS = re.compile(r"""
    (?:^|\n)\s*
    (?:
        CORAM\s*[:–-]?                   |
        BEFORE\s*[:–-]?                  |
        PRESENT\s*[:–-]?                 |
        HON['']?BLE\s+JUDGES?\s*[:–-]? |
        BENCH\s*[:–-]?                   |
        SUPREME\s+COURT\.?\s*          |
        IN\s+THE\s+PRESENCE\s+OF\s*[:–-]?
    )
""", re.IGNORECASE | re.VERBOSE | re.MULTILINE)

def extract_section_window(text, pattern, window_lines=12):
    windows = []
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if pattern.search(line):
            end = min(i + window_lines, len(lines))
            
            # Look for section-ending keywords that indicate judges section is over
            # Use more specific patterns to avoid false positives
            for j in range(i + 1, end):
                line_lower = lines[j].lower().strip()
                # Stop at Counsel/Solicitor/Attorney sections (but not if part of a name)
                if (line_lower.startswith("counsel") or 
                    line_lower.startswith("solicitor") or 
                    line_lower.startswith("attorney") or
                    line_lower.startswith("for the")):
                    end = j
                    break
            
            windows.append("\n".join(lines[i:end]))
    return windows

SLR_HEADER_AUTHOR = re.compile(
    r"\(([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?),\s*(?:C\.?J\.?|J\.?)\)"
)

# Example match: "(Amerasinghe, J.)" from running header
# "SC   Samanthilaka v. Ernest Perera (Amerasinghe, J.)   321"