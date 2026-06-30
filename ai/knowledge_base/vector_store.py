# ============================================
# NyayaAI — Vector Store
# Stores chunks and their vectors in ChromaDB
# ChromaDB is a local vector database
# Handles storing and searching of chunks
# ============================================

import chromadb
from ai.config import CHROMA_DIR, COLLECTION_NAME
from ai.knowledge_base.embeddings import get_embeddings, get_single_embedding
import logging

log = logging.getLogger(__name__)


def get_collection():
    # create ChromaDB client — stores data locally
    # PersistentClient saves data to disk permanently
    # data survives even after program restarts
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # get or create collection — like a table in database
    # if collection exists — returns existing one
    # if not — creates new one
    collection = client.get_or_create_collection(
        name     = COLLECTION_NAME,
        metadata = {"hnsw:space": "cosine"}  # cosine similarity for search
    )
    return collection


def store_chunks(chunks):
    # stores all chunks with their vectors in ChromaDB
    # chunks = list of dicts from chunker.py
    collection = get_collection()

    # prepare data for ChromaDB
    ids        = []  # unique id for each chunk
    texts      = []  # raw text of each chunk
    metadatas  = []  # category source info etc

    for chunk in chunks:
        ids.append(chunk["chunk_id"])
        texts.append(chunk["text"])
        metadatas.append({
            "category"  : chunk["category"],
            "source"    : chunk["source"],
            "source_key": chunk["source_key"],
            "file_type" : chunk["file_type"],
            "word_count": str(chunk["word_count"])
        })

    # generate vectors for all chunk texts
    embeddings = get_embeddings(texts)

    # store everything in ChromaDB in one call
    # upsert = update if exists, insert if not
    # prevents duplicate chunks on re-run
    collection.upsert(
        ids        = ids,
        documents  = texts,
        embeddings = embeddings,
        metadatas  = metadatas
    )

    log.info(f"✅ Stored {len(chunks)} chunks in ChromaDB")
    return len(chunks)


def query_knowledge_base(query_text, top_k=3, category_filter=None):
    # searches ChromaDB for chunks similar to query
    # query_text = user question as string
    # top_k = how many chunks to return
    # category_filter = optional list of category names
    #   when given, ChromaDB only searches chunks whose
    #   "category" metadata is in this list (topic-lock filter)
    collection = get_collection()

    # convert user query to vector
    query_embedding = get_single_embedding(query_text)

    # build optional where clause for category filtering
    where_clause = None
    if category_filter:
        where_clause = {"category": {"$in": category_filter}}

    # search ChromaDB — returns most similar chunks
    results = collection.query(
        query_embeddings = [query_embedding],
        n_results        = top_k,
        where            = where_clause,
        include          = ["documents", "metadatas", "distances"]
    )

    # format results into clean list of dicts
    chunks = []
    for i in range(len(results["documents"][0])):
        chunks.append({
            "text"    : results["documents"][0][i],
            "category": results["metadatas"][0][i]["category"],
            "source"  : results["metadatas"][0][i]["source"],
            "distance": results["distances"][0][i]
        })

    log.info(f"✅ Retrieved {len(chunks)} chunks for query")
    return chunks


def get_collection_count():
    # returns total number of chunks stored in ChromaDB
    # useful for verifying ingestion worked correctly
    collection = get_collection()
    count      = collection.count()
    log.info(f"📊 Total chunks in knowledge base: {count}")
    return count
