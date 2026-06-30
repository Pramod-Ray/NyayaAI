# ============================================
# NyayaAI — Smart Chunker
# Takes extracted pages and splits into chunks
# Each chunk is small enough for ChromaDB
# Overlap keeps context between chunks intact
# ============================================

import re
from ai.config import CHUNK_SIZE, CHUNK_OVERLAP, CATEGORIES
import logging

log = logging.getLogger(__name__)

# keyword map — detects which topic a chunk belongs to
# if any keyword found in chunk text — assign that category
SECTION_KEYWORDS = {
    "Digital Arrest Scam"       : ["digital arrest", "scam alert",
                                    "advisory"],
    "Scam Modus Operandi"       : ["modus operandi", "impersonation",
                                    "ivr calling", "intimidation",
                                    "digital confinement"],
    "Cybercrime Prevention Tips": ["precaution", "prevention",
                                    "stop think", "verify identity",
                                    "never share"],
    "NCRP Portal Usage"         : ["cybercrime.gov.in", "ncrp",
                                    "reporting portal", "1930"],
    "Complaint Filing Process"  : ["file complaint", "report and track",
                                    "anonymous", "register complaint"],
    "Evidence and Legal Process": ["evidence", "hash value", "fir",
                                    "false complaint", "withdraw"],
    "Money Mule Operations"     : ["money mule", "mule account",
                                    "otp based", "f2f", "commission"],
    "Underground Banking Trends": ["underground banking",
                                    "telegram channel",
                                    "merchant qr", "mqr",
                                    "bulk upload"],
    "USDT Crypto Laundering"    : ["usdt", "crypto",
                                    "inr conversion",
                                    "gaming fund", "stock fund"],
    "Illegal Loan Apps"         : ["loan app", "offshore", "nbfc",
                                    "play store", "blackmail"],
    "Banking Fraud Indicators"  : ["mule account statement",
                                    "pass through", "inflow",
                                    "outflow", "red flag"],
    "Regulatory Recommendations": ["recommendation", "npci",
                                    "upi ecosystem", "fintech"],
    
    # --- Naye traffic keywords ---
    "Driving Licence"          : ["driving licence", "learner's licence",
                                   "licensing authority", "driving test",
                                   "disqualification"],
    "Vehicle Registration"     : ["certificate of registration",
                                   "registering authority",
                                   "registration mark", "fitness"],
    "Traffic Fines and Penalties": ["fine", "punishable", "penalty",
                                     "challan", "imprisonment",
                                     "offence", "section 183",
                                     "section 184", "section 185"],
    "Road Safety"              : ["road safety", "helmet", "seat belt",
                                   "speed limit", "drunk driving",
                                   "emergency vehicle", "good samaritan",
                                   "accident", "hit and run"],
    "Motor Vehicle Insurance"  : ["insurance", "third party",
                                   "certificate of insurance",
                                   "insurer", "claims tribunal"],
    "Traffic Rules and Offences": ["motor vehicle", "traffic sign",
                                    "red light", "overtaking",
                                    "dangerous driving", "mobile phone"],
    
    
    # --- Naye lawyer/criminal law keywords ---
    "Offences Against Body (Murder, Hurt, Assault)": [
        "murder", "culpable homicide", "hurt", "grievous hurt",
        "assault", "criminal force", "negligence", "attempt to murder"
    ],
    "Offences Against Women (Rape, Harassment, Dowry)": [
        "rape", "gang rape", "sexual harassment", "voyeurism",
        "stalking", "dowry death", "cruelty by husband", "trafficking"
    ],
    "Property Offences (Theft, Robbery, Cheating, Forgery)": [
        "theft", "snatching", "extortion", "robbery", "dacoity",
        "criminal breach of trust", "cheating", "forgery",
        "criminal trespass", "false document"
    ],
    "Public Order and Evidence Offences": [
        "unlawful assembly", "rioting", "public nuisance",
        "false evidence", "destruction of evidence",
        "criminal intimidation", "defamation", "organized crime"
    ],
    "Cyber Law and IT Act Provisions": [
        "cybercrime", "hacking", "identity theft", "phishing",
        "cyber stalking", "email spoofing", "malware",
        "information technology act", "computer resource",
        "obscene material", "cyber terrorism"
    ],
    "Digital Signature and Certifying Authorities": [
        "digital signature", "electronic signature", "certifying authority",
        "key pair", "asymmetric crypto", "subscriber", "controller of certifying"
    ],
    "IT Act Penalties and Adjudication": [
        "adjudicating officer", "appellate tribunal", "compounding",
        "penalty and compensation", "section 43", "section 66",
        "section 72", "section 79"
    ]
}


