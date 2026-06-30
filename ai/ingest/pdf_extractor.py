# ============================================
# NyayaAI — PDF Extractor
# Reads all PDFs from ai/data/pdfs/ folder
# Extracts clean text with page number tracking
# Returns list of pages with metadata
# ============================================

import fitz  # PyMuPDF — reads PDF files
import re    # regex — used for text cleaning
from pathlib import Path
from ai.config import PDF_DIR, SOURCE_MAP
import logging

# logger tracks what is happening during extraction
log = logging.getLogger(__name__)


def clean_text(text):
    # remove multiple newlines — replace with single newline
    text = re.sub(r'\n+', '\n', text)
    # remove multiple spaces — replace with single space
    text = re.sub(r' +', ' ', text)
    # remove page number patterns like "Page 1 of 33"
    text = re.sub(r'Page \d+ of \d+', '', text)
    # remove leading and trailing whitespace
    text = text.strip()
    return text


def get_source_key(filename):
    # match filename to SOURCE_MAP key
    # so we know which report this PDF belongs to
    filename_upper = filename.upper()

    if "TAU" in filename_upper and "397" in filename_upper:
        return "TAU_397"
    elif "ADV" in filename_upper or "ADVISORY" in filename_upper:
        return "ADV_003"
    # else:
    #     # if no match found use filename itself as source key
    #     return filename.replace(".pdf", "").upper()
    
    # --- Naye traffic PDFs ---
    elif "A1988" in filename_upper or "1988-59" in filename_upper:
        return "A1988_59"
    elif "AMENDMENT" in filename_upper or "2019" in filename_upper:
        return "MOTOR_VEH"
    elif "ROAD" in filename_upper or "ACCIDENT" in filename_upper or "ADSI" in filename_upper:
        return "RA_2023"
    elif "CMVR" in filename_upper or "1989" in filename_upper:
        return "CMVR_1989"
    
    # --- Naye lawyer/IT Act PDFs ---
    elif "A2000-21" in filename_upper or "IT_ACT" in filename_upper or "ITACT" in filename_upper:
        return "IT_ACT_2000"
    elif "A202345" in filename_upper or "BNS" in filename_upper:
        return "BNS_2023"
    else:
        return filename.replace(".pdf", "").upper()


def extract_pdf(pdf_path):
    # open PDF file using PyMuPDF
    doc = fitz.open(str(pdf_path))
    pages_data = []

    # get source key and name for this PDF
    source_key  = get_source_key(pdf_path.name)
    source_name = SOURCE_MAP.get(source_key, pdf_path.name)

    for page_num in range(len(doc)):
        page = doc[page_num]

        # get_text pulls raw text from each page
        text = page.get_text("text")
        text = clean_text(text)

        # skip pages with very little content
        # likely blank pages or image only pages
        if len(text) < 100:
            continue

        pages_data.append({
            "text"       : text,
            "page_no"    : page_num + 1,    # human readable page number
            "source_key" : source_key,       # short key for mapping
            "source_name": source_name,      # full source name for display
            "file_name"  : pdf_path.name,    # original filename
            "file_type"  : "pdf"
        })

    # close file to free memory after reading
    doc.close()
    log.info(f"✅ Extracted {len(pages_data)} pages from {pdf_path.name}")
    return pages_data


def extract_all_pdfs():
    # read all PDF files from ai/data/pdfs/ folder
    # automatically picks up any new PDF added to folder
    all_pages = []

    # get list of all .pdf files in pdfs folder
    pdf_files = list(PDF_DIR.glob("*.pdf"))

    if not pdf_files:
        log.warning(f"⚠️ No PDF files found in {PDF_DIR}")
        return []

    for pdf_path in pdf_files:
        log.info(f"📄 Processing: {pdf_path.name}")
        pages = extract_pdf(pdf_path)
        all_pages.extend(pages)

    log.info(f"✅ Total pages extracted from all PDFs: {len(all_pages)}")
    return all_pages
