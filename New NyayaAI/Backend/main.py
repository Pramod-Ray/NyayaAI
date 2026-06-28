from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session as DBSession
from database import get_db, engine
import models, schemas
from groq import Groq
import chromadb
from sentence_transformers import SentenceTransformer
import os
import re
import uuid
from dotenv import load_dotenv
from typing import List, Optional

from utils.document_processor import (
    validate_file,
    encode_image_to_data_url,
    extract_text_from_pdf,
)

load_dotenv()

print("GROQ KEY =", os.getenv("GROQ_API_KEY")[:15])

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="NyayaAI Backend")

# Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


GROQ_VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "qwen/qwen3.6-27b")

# ChromaDB — absolute path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_PATH = os.path.join(BASE_DIR, os.getenv("CHROMA_DB_PATH", "ai/data/chroma_db"))

chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = chroma_client.get_or_create_collection(name="nyayaai_knowledge")

print("CHROMA PATH =", CHROMA_PATH)
print("COLLECTION COUNT =", collection.count())

# Embedding model
embedding_model = SentenceTransformer(os.getenv("EMBEDDING_MODEL"))

# ── Reasoning-model cleanup ────────────────────────────
def clean_llm_response(text: str) -> str:
    if not text:
        return text
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"^.*?</think>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
    return cleaned.strip()

def ask_llm(messages):

    # ---------------- GROQ ----------------

    try:
        completion = groq_client.chat.completions.create(
            model=os.getenv("GROQ_MODEL"),
            messages=messages,
            max_tokens=1500,
            temperature=0.1,
            top_p=0.9,
        )

        print("✅ Response from GROQ")

        return clean_llm_response(
            completion.choices[0].message.content
        )

    except Exception as e:
        print("❌ Groq Failed")
        print(e)

        raise HTTPException(
            status_code=500,
            detail=f"Groq Error: {str(e)}"
        )
        
        
        
@app.get("/")
def root():
    return {"message": "NyayaAI Backend is running!"}

@app.post("/session/new")
def new_session(db: DBSession = Depends(get_db)):
    session_id = str(uuid.uuid4())
    session = models.Session(session_id=session_id, title="New Chat")
    db.add(session)
    db.commit()
    return {"session_id": session_id}

@app.get("/sessions", response_model=List[schemas.SessionOut])
def get_sessions(db: DBSession = Depends(get_db)):
    return db.query(models.Session)\
        .order_by(models.Session.created_at.desc()).all()

@app.get("/session/{session_id}/history", response_model=List[schemas.MessageOut])
def get_history(session_id: str, db: DBSession = Depends(get_db)):
    messages = db.query(models.ChatHistory)\
        .filter(models.ChatHistory.session_id == session_id)\
        .order_by(models.ChatHistory.id.asc()).all()
    if not messages:
        raise HTTPException(status_code=404, detail="Session not found")
    return messages

