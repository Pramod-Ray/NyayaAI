# ============================================
# NyayaAI — Knowledge Base Package
# This file makes knowledge_base folder a Python package
# Allows importing like:
# from ai.knowledge_base.embeddings import get_embeddings
# from ai.knowledge_base.vector_store import store_chunks
# ============================================

from ai.knowledge_base.embeddings import get_embeddings
from ai.knowledge_base.vector_store import store_chunks, query_knowledge_base
