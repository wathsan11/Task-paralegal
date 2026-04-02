from pathlib import Path
import json, logging

from Extarct.pdfReader import _try_pdfplumber, _try_pymupdf, _try_ocr, _is_sufficient
from Extarct.textNormalizer import normalize
from Extarct.SectionDetection import CORAM_HEADERS, extract_section_window, SLR_HEADER_AUTHOR
from Extarct.BranchExtract import NameValidator, JUDGE_WITH_TITLE, JUDGE_BARE_SUFFIX, JUDGE_WITH_PC_CJ, split_bench_line
from Extarct.AutherExtraction import filter_concurrences, cross_validate, deduplicate_candidates, AUTHOR_STANDALONE, AUTHOR_JUDGE_PREFIX, AUTHOR_PATTERNS

def extract_text(pdf_path):
    text = _try_pdfplumber(pdf_path)
    if _is_sufficient(text): return text
    text = _try_pymupdf(pdf_path)
    if _is_sufficient(text): return text
    return _try_ocr(pdf_path)

def extract_bench(windows, validator):
    bench_candidates = set()
    for window in windows:
        for line in window.split('\n'):
            # Try to match with titles or suffixes first
            for m in JUDGE_WITH_TITLE.finditer(line):
                name = m.group(1).strip()
                if validator.is_valid_judge_name(name):
                    bench_candidates.add(name)
            for m in JUDGE_BARE_SUFFIX.finditer(line):
                name = m.group(1).strip()
                if validator.is_valid_judge_name(name):
                    bench_candidates.add(name)
            # Try matching names with PC/CJ/J suffixes
            for m in JUDGE_WITH_PC_CJ.finditer(line):
                name = m.group(1).strip()
                if validator.is_valid_judge_name(name):
                    bench_candidates.add(name)
            
            # Fallback to Named Entity Recognition handling lines splitting
            parts = split_bench_line(line)
            for part in parts:
                if validator.is_valid_judge_name(part):
                    bench_candidates.add(part)
                else:
                    ents = validator.extract_persons(part)
                    for ent in ents:
                        if validator.is_valid_judge_name(ent):
                            bench_candidates.add(ent)
                            
    return list(bench_candidates)

def extract_author(text, bench):
    candidates = []
    author_patterns_found = []
    
    # First, try high-confidence author patterns
    for pattern in AUTHOR_PATTERNS:
        for m in pattern.finditer(text):
            author_name = m.group(1).strip()
            candidates.append(author_name)
            author_patterns_found.append(author_name)
    
    # If no strong patterns matched, try other sources
    if not author_patterns_found:
        for m in AUTHOR_STANDALONE.finditer(text):
            candidates.append(m.group(1).strip())
        
        for m in AUTHOR_JUDGE_PREFIX.finditer(text):
            candidates.append(m.group(1).strip())
            
        for m in SLR_HEADER_AUTHOR.finditer(text):
            candidates.append(m.group(1).strip())
    
    # Clean all candidates (remove J. prefix/suffix)
    import re
    cleaned_candidates = []
    for c in candidates:
        c_clean = re.sub(r"^J\.?\s+|,?\s*J\.?\s*$", "", c, flags=re.IGNORECASE).strip()
        if c_clean:
            cleaned_candidates.append(c_clean)
    
    # Deduplicate case-insensitively
    cleaned_candidates = deduplicate_candidates(cleaned_candidates)
    
    # Filter out concurring judges (those who say "I agree" after their name)
    cleaned_candidates = filter_concurrences(text, cleaned_candidates)
    
    # Cross-validate against bench
    valid_authors = cross_validate(cleaned_candidates, bench)
    
    return list(set(valid_authors))

def process_pdf(pdf_path, validator):
    raw = extract_text(str(pdf_path))
    text = normalize(raw)
    windows = extract_section_window(text, CORAM_HEADERS)
    bench = extract_bench(windows, validator)
    author = extract_author(text, bench)
    return {
        "file": pdf_path.name,
        "bench": bench,
        "author_judge": author,
        "extraction_meta": {
            "coram_windows_found": len(windows),
            "text_length": len(text)
        }
    }

def main():
    validator = NameValidator()
    for pdf in sorted(Path("input_pdfs").glob("*.pdf")):
        try:
            result = process_pdf(pdf, validator)
            out = Path("output_json") / (pdf.stem + ".json")
            out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
            logging.info(f"OK: {pdf.name}")
        except Exception as e:
            logging.error(f"FAIL: {pdf.name} — {e}", exc_info=True)
    

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
