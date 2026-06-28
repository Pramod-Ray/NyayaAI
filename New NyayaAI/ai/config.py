# ============================================
# NyayaAI — Central Configuration
# All settings in one place
# If any value needs to change — only come here
# ============================================

import os
from pathlib import Path
from dotenv import load_dotenv

# load_dotenv reads .env file
# makes all keys available via os.getenv()
load_dotenv()

# ── Base Paths ────────────────────────────────────────
# Path(__file__) gives current file location
# .parent.parent goes up 2 folders to reach project root
BASE_DIR   = Path(__file__).parent.parent

# full paths to data folders
PDF_DIR    = BASE_DIR / "ai" / "data" / "pdfs"
FAQ_DIR    = BASE_DIR / "ai" / "data" / "faqs"
CHROMA_DIR = BASE_DIR / os.getenv("CHROMA_DB_PATH",
                                   "ai/data/chroma_db")

# ── Groq Settings ─────────────────────────────────────
# os.getenv reads value from .env file
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL   = os.getenv("GROQ_MODEL",
                          "llama-3.3-70b-versatile")

# Vision model — image/photo samajhne ke liye (FIR, challan, notice photos)
# qwen3.6-27b multimodal hai — text + image dono leta hai
GROQ_VISION_MODEL = os.getenv("GROQ_VISION_MODEL",
                               "qwen/qwen3.6-27b")

# ── Document Upload Settings ──────────────────────────
# max file size for uploads (MB) — Groq base64 image limit 4MB hai
MAX_UPLOAD_SIZE_MB = 15
ALLOWED_IMAGE_TYPES = ["png", "jpg", "jpeg", "webp"]
ALLOWED_DOC_TYPES   = ["pdf"]

# ── Embeddings Settings ───────────────────────────────
# this model converts text into vectors
# vectors stored in ChromaDB for similarity search
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL",
                             "all-MiniLM-L6-v2")

# ── Chunking Settings ─────────────────────────────────
# controls how PDF text is split before storing
CHUNK_SIZE    = 400  # max words per chunk
CHUNK_OVERLAP = 50   # words repeated between chunks

# ── RAG Settings ──────────────────────────────────────
# how many chunks to retrieve per user query
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", 7))

# ── ChromaDB Settings ─────────────────────────────────
# collection is like a table in ChromaDB
COLLECTION_NAME = "nyayaai_knowledge"

# ── Categories ────────────────────────────────────────
# fixed list of topics for the knowledge base
# every chunk belongs to one of these categories
# used in chunker.py for category detection
# used in frontend for filtering
CATEGORIES = [
    "Digital Arrest Scam",
    "Scam Modus Operandi",
    "Cybercrime Prevention Tips",
    "NCRP Portal Usage",
    "Complaint Filing Process",
    "Evidence and Legal Process",
    "Money Mule Operations",
    "Underground Banking Trends",
    "USDT Crypto Laundering",
    "Illegal Loan Apps",
    "Banking Fraud Indicators",
    "Regulatory Recommendations",
    "General Cybercrime",
    
    # --- Naye traffic categories ---
    "Traffic Rules and Offences",
    "Driving Licence",
    "Vehicle Registration",
    "Traffic Fines and Penalties",
    "Road Safety",
    "Motor Vehicle Insurance",
    "Traffic Accident Statistics",
    
    # --- Naye lawyer/criminal law categories ---
    "Offences Against Body (Murder, Hurt, Assault)",
    "Offences Against Women (Rape, Harassment, Dowry)",
    "Property Offences (Theft, Robbery, Cheating, Forgery)",
    "Public Order and Evidence Offences",
    "Cyber Law and IT Act Provisions",
    "Digital Signature and Certifying Authorities",
    "IT Act Penalties and Adjudication"
]

# ── Topic Groups (for sidebar filter buttons) ─────────
# 3 broad buttons -> maps to multiple CATEGORIES each
# used by retriever.py to filter ChromaDB query by category
TOPIC_GROUPS = {
    "Cybercrime": [
        "Digital Arrest Scam",
        "Scam Modus Operandi",
        "Cybercrime Prevention Tips",
        "NCRP Portal Usage",
        "Complaint Filing Process",
        "Evidence and Legal Process",
        "Money Mule Operations",
        "Underground Banking Trends",
        "USDT Crypto Laundering",
        "Illegal Loan Apps",
        "Banking Fraud Indicators",
        "Regulatory Recommendations",
        "General Cybercrime",
    ],
    "Traffic & Motor Vehicle": [
        "Traffic Rules and Offences",
        "Driving Licence",
        "Vehicle Registration",
        "Traffic Fines and Penalties",
        "Road Safety",
        "Motor Vehicle Insurance",
        "Traffic Accident Statistics",
    ],
    "Criminal Law (BNS & IT Act)": [
        "Offences Against Body (Murder, Hurt, Assault)",
        "Offences Against Women (Rape, Harassment, Dowry)",
        "Property Offences (Theft, Robbery, Cheating, Forgery)",
        "Public Order and Evidence Offences",
        "Cyber Law and IT Act Provisions",
        "Digital Signature and Certifying Authorities",
        "IT Act Penalties and Adjudication",
    ],
}

# ── Source Mapping ────────────────────────────────────
# short key → full readable source name
# add new entry here when new PDF or FAQ is added
SOURCE_MAP = {
    "TAU_397"  : "TAU-397 Monthly Underground Banking Report May 2026",
    "ADV_003"  : "Advisory TAU-ADV-003 Digital Arrest March 2025",
    "NCRP_FAQ" : "NCRP FAQ - cybercrime.gov.in",
    "FAQ2"     : "I4C Cybercrime Advisories Collection",
    
    # --- Naye traffic sources ---
    "A1988_59"  : "Motor Vehicles Act 1988",
    "MOTOR_VEH" : "Motor Vehicles Amendment Act 2019",
    "RA_2023"  : "Road Accidents in India 2023 - MoRTH Report",
    "CMVR_1989": "Central Motor Vehicles Rules 1989",
    
    # --- Naye lawyer/IT Act sources ---
    "IT_ACT_2000" : "Information Technology Act, 2000",
    "BNS_2023"    : "Bharatiya Nyaya Sanhita, 2023",
    "LAWYER_FAQ"  : "Lawyer FAQs - Criminal & Cyber Law",
}

# ── App Settings ──────────────────────────────────────
APP_NAME    = os.getenv("APP_NAME", "NyayaAI")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

# ── Validation ────────────────────────────────────────
# called at startup to check all required keys present
# fails early rather than failing silently later
def validate_config():
    errors = []

    if not GROQ_API_KEY:
        errors.append(
            "GROQ_API_KEY missing — add it in .env file"
        )

    if errors:
        raise ValueError(
            "Config Error:\n" + "\n".join(errors)
        )

    print(f"✅ Config loaded — {APP_NAME} v{APP_VERSION}")
