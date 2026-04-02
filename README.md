# Task-Paralegal: Judgment Document Extraction

A Python-based extraction system for automatically extracting bench members and authoring judges from Sri Lankan Supreme Court judgment PDFs.

## Overview

This project processes judgment documents in PDF format and extracts:
- **Bench members**: The list of judges who heard the case
- **Authoring judge**: The judge(s) who delivered/wrote the judgment

The system handles various PDF formats, layouts, and document structures using multiple text extraction methods and pattern matching.

## Features

✅ **Multi-format PDF support** - Handles text-based, scanned, and corrupted PDFs  
✅ **Robust pattern matching** - Uses regex patterns for different judgment structures  
✅ **Named Entity Recognition** - Integrates spaCy for enhanced name detection  
✅ **Intelligent validation** - Filters out non-judge names using comprehensive stopwords  
✅ **JSON output** - Structured extraction results for programmatic use  

## Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Setup

1. **Clone or navigate to the project directory:**
   ```bash
   cd paralegal-lk-internship-assignment
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment:**
   - On Windows (PowerShell):
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - On Windows (Command Prompt):
     ```cmd
     .venv\Scripts\activate.bat
     ```
   - On macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Extraction Pipeline

```bash
python main.py
```

**What happens:**
- The script processes all PDFs in the `input_pdfs/` directory
- Extracts bench members and authoring judges using pattern matching and NLP
- Saves results as JSON files in `output_json/` directory

### Input and Output

**Input:**
- Place PDF files in the `input_pdfs/` folder
- Supports any Supreme Court judgment PDF format

**Output:**
- Each PDF generates a JSON file with the same name in `output_json/`
- JSON structure:
  ```json
  {
    "file": "filename.pdf",
    "bench": ["Judge Name 1", "Judge Name 2", ...],
    "author_judge": ["Authoring Judge Name"],
    "extraction_meta": {
      "coram_windows_found": 2,
      "text_length": 19932
    }
  }
  ```

## Approach

The extraction system uses a multi-stage pipeline designed to handle the diverse formats and layouts found in Sri Lankan Supreme Court judgments:

### 1. **PDF Text Extraction**
   - **Primary method**: Uses `pdfplumber` to extract text from text-based PDFs (fastest, most reliable)
   - **Fallback method 1**: Uses `PyMuPDF` for PDFs that pdfplumber struggles with
   - **Fallback method 2**: Uses OCR (pytesseract + pdf2image) for scanned/image-based PDFs
   - Gracefully degrades through each method until sufficient text is recovered

### 2. **Text Normalization**
   - Converts Unicode ligatures and quote variants to standard ASCII
   - Collapses excessive whitespace while preserving line breaks
   - Removes page numbers and normalizes dash/hyphen variants
   - Fixes PDF extraction artifacts (e.g., `J .` → `J.`)

### 3. **Bench Section Detection (CORAM)**
   - Identifies the bench/court composition section using regex patterns
   - Recognizes multiple header formats:
     - `CORAM: Judge Names`
     - `BEFORE: Judge Names`
     - `SUPREME COURT: Judge Names`
   - Extracts a fixed-size window around the header to capture all judges
   - Stops extraction at counsel/solicitor keywords to avoid including lawyers' names

### 4. **Bench Member Extraction**
   - Applies multiple regex patterns to identify judge names:
     - `JUSTICE/HON. NAME, J./PC` (title-based pattern)
     - `NAME, J./PC` (suffix-based pattern)
     - `NAME, PC, CJ` (Chief Justice identifier)
   - Falls back to Named Entity Recognition (spaCy) for complex names
   - Splits comma-separated judge lists on the same line
   - Removes suffixes like "J.", "C.J.", "PC" to clean names

### 5. **Judge Name Validation**
   - Applies multi-criterion validation to filter false positives:
     - Requires minimum 3 letters per name
     - Rejects single-initial names (e.g., "N. Wijeratne")
     - Filters 40+ stopwords (legal terms, section headers, etc.)
     - Rejects names ending with colons
     - Ensures names have at least one uppercase letter
   - Deduplicates results case-insensitively

### 6. **Authoring Judge Extraction**
   - Uses pattern priority system with multiple detection methods:
     - **Pattern 0**: "Justice NAME delivered/pronounced the judgment"
     - **Pattern 1**: "Judgment delivered by Justice NAME"
     - **Pattern 2**: "I pronounce/make NAME, J." (main author statement)
     - **Pattern 3**: "NAME, PC, CJ" (Chief Justice from CORAM section)
   - Applies filters to remove concurring judges (those who "agree" without authoring)
   - Cross-validates author against the bench list
   - Deduplicates and normalizes author names

### 7. **Result Assembly**
   - Formats bench members as a clean list
   - Returns authoring judge(s) separately
   - Includes metadata (window count, text length) for diagnostics

## Architecture

```
main.py
├── extract_text()              [PDF extraction with fallbacks]
├── normalize()                 [Text cleanup & standardization]
├── extract_section_window()    [CORAM section detection]
├── extract_bench()             [Judge name extraction & validation]
└── extract_author()            [Authoring judge identification]

