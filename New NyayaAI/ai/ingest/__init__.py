# ============================================
# NyayaAI — Ingest Package
# This file makes ingest folder a Python package
# Allows importing from ingest folder like:
# from ai.ingest.pdf_extractor import extract_all_pdfs
# from ai.ingest.faq_extractor import extract_all_faqs
# from ai.ingest.chunker import chunk_all
# ============================================

# from ai.ingest.pdf_extractor import extract_all_pdfs
# from ai.ingest.faq_extractor import extract_all_faqs
# from ai.ingest.chunker import chunk_all




from .pdf_extractor import extract_all_pdfs
from .faq_extractor import extract_all_faqs
from .chunker import chunk_all