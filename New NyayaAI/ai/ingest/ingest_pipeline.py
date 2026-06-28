# ============================================
# NyayaAI — Ingest Pipeline
# Main entry point for ingesting data
# Runs all steps in sequence:
# 1. Extract text from PDFs
# 2. Extract text from FAQs
# 3. Chunk all extracted text
# 4. Store chunks in ChromaDB
# Run this file whenever new data is added
# ============================================

import logging
from ai.config import validate_config
from ai.ingest.pdf_extractor import extract_all_pdfs
from ai.ingest.faq_extractor import extract_all_faqs
from ai.ingest.chunker import chunk_all
from ai.knowledge_base.vector_store import store_chunks, get_collection_count

# setup logging — shows what is happening step by step
logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s — %(levelname)s — %(message)s"
)
log = logging.getLogger(__name__)


def run_ingestion():
    print("\n" + "="*50)
    print("  NyayaAI — Ingest Pipeline")
    print("="*50 + "\n")

    # validate config — check all keys present
    validate_config()

    # ── Step 1: Extract PDFs ──────────────────────────
    print("📄 Step 1: Extracting PDFs...")
    pdf_pages = extract_all_pdfs()
    print(f"✅ PDF pages extracted: {len(pdf_pages)}")

    # ── Step 2: Extract FAQs ──────────────────────────
    print("\n📄 Step 2: Extracting FAQs...")
    faq_blocks = extract_all_faqs()
    print(f"✅ FAQ blocks extracted: {len(faq_blocks)}")

    # merge pdf pages and faq blocks into single list
    all_pages = pdf_pages + faq_blocks
    print(f"\n✅ Total pages/blocks: {len(all_pages)}")

    # ── Step 3: Chunk All Text ────────────────────────
    print("\n✂️  Step 3: Chunking text...")
    all_chunks = chunk_all(all_pages)
    print(f"✅ Total chunks created: {len(all_chunks)}")

    # ── Step 4: Store in ChromaDB ─────────────────────
    print("\n💾 Step 4: Storing in ChromaDB...")
    store_chunks(all_chunks)

    # verify total chunks stored
    total = get_collection_count()
    print(f"✅ Total chunks in knowledge base: {total}")

    print("\n" + "="*50)
    print("  ✅ Ingestion Complete!")
    print("="*50 + "\n")


if __name__ == "__main__":
    # run ingestion when file is called directly
    # python ai/ingest/ingest_pipeline.py
    run_ingestion()