@app.post("/chat", response_model=schemas.ChatResponse)
def chat(request: schemas.ChatRequest, db: DBSession = Depends(get_db)):

    print(f"🐛 DEBUG topic_name={request.topic_name!r}  topic_filter={request.topic_filter!r}  message={request.message!r}")

    session = db.query(models.Session)\
        .filter(models.Session.session_id == request.session_id).first()
    if not session:
        session = models.Session(session_id=request.session_id, title=request.message[:50])
        db.add(session)
    else:
        if session.title == "New Chat":
            session.title = request.message[:50]

    history = db.query(models.ChatHistory)\
        .filter(models.ChatHistory.session_id == request.session_id)\
        .order_by(models.ChatHistory.id.asc()).all()

    # RAG - relevant context dhundo
    try:
        query_embedding = embedding_model.encode(
            [request.message]
        ).tolist()

        # topic_filter aaya hai to sirf un categories ke chunks search karo
        # (sidebar ke "Cybercrime / Traffic / Criminal Law" buttons se aata hai)
        query_kwargs = dict(
            query_embeddings=query_embedding,
            n_results=5
        )

        if request.topic_filter:
            query_kwargs["where"] = {"category": {"$in": request.topic_filter}}

        results = collection.query(**query_kwargs)
        
        # print("========== CHROMA DEBUG ==========")
        # print(results.get("metadatas"))
        # print(results.get("documents"))
        # print("==================================")
        print(f"🐛 DEBUG topic_name={request.topic_name!r} topic_filter={request.topic_filter!r} message={request.message!r}")

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Retrieval Error: {str(e)}"
        )
        
    metadatas = results.get("metadatas", [[]])
        
    documents = results.get("documents", [])

    distances = results.get("distances", [[]])

    filtered_docs = []

    if documents and distances:

        for doc, score in zip(documents[0], distances[0]):

            if score < 1.0:
                filtered_docs.append(doc)
 
        documents = [filtered_docs]
    
    context = ""

    if documents and len(documents[0]) > 0:

        MAX_CONTEXT = 3000

        seen = set()

        for chunk in documents[0]:

            chunk = chunk.strip()

            if chunk in seen:
                continue

            if len(chunk) < 80:
                continue

            seen.add(chunk)

            if len(context) + len(chunk) > MAX_CONTEXT:
                break

            context += chunk + "\n\n"
    # topic_filter active tha but RAG ko us category me kuch bhi
    # relevant nahi mila — matlab sawal selected topic ke bahar ka hai.
    # Yeh RAG-based check hai, keyword list pe depend nahi karta,
    # isliye keyword list me na hone wale sawalon ko bhi pakad lega.
    
    # ---------------- Topic Validation ----------------
    topic_out_of_scope = False

    if request.topic_filter:

        retrieved_categories = set()

        if metadatas and len(metadatas[0]) > 0:
            for meta in metadatas[0]:
                category = meta.get("category")
                if category:
                    retrieved_categories.add(category.lower())

        allowed_topics = {t.lower() for t in request.topic_filter}

        if retrieved_categories:
            topic_out_of_scope = retrieved_categories.isdisjoint(allowed_topics)

        # Agar retrieval fail ho jaye to turant reject mat karo.
        else:
            topic_out_of_scope = False


    question = request.message.lower()


    # Har topic ke liye "doosre topics ke" keywords — fast pre-check
    # (RAG call se pehle hi obvious mismatch pakad lo, extra safety net)
    OTHER_TOPIC_KEYWORDS = {
        "Traffic & Motor Vehicle": [
            "murder", "rape", "dowry", "assault", "theft", "robbery",
            "cheating", "forgery", "bns",
            "cybercrime", "phishing", "loan app", "money mule",
            "crypto", "digital arrest", "bank fraud",
        ],
        "Criminal Law (BNS & IT Act)": [
            "traffic", "driving licence", "vehicle", "helmet",
            "seat belt", "road safety",
            "cybercrime", "phishing", "loan app", "money mule",
            "crypto", "digital arrest", "bank fraud",
        ],
        "Cybercrime": [
            "traffic", "driving licence", "vehicle", "helmet",
            "seat belt", "road safety",
            "murder", "rape", "dowry", "assault", "theft", "robbery",
            "cheating", "forgery", "bns",
        ],
    }

    other_keywords = OTHER_TOPIC_KEYWORDS.get(request.topic_name, [])
    # word-boundary match — purana code "word in question" plain
    # substring check tha, jisse galat false-positives aate the
    # (e.g. agar kisi single-word keyword ka substring kisi doosre
    # word ke beech mein aa jaaye). \b...\b se sirf poora word /
    # poora phrase match hota hai, partial substring nahi.
    keyword_out_of_scope = bool(other_keywords) and any(
        re.search(r"\b" + re.escape(word) + r"\b", question)
        for word in other_keywords
    )

    # Dono checks me se koi bhi true ho to block: ya to keyword se
    # explicitly doosre topic ka pata chala, ya RAG ko locked
    # category me kuch nahi mila.
    if request.topic_name == "Cybercrime":

        cyber_keywords = [
            "cyber","online","internet","hacking","hack","otp","upi",
            "bank fraud","phishing","digital arrest","loan app",
            "qr","scam","fraud","cybercrime","email","social media",
            "crypto","wallet","malware","virus","ransomware"
        ]

        if not any(k in question for k in cyber_keywords):
            return {
                "session_id": request.session_id,
                "response": (
                    "⚠️ This chat is locked to Cybercrime.\n\n"
                    "Your question is not related to Cybercrime.\n\n"
                    "Please change the Topic Lock to ask Traffic or Criminal Law questions."
                )
            }

    elif request.topic_name == "Traffic & Motor Vehicle":

        traffic_keywords = [
            "traffic","driving","licence","license","helmet","car",
            "bike","vehicle","challan","seat belt","road","rto",
            "accident","speed","parking"
        ]

        if not any(k in question for k in traffic_keywords):
            return {
                "session_id": request.session_id,
                "response": (
                    "⚠️ This chat is locked to Traffic & Motor Vehicle.\n\n"
                    "Please change the Topic Lock."
                )
            }

    elif request.topic_name == "Criminal Law (BNS & IT Act)":

        criminal_keywords = [
            "murder","rape","dowry","assault","theft","robbery",
            "cheating","forgery","bns","ipc","crime","court",
            "fir","police","lawyer"
        ]

        if not any(k in question for k in criminal_keywords):
            return {
                "session_id": request.session_id,
                "response": (
                    "⚠️ This chat is locked to Criminal Law.\n\n"
                    "Please change the Topic Lock."
                )
            }

    # ── Topic Persona ──────────────────────────────────────
    # Har topic lock ka apna real-world expert persona hai —
    # tone, vocabulary, aur sign-off us expert jaisa hota hai.
    # Bot khud ko introduce NAHI karta ("main expert hoon" type) —
    # sirf tone/style/sign-off se persona naturally jhalakta hai.
    TOPIC_PERSONAS = {
        "Cybercrime": """
        PERSONA — Cyber Crime Cell Officer / Helpline 1930 Expert:
        - Tone: alert, sturdy, thoda urgent jab scam ki baat ho — jaise koi cyber cell
          officer victim ko calmly samjha raha ho ki ghabrana nahi hai, action lena hai.
        - Scam pattern dikhe to seedha naam do (digital arrest, phishing, money mule, etc.)
          aur clearly bolo "yeh ek SCAM hai" — jaise real cyber expert turant red-flag karta hai.
        - Practical, time-sensitive advice do: evidence save karo, screenshot lo, link pe click
          mat karo, OTP/paisa kisi ko mat do.
        - Jab bhi relevant ho, NCRP portal (cybercrime.gov.in) aur 1930 helpline ka
          mention naturally karo — jaise real officer karega, sirf list ke end mein nahi
          balki advice ke flow mein.
        - Language: Hinglish mein practical aur thoda directive — jaise field officer
          baat kar raha ho, lecture nahi de raha.
        """,
        "Traffic & Motor Vehicle": """
        PERSONA — Traffic Police / RTO Officer:
        - Tone: rule-clear, matter-of-fact — jaise traffic police ya RTO official
          seedha rule, fine amount, aur section bata raha ho.
        - Fines, penalties, aur sections EXACT numbers ke saath do — round-up ya
          vague mat bolo agar context mein exact figure available hai.
        - Process-oriented: licence renewal, challan payment, registration jaise sawalon
          mein step-by-step official process bolo — jaise RTO counter pe baithe officer
          guide kar raha ho.
        - Road safety ka mention naturally aaye jab relevant ho (jaise helmet/seatbelt
          ka sawal ho to safety angle bhi touch karo, sirf fine nahi).
        - Language: Hinglish mein practical aur to-the-point — jaise actual traffic
          stop pe officer bolta hai.
        """,
        "Criminal Law (BNS & IT Act)": """
        PERSONA — Criminal Lawyer / Legal Advisor:
        - Tone: formal, measured, section-wise — jaise ek wakil client ko case
          samjha raha ho courtroom register mein.
        - Har offence ke saath relevant BNS section ya IT Act provision clearly
          quote karo (jahan context mein available ho) — jaise lawyer apne
          opinion ko legal basis ke saath deta hai.
        - Punishment/penalty ka mention karo jahan applicable ho, aur zaroor
          clarify karo ki yeh general legal information hai, case-specific
          advice ke liye qualified wakil se consult karna chahiye.
        - Sensitive topics (rape, dowry, assault) par tone respectful aur
          serious rakho — kabhi casual ya dismissive na ho.
        - Language: thoda formal Hinglish, jaise legal consultation mein
          bola jaata hai — explanatory par halka-phulka nahi.
        """,
    }

    persona_instruction = TOPIC_PERSONAS.get(request.topic_name, "")

    # ── Language selection ────────────────────────────────
    # frontend se "English" ya "Hindi" aata hai (toggle button se)
    # default "English" rakha hai agar field missing ho
    language = (request.language or "English").strip().lower()

    if language == "hindi":

        language_instruction = """
    IMPORTANT LANGUAGE RULE

    Reply ONLY in Hindi (Devanagari).

    Never use English.

    Never use Hinglish.

    Even if the user asks in English,
    reply only in Hindi.

    """

    else:

        language_instruction = """
    IMPORTANT LANGUAGE RULE

    Reply ONLY in English.

    Never use Hindi.

    Never use Hinglish.

    Even if the user asks in Hindi,
    reply only in English.

    """

    if request.topic_name != "All Topics":

        if request.topic_name == "Cybercrime":
            topic_rules = """
    IMPORTANT RULES

    You MUST behave only as an expert of Cybercrime.

    Answer ONLY about:

    • Online Fraud
    • UPI Fraud
    • Banking Fraud
    • OTP Scam
    • Digital Arrest
    • Hacking
    • Social Media Crime
    • Email Scam
    • QR Scam
    • Cyber Laws
    • IT Act

    Never answer:

    • Traffic Laws
    • Criminal Law
    • General Questions

    If the question is outside Cybercrime,
    politely tell the user to switch the Topic Lock.
    """

        elif request.topic_name == "Traffic & Motor Vehicle":
            topic_rules = """
    IMPORTANT RULES

    You MUST behave only as an expert of Traffic Laws.

    Answer ONLY about:

    • Driving Licence
    • Vehicle Registration
    • Challan
    • Helmet
    • Seat Belt
    • Road Safety
    • MV Act
    • Accidents

    Never answer:

    • Cybercrime
    • Criminal Law
    • General Questions

    If the question is outside Traffic Laws,
    politely tell the user to switch the Topic Lock.
    """

        elif request.topic_name == "Criminal Law (BNS & IT Act)":
            topic_rules = """
    IMPORTANT RULES

    You MUST behave only as an expert of Criminal Law.

    Answer ONLY about:

    • BNS
    • FIR
    • Arrest
    • Bail
    • Court
    • Evidence
    • Theft
    • Murder
    • Assault
    • Cheating
    • IT Act

    Never answer:

    • Cybercrime
    • Traffic Laws
    • General Questions

    If the question is outside Criminal Law,
    politely tell the user to switch the Topic Lock.
    """

        topic_lock_instruction = f"""
    Current Topic Lock:
    {request.topic_name}

    {topic_rules}

    Never answer outside the locked topic.

    Never ignore Topic Lock.

    Use ONLY the retrieved context.

    {persona_instruction}
    """
    else:
        topic_lock_instruction = ""
    
    print("=" * 60)
    print("request.language =", request.language)
    print("language =", language)
    print("language_instruction =")
    print(language_instruction)
    print("=" * 60)
    
    messages = [
    {
        "role": "system",
        "content": f"""
You are NyayaAI, a legal awareness assistant.

{language_instruction}

{topic_lock_instruction}

IMPORTANT RULES:

1. Use ONLY the retrieved context.
2. Never invent legal facts.
3. Never answer outside the locked topic.
4. Give complete and detailed answers.
5. Follow the selected language STRICTLY.
6. Never mix Hindi and English.
7. If the selected language is English, answer ONLY in English.
8. If the selected language is Hindi, answer ONLY in Hindi (Devanagari script).
9. Never answer in Hinglish.
10. Use a professional tone.

ANSWER FORMAT:

- Direct answer first
- Then step-by-step explanation
- Highlight important facts
- End with action steps or helpline if relevant

Context:
{context}
"""
    }
]
    # Sirf recent conversation bhejo (last 2 user + 2 assistant)
    recent_history = history[-4:]

    for h in recent_history:
        if h.role in ["user", "assistant"]:
            messages.append({
                "role": h.role,
                "content": h.message
            })

    # Current question
    messages.append({
        "role": "user",
        "content": request.message
    })

    try:
        # completion = groq_client.chat.completions.create(
        #     model=os.getenv("GROQ_MODEL"),
        #     messages=messages,
        #     max_tokens=1500
        # )

        # ai_response = clean_llm_response(completion.choices[0].message.content)
        
        ai_response = ask_llm(messages)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"LLM Error: {str(e)}"
        )

    db.add(models.ChatHistory(
        session_id=request.session_id, role="user", message=request.message))
    db.add(models.ChatHistory(
        session_id=request.session_id, role="assistant", message=ai_response))
    db.commit()

    return {"session_id": request.session_id, "response": ai_response}