Extarct/
├── pdfReader.py               [PDF text extraction methods]
├── textNormalizer.py          [Text normalization utilities]
├── SectionDetection.py         [CORAM/Bench section patterns]
├── BranchExtract.py            [Judge name extraction & validation]
└── AutherExtraction.py         [Authoring judge detection]
```

## Example Results

**Sample 1 - Traditional Format:**
- Bench: H.A.G. DE SILVA, AMERASINGHE, DHEERARATNE
- Author: AMERASINGHE
- Status: ✅ Extracted successfully

**Sample 4 - Chief Justice Format:**
- Bench: 6 judges including Jayantha Jayasuriya (CJ)
- Author: Jayantha Jayasuriya (detected via "PC, CJ" suffix)
- Status: ✅ Extracted successfully

## Key Patterns & Regex

| Pattern | Matches | Example |
|---------|---------|---------|
| CORAM_HEADERS | Bench section headers | `CORAM:`, `BEFORE:`, `SUPREME COURT:` |
| JUDGE_WITH_TITLE | Justice + name + suffix | `Justice AMERASINGHE, J.` |
| JUDGE_BARE_SUFFIX | Name + J./PC/CJ/PC suffix | `DHEERARATNE, J.` |
| JUDGE_WITH_PC_CJ | Chief Justice indicator | `Jayantha Jayasuriya, PC, CJ` |
| AUTHOR_PATTERNS | Judge delivery statements | `delivered the judgment`, `I pronounce` |

## Troubleshooting

**No judges extracted:**
- Check if PDF is readable (try opening manually first)
- Verify bench section has standard headers (CORAM, BEFORE, SUPREME COURT)
- Ensure judge names follow expected format (Capital letters, spaces)

**Too many false positives:**
- Add new stopwords to `NameValidator.STOPWORDS` in `Extarct/BranchExtract.py`
- Adjust validation thresholds in `is_valid_judge_name()`

**Author not extracted:**
- Check if judgment contains standard delivery phrases
- Verify author is in the bench list (cross-validation requirement)
- Look for Chief Justice indicators in CORAM (PC, CJ suffix)

## Project Structure

```
paralegal-lk-internship-assignment/
├── main.py                    [Main extraction orchestrator]
├── requirements.txt           [Python dependencies]
├── README.md                  [This file]
├── Extarct/
│   ├── pdfReader.py
│   ├── textNormalizer.py
│   ├── SectionDetection.py
│   ├── BranchExtract.py
│   └── AutherExtraction.py
├── input_pdfs/               [Place PDFs here]
├── output_json/              [Extraction results]
└── Data/                     [Sample data & reference]
```

## Dependencies

- **pdfplumber**: PDF text extraction
- **PyMuPDF**: Alternative PDF processing
- **pytesseract**: OCR for scanned PDFs
- **pdf2image**: Image conversion for OCR
- **spacy**: Named Entity Recognition (en_core_web_sm model)
- **reportlab**: PDF generation (testing)

## Author & License

See LICENSE file for project licensing information.