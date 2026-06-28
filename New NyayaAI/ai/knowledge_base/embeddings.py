# ============================================
# NyayaAI — Embeddings
# Converts text into vectors using
# sentence-transformers model
# Vectors are used for similarity search
# in ChromaDB knowledge base
# ============================================

from sentence_transformers import SentenceTransformer
from ai.config import EMBEDDING_MODEL
import logging

log = logging.getLogger(__name__)

# load embedding model once at module level
# loading is slow — doing it once saves time
# all-MiniLM-L6-v2 is fast, free, good quality
model = SentenceTransformer(EMBEDDING_MODEL)


def get_embeddings(texts):
    # texts = list of strings to convert to vectors
    # returns list of vectors — one per text
    # each vector is a list of 384 numbers
    # similar texts will have similar vectors
    log.info(f"🔢 Generating embeddings for {len(texts)} texts")
    embeddings = model.encode(
        texts,
        show_progress_bar=True,  # shows progress during encoding
        # convert_to_list=True     # returns plain list not numpy array
    )
    # log.info(f"✅ Embeddings generated — {len(embeddings)} vectors")
    # return embeddings
    embeddings = embeddings.tolist()
    log.info(f"✅ Embeddings generated — {len(embeddings)} vectors")
    return embeddings
    


def get_single_embedding(text):
    # converts single text string to vector
    # used in RAG retriever for user query
    embedding = model.encode(text)
    return embedding.tolist()
