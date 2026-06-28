# ============================================
# NyayaAI — FAQ Extractor
# Reads all .txt files from ai/data/faqs/ folder
# Splits FAQ text into blocks
# Returns list of blocks with metadata
# ============================================

import re
from ai.config import FAQ_DIR, SOURCE_MAP
import logging

log = logging.getLogger(__name__)


def get_source_key(filename):
    # match filename to SOURCE_MAP key
    # so we know which FAQ file this belongs to
    filename_upper = filename.upper()

    if "NCRP" in filename_upper:
        return "NCRP_FAQ"
    elif "FAQ2" in filename_upper:
        # all cybercrime advisories collection
        return "FAQ2"
    elif "LAWYER" in filename_upper:
        return "LAWYER_FAQ"
    elif "TRAFFIC" in filename_upper:
        return "TRAFFIC_FAQ"
    elif "ROAD" in filename_upper or "ACCIDENT" in filename_upper:
        return "ROAD_ACCIDENT_FAQ"
    elif "FAQ1" in filename_upper:
        # general cybercrime FAQ collection
        return "FAQ2"
    else:
        # if no match use filename as source key
        return filename.replace(".txt", "").upper()


def extract_faq(faq_path):
    # open and read raw text from .txt file
    with open(str(faq_path), "r", encoding="utf-8") as f:
        raw_text = f.read()

    # get source info for this file
    source_key  = get_source_key(faq_path.name)
    source_name = SOURCE_MAP.get(source_key, faq_path.name)

    blocks        = []
    current_block = ""

    # split on double newlines — FAQ sections separated this way
    raw_blocks = re.split(r'\n{2,}', raw_text.strip())

    for block in raw_blocks:
        block = block.strip()

        # skip empty blocks
        if not block:
            continue

        current_block += " " + block

        # group entries until 300 words reached
        # avoids tiny single QA going to knowledge base
        if len(current_block.split()) > 300:
            blocks.append({
                "text"       : current_block.strip(),
                "page_no"    : "FAQ",
                "source_key" : source_key,
                "source_name": source_name,
                "file_name"  : faq_path.name,
                "file_type"  : "faq"
            })
            current_block = ""

    # handle leftover text that did not reach 300 words
    if current_block.strip():
        blocks.append({
            "text"       : current_block.strip(),
            "page_no"    : "FAQ",
            "source_key" : source_key,
            "source_name": source_name,
            "file_name"  : faq_path.name,
            "file_type"  : "faq"
        })

    log.info(f"✅ Extracted {len(blocks)} blocks from {faq_path.name}")
    return blocks


def extract_all_faqs():
    # read all .txt files from ai/data/faqs/ folder
    # automatically picks up any new FAQ file added
    all_blocks = []

    txt_files = list(FAQ_DIR.glob("*.txt"))

    if not txt_files:
        log.warning(f"⚠️ No FAQ files found in {FAQ_DIR}")
        return []

    for faq_path in txt_files:
        log.info(f"📄 Processing: {faq_path.name}")
        blocks = extract_faq(faq_path)
        all_blocks.extend(blocks)

    log.info(f"✅ Total FAQ blocks extracted: {len(all_blocks)}")
    return all_blocks