# ── Source -> allowed category domain ─────────────────
# Generic legal words ("fine", "penalty", "offence", "evidence")
# appear in almost every PDF — cybercrime advisories, traffic
# acts, AND criminal law acts. Without this restriction, those
# generic words let one PDF's chunks bleed into a totally
# unrelated category (e.g. BNS criminal-law chunks getting
# tagged "Traffic Fines and Penalties" just because the word
# "punishable" appears in both). source_key (from pdf_extractor)
# tells us which Act/report a chunk actually came from, so we
# restrict scoring to only the categories that make sense for
# that source. FAQ sources / unmapped PDFs get no restriction
# (None) and fall back to plain keyword scoring across everyone.
SOURCE_DOMAIN_CATEGORIES = {
    # Cybercrime advisories / reports
    "TAU_397": {
        "Digital Arrest Scam", "Scam Modus Operandi",
        "Cybercrime Prevention Tips", "NCRP Portal Usage",
        "Complaint Filing Process", "Evidence and Legal Process",
        "Money Mule Operations", "Underground Banking Trends",
        "USDT Crypto Laundering", "Illegal Loan Apps",
        "Banking Fraud Indicators", "Regulatory Recommendations",
        "General Cybercrime",
    },
    "ADV_003": {
        "Digital Arrest Scam", "Scam Modus Operandi",
        "Cybercrime Prevention Tips", "NCRP Portal Usage",
        "Complaint Filing Process", "Evidence and Legal Process",
        "General Cybercrime",
    },
    "NCRP_FAQ": {
        "NCRP Portal Usage", "Complaint Filing Process",
        "Evidence and Legal Process", "General Cybercrime",
    },
    "FAQ2": {
        "Digital Arrest Scam", "Scam Modus Operandi",
        "Cybercrime Prevention Tips", "NCRP Portal Usage",
        "Complaint Filing Process", "Money Mule Operations",
        "Illegal Loan Apps", "Banking Fraud Indicators",
        "General Cybercrime",
    },
    # Traffic / Motor Vehicle sources
    "A1988_59": {
        "Traffic Rules and Offences", "Driving Licence",
        "Vehicle Registration", "Traffic Fines and Penalties",
        "Road Safety", "Motor Vehicle Insurance",
    },
    "MOTOR_VEH": {
        "Traffic Rules and Offences", "Driving Licence",
        "Vehicle Registration", "Traffic Fines and Penalties",
        "Road Safety", "Motor Vehicle Insurance",
    },
    "RA_2023": {
        "Road Safety", "Traffic Accident Statistics",
        "Traffic Rules and Offences",
    },
    "CMVR_1989": {
        "Traffic Rules and Offences", "Driving Licence",
        "Vehicle Registration", "Motor Vehicle Insurance",
        "Road Safety",
    },
    "TRAFFIC_FAQ": {
        "Traffic Rules and Offences", "Driving Licence",
        "Vehicle Registration", "Traffic Fines and Penalties",
        "Road Safety", "Motor Vehicle Insurance",
    },
    "ROAD_ACCIDENT_FAQ": {
        "Road Safety", "Traffic Accident Statistics",
        "Traffic Rules and Offences",
    },
    # Criminal law / IT Act sources
    "IT_ACT_2000": {
        "Cyber Law and IT Act Provisions",
        "Digital Signature and Certifying Authorities",
        "IT Act Penalties and Adjudication",
    },
    "BNS_2023": {
        "Offences Against Body (Murder, Hurt, Assault)",
        "Offences Against Women (Rape, Harassment, Dowry)",
        "Property Offences (Theft, Robbery, Cheating, Forgery)",
        "Public Order and Evidence Offences",
    },
    "LAWYER_FAQ": {
        "Offences Against Body (Murder, Hurt, Assault)",
        "Offences Against Women (Rape, Harassment, Dowry)",
        "Property Offences (Theft, Robbery, Cheating, Forgery)",
        "Public Order and Evidence Offences",
        "Cyber Law and IT Act Provisions",
    },
}