@app.delete("/session/{session_id}")
def delete_session(
    session_id: str,
    db: DBSession = Depends(get_db)
):

    session = (
        db.query(models.Session)
        .filter(models.Session.session_id == session_id)
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    db.query(models.ChatHistory)\
        .filter(
            models.ChatHistory.session_id == session_id
        )\
        .delete()

    db.query(models.Session)\
        .filter(
            models.Session.session_id == session_id
        )\
        .delete()

    db.commit()

    return {
        "message": "Session deleted successfully"
    }


# ── Document / Photo Upload + Analysis ────────────────
# User FIR copy, traffic challan, legal notice, ya kisi
# bhi document/photo ka upload karta hai, AI usko explain
# karta hai legal context ke saath (RAG knowledge base se
# relevant sections/acts bhi jod ke).
@app.post("/chat/upload", response_model=schemas.DocumentAnalysisResponse)
def chat_upload(
    session_id: str = Form(...),
    message: Optional[str] = Form(None),
    language: Optional[str] = Form("English"),
    file: UploadFile = File(...),
    db: DBSession = Depends(get_db),
):
    file_bytes = file.file.read()

    # ── Step 1: File validate karo (type + size) ──────
    try:
        file_kind = validate_file(file.filename, file_bytes)  # "image" ya "pdf"
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # ── Step 2: Session ensure karo ───────────────────
    session = db.query(models.Session)\
        .filter(models.Session.session_id == session_id).first()
    if not session:
        session = models.Session(
            session_id=session_id,
            title=f"📎 {file.filename}"
        )
        db.add(session)
    elif session.title == "New Chat":
        session.title = f"📎 {file.filename}"

    history = db.query(models.ChatHistory)\
        .filter(models.ChatHistory.session_id == session_id)\
        .order_by(models.ChatHistory.id.asc()).all()

    language_clean = (language or "English").strip().lower()
    lang_line = (
        "Hindi (Devanagari script) mein jawab do."
        if language_clean == "hindi"
        else "Reply in clear English."
    )

    user_note = message.strip() if message else ""
    user_question_for_history = (
        user_note if user_note else f"[Uploaded document: {file.filename}]"
    )

    system_prompt = f"""Tum NyayaAI ho — ek expert legal awareness assistant jo
cybercrime, traffic laws, aur criminal law (BNS & IT Act) mein specialize karta hai.

User ne ek document/photo upload ki hai (jaise FIR copy, traffic challan,
e-challan, court notice, bank fraud SMS/email screenshot, legal notice, etc.)
Tumhara kaam hai is document ko carefully analyze karna aur user ko
simple, clear language mein samjhana:

1. Document kis type ka hai (challan / FIR / notice / fraud message / etc.) — pehchaano
2. Usme jo important details hain (amount, date, section/act, deadline, sender,
   case number, etc.) unko clearly list karo
3. Iska legal matlab kya hai — konsa law/section apply hota hai
4. User ko kya karna chahiye — practical next steps (kahan complaint karein,
   kitne din mein jawab dena hai, fine kitna hai, appeal ka process, etc.)
5. Agar ye kisi scam/fraud jaisa lagta hai (jaise fake digital arrest notice,
   fake challan link, phishing message) to SAAF SAAF warn karo — koi bhi
   real government agency WhatsApp/SMS se directly paisa nahi maangti aur
   digital arrest jaisi koi legal process exist nahi karti.

IMPORTANT:
- Agar image/text clearly nahi padh paye to wahi bolo, guess mat karo
- Numbers, dates, amounts ko bold karke highlight karo
- {lang_line}
- End mein agar relevant ho to helpline number ya next-step suggest karo
  (Cybercrime: 1930, Traffic: 1073, NALSA Free Legal Aid: 15100)

{f"User ka extra sawal/context: {user_note}" if user_note else ""}"""

    try:
        if file_kind == "image":
            data_url = encode_image_to_data_url(file.filename, file_bytes)
            vision_messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": system_prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ]
            completion = groq_client.chat.completions.create(
                model=GROQ_VISION_MODEL,
                messages=vision_messages,
                max_tokens=4000,
                temperature=0.2,
            )

            ai_response = clean_llm_response(
                completion.choices[0].message.content
            )


        else:  # PDF
            try:
                extracted_text = extract_text_from_pdf(file_bytes)
                print("=" * 60)
                print("PDF TEXT LENGTH:", len(extracted_text))
                print("=" * 60)
                print(extracted_text[:1000])
                print("=" * 60)
                
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

            # ── RAG: extracted text se relevant legal context dhundo ──
            # (README promise karta hai ki document upload pe bhi
            # knowledge-base se relevant sections/acts jode jaate hain —
            # purana code yahan RAG call karta hi nahi tha, isliye
            # sections/fines kabhi-kabhi LLM ki general knowledge se
            # aate the jo exact/accurate nahi hote)
            upload_context = ""
            try:
                doc_query_embedding = embedding_model.encode(
                    [extracted_text[:2500]] 
                ).tolist()
                doc_results = collection.query(
                    query_embeddings=doc_query_embedding,
                    n_results=3,
                )
                doc_docs = doc_results.get("documents", [])
                if doc_docs and len(doc_docs[0]) > 0:
                    upload_context = "\n\n".join(doc_docs[0][:3])
            except Exception:
                # RAG fail ho jaye to bhi document analysis rukna nahi chahiye —
                # LLM general knowledge se hi answer de dega, just less precise
                upload_context = ""

            # text_messages = [
            #     {
            #         "role": "system",
            #         "content": (
            #             system_prompt
            #             + (
            #                 f"\n\nRelevant legal knowledge base context "
            #                 f"(use exact numbers/sections from here jahan applicable ho):\n{upload_context}"
            #                 if upload_context else ""
            #             )
            #         ),
            #     },
            #     {
            #         "role": "user",
            #         "content": f"Document ka extracted text:\n\n{extracted_text}",
            #     },
            # ]
            # completion = groq_client.chat.completions.create(
            #     model=os.getenv("GROQ_MODEL"),
            #     messages=text_messages,
            #     max_tokens=1500,
            # )
            # ai_response = clean_llm_response(completion.choices[0].message.content)
            # ai_response = ask_llm(text_messages)
            MAX_PDF_TEXT = 6000   # Approx. 5–6 pages of text

            pdf_text = extracted_text[:MAX_PDF_TEXT]

            text_messages = [
                {
                    "role": "system",
                    "content": (
                        system_prompt
                        + (
                            f"\n\nRelevant legal knowledge base context:\n{upload_context}"
                            if upload_context else ""
                        )
                    ),
                },
                {
                    "role": "user",
                    "content": f"Document ka extracted text:\n\n{pdf_text}",
                },
            ]
            print("Sending to Groq...")
            print(text_messages[1]["content"][:1000])
            ai_response = ask_llm(text_messages)
            
            print("=" * 60)
            print("AI RESPONSE:")
            print(ai_response)
            print("=" * 60)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Document Analysis Error: {str(e)}"
        )

    # ── Step 3: History save karo ──────────────────────
    db.add(models.ChatHistory(
        session_id=session_id,
        role="user",
        message=user_question_for_history,
        attachment_name=file.filename,
    ))
    db.add(models.ChatHistory(
        session_id=session_id,
        role="assistant",
        message=ai_response,
    ))
    db.commit()

    return {
        "session_id": session_id,
        "response": ai_response,
        "filename": file.filename,
        "file_type": file_kind,
    }

    
    
    






