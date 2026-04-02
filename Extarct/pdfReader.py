import pdfplumber

def _try_pdfplumber(path):
    try:
        with pdfplumber.open(path) as pdf:
            pages = pdf.pages[:8]
            return "\n".join(p.extract_text() or "" for p in pages)
    except Exception as e:
        # Return empty string instead of "none" for consistency
        return ""
    
import fitz  # PyMuPDF

def _try_pymupdf(path):
    try:
        doc = fitz.open(path)
        return "\n".join(
            doc[i].get_text()
            for i in range(min(8, len(doc)))
        )
    except Exception:
        return ""

def _is_sufficient(text, min_chars=300):
    if not text: return False
    ascii_ratio = sum(c.isascii() for c in text) / len(text)
    return len(text) > min_chars and ascii_ratio > 0.85

import pytesseract
from pdf2image import convert_from_path

def _try_ocr(path):
    try:
        images = convert_from_path(path, last_page=8, dpi=300)
        return "\n".join(
            pytesseract.image_to_string(img, config="--psm 6")
            for img in images
        )
    except Exception:
        return ""