# ============================================
# NyayaAI — Retriever
# Takes user question as input
# Searches ChromaDB for similar chunks
# Returns top matching chunks with metadata
# If no good match found — returns empty list
# ============================================

from ai.knowledge_base.vector_store import query_knowledge_base
from ai.config import TOP_K_RESULTS
import logging

log = logging.getLogger(__name__)

# if similarity distance is above this threshold
# chunk is considered not relevant enough
# cosine distance — lower means more similar
# 0 = exact match, 1 = unrelated, 2 = opposite
# 1.5 was too loose — almost everything passed through
# 0.9 keeps genuinely relevant matches while filtering noise
SIMILARITY_THRESHOLD = 0.9


def retrieve_chunks(user_question, topic_filter=None):
    # search ChromaDB for chunks similar to user question
    # topic_filter = optional list of category names
    #   (from TOPIC_GROUPS in config.py) — when given,
    #   only chunks belonging to those categories are searched
    chunks = query_knowledge_base(
        query_text      = user_question,
        top_k           = TOP_K_RESULTS,
        category_filter = topic_filter
    )

    # filter out chunks that are not similar enough
    # prevents hallucination from irrelevant chunks
    relevant_chunks = [
        chunk for chunk in chunks
        if chunk["distance"] < SIMILARITY_THRESHOLD
    ]

    if not relevant_chunks:
        # no relevant chunks found in knowledge base
        log.info(f"⚠️ No relevant chunks found for: {user_question}")
        return []

    log.info(f"✅ Found {len(relevant_chunks)} relevant chunks")
    return relevant_chunks