def detect_category(text, source_key=None):
    # lowercase for case insensitive matching
    text_lower = text.lower()

    # ── BEST-MATCH scoring (purana code sirf "first matching
    # category in dict order" return karta tha — isse generic
    # keyword wali categories jaise "Evidence and Legal Process"
    # ya "Traffic Fines and Penalties" har chunk ko khinch lete
    # the, kyunki dictionary ke upar pade the. Specific categories
    # jaise "Offences Against Women" kabhi chance hi nahi paati thi
    # agar chunk me "evidence" ya "fine" word bhi kahin aa jaaye. ──
    #
    # Naya logic: HAR category ke liye score banao (kitne keywords
    # match hue, multi-word/specific keywords ko zyada weight do),
    # phir sabse highest-score wali category choose karo.
    best_category = None
    best_score    = 0

    allowed = SOURCE_DOMAIN_CATEGORIES.get(source_key)

    for category, keywords in SECTION_KEYWORDS.items():
        # agar is source ke liye allowed-domain set defined hai,
        # to sirf usi domain ki categories consider karo — kisi
        # doosre Act/report ki category ko score hi mat karne do
        if allowed is not None and category not in allowed:
            continue

        score = 0
        for kw in keywords:
            if kw in text_lower:
                # multi-word keywords (jaise "digital arrest",
                # "money mule") zyada specific hote hain single
                # generic words (jaise "fine", "evidence") se —
                # isliye unko zyada weight (2x) milta hai
                score += 2 if " " in kw else 1

        if score > best_score:
            best_score   = score
            best_category = category

    # koi keyword match nahi hua (ya allowed-domain me se kuch
    # match hi nahi hua) to fallback: agar domain restricted tha,
    # us domain ki sabse pehli category ko default maan lo
    # (better than always "General Cybercrime" for a traffic/
    # criminal-law PDF); warna General Cybercrime.
    if best_category:
        return best_category
    if allowed:
        return next(iter(allowed))
    return "General Cybercrime"


def chunk_single_page(page, chunk_id_start):
    # split page text into list of words
    words    = page["text"].split()
    chunks   = []
    chunk_id = chunk_id_start
    start    = 0

    # skip pages with very few words
    if len(words) < 50:
        return chunks, chunk_id

    while start < len(words):
        end         = min(start + CHUNK_SIZE, len(words))
        chunk_words = " ".join(words[start:end])

        # detect which topic this chunk belongs to
        # (source_key batata hai yeh chunk konsi Act/report se aaya
        # hai, isliye sirf usi domain ki categories consider hoti hain)
        category = detect_category(chunk_words, page.get("source_key"))

        # build source string for display in frontend
        if page["page_no"] == "FAQ":
            source = page["source_name"]
        else:
            source = f"{page['source_name']} — Page {page['page_no']}"

        chunks.append({
            "chunk_id"   : f"chunk_{chunk_id:04d}",
            "text"       : chunk_words,
            "word_count" : len(words[start:end]),
            "category"   : category,
            "source"     : source,
            "source_key" : page["source_key"],
            "file_type"  : page["file_type"]
        })

        chunk_id += 1

        # calculate next start with overlap
        next_start = end - CHUNK_OVERLAP

        # ensure start always moves forward — prevents infinite loop
        if next_start <= start:
            next_start = start + CHUNK_SIZE
        start = next_start

        # stop when end of words reached
        if end >= len(words):
            break

    return chunks, chunk_id


def chunk_all(pages_data):
    # process all pages and split into chunks
    all_chunks = []
    chunk_id   = 0

    for page in pages_data:
        chunks, chunk_id = chunk_single_page(page, chunk_id)
        all_chunks.extend(chunks)

    log.info(f"✅ Total chunks created: {len(all_chunks)}")
    return all_chunks
