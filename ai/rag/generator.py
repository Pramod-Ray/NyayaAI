# ============================================
# NyayaAI — Generator
# Takes retrieved chunks and user question
# Sends both to Groq LLM
# Returns formatted answer with source info
# Handles out of scope questions gracefully
# ============================================

from groq import Groq
from ai.config import GROQ_API_KEY, GROQ_MODEL
import logging

log = logging.getLogger(__name__)

client = Groq(api_key=GROQ_API_KEY)

OUT_OF_SCOPE_MESSAGE = """I don't have specific information about this topic in my knowledge base.

For cybercrime related help:
📞 Helpline: 1930
🌐 Portal: www.cybercrime.gov.in
📱 Follow: @cyberdost on social media"""


def format_context(chunks):
    context_parts = []
    for i, chunk in enumerate(chunks):
        context_parts.append(
            f"[Source {i+1}: {chunk['source']}]\n"
            f"{chunk['text']}"
        )
    return "\n\n".join(context_parts)


# def build_prompt(user_question, context):
#     return f"""You are NyayaAI, a cybercrime awareness assistant for Indian citizens.
# Answer the user's question using ONLY the context provided below.

# STRICT RULES:
# 1. Only use information from the context below
# 2. Do NOT make up any information
# 3. If context does not have enough information — say so clearly
# 4. If the question involves a process or steps — ALWAYS format as numbered steps
# 5. If the question is simple — answer in 2 to 3 clear sentences
# 6. Do not use phrases like "according to the context" or "the document says"
# 7. Answer in a helpful and professional tone
# 8. Use bullet points or numbered lists wherever it makes the answer clearer




def build_prompt(user_question, context):
    return f"""You are NyayaAI, a legal awareness assistant for Indian citizens.
You have expertise in BOTH cybercrime awareness AND Indian traffic/motor vehicle laws.
Answer the user's question using ONLY the context provided below.

STRICT RULES:
1. Only use information from the context below
2. Do NOT make up any information
3. If context does not have enough information — say so clearly
4. If the question involves fines or penalties — ALWAYS mention the exact amount in rupees
5. If the question involves a process or steps — ALWAYS format as numbered steps
6. If the question is simple — answer in 2 to 3 clear sentences
7. Do not use phrases like "according to the context" or "the document says"
8. Answer in a helpful and professional tone
9. Use bullet points or numbered lists wherever it makes the answer clearer

CONTEXT:
{context}

USER QUESTION:
{user_question}

ANSWER:"""


def generate_answer(user_question, chunks, chat_history=None):  # ← chat_history add kiya
    if chat_history is None:
        chat_history = []

    # ── Messages list banao ───────────────────────────────
    messages = [
        {
            "role": "system",
            # "content": "You are NyayaAI, a helpful cybercrime awareness assistant for Indian citizens."
            "content": "You are NyayaAI, a helpful legal awareness assistant for Indian citizens covering both cybercrime and traffic/motor vehicle laws."
        }
    ]

    # ← Purani 5 chat history inject karo (context ke liye)
    messages += chat_history

    # ── Prompt banao (chunks mile ya nahi) ───────────────
    if chunks:
        context = format_context(chunks)
        prompt = build_prompt(user_question, context)
    else:
        log.info("⚠️ No chunks — using Groq general knowledge")
        prompt = f"""You are NyayaAI, a cybercrime awareness assistant for Indian citizens.
Answer the user's question about cybercrime, digital fraud, or online safety.

RULES:
1. Give helpful, accurate information about Indian cybercrime laws and safety
2. If the question involves a process or steps — ALWAYS format as numbered steps
3. If the question is simple — answer in 2 to 3 sentences
4. Mention helpline 1930 or cybercrime.gov.in where relevant
5. Use bullet points or numbered lists wherever it makes answer clearer
6. Professional and helpful tone

USER QUESTION:
{user_question}

ANSWER:"""

    # ← Naya user message (prompt ke saath) add karo
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.3,
        max_tokens=500
    )

    answer = response.choices[0].message.content.strip()
    best_chunk = chunks[0] if chunks else None

    return {
        "answer"  : answer,
        "source"  : best_chunk["source"] if best_chunk else "General Knowledge",
        "category": best_chunk["category"] if best_chunk else "Cybercrime Awareness",
        "found"   : True
    }
