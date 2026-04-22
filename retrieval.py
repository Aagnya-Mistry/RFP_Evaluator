import time
import json
import hashlib
import os
import chromadb
from google import genai
from google.genai import types
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

# Initialize the new-style client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

CACHE_FILE = ".cache/uploaded_doc_embeddings.json"

# ── ChromaDB ───────────────────────────────────────────
def load_collection(db_path="./idobro_db"):
    chroma_client = chromadb.PersistentClient(path=db_path)
    return chroma_client.get_or_create_collection(name="idobro_knowledge")

# ── Embedding ──────────────────────────────────────────
def embed_text(text, task_type="RETRIEVAL_QUERY"):
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(task_type=task_type)
    )
    return result.embeddings[0].values

def embed_chunks_with_ratelimit(chunks, task_type="RETRIEVAL_QUERY"):
    """Embed a list of chunks with a 2s pause every 5 requests to stay under 5 req/min."""
    embeddings = []
    for i, chunk in enumerate(chunks):
        embeddings.append(embed_text(chunk, task_type=task_type))
        if i % 5 == 4:
            time.sleep(2)
    return embeddings

# ── Cache ──────────────────────────────────────────────
def get_file_hash(text):
    return hashlib.md5(text.encode()).hexdigest()

def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    with open(CACHE_FILE, "r") as f:
        return json.load(f)

def save_cache(cache):
    os.makedirs(".cache", exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

def get_or_embed_chunks(chunks, file_hash):
    """Return cached embeddings if available, else embed and cache them."""
    cache = load_cache()
    if file_hash in cache:
        return cache[file_hash]["embeddings"], True  # (embeddings, cache_hit)

    embeddings = embed_chunks_with_ratelimit(chunks, task_type="RETRIEVAL_QUERY")
    cache[file_hash] = {"embeddings": embeddings}
    save_cache(cache)
    return embeddings, False  # (embeddings, cache_hit)

# ── Chunking ───────────────────────────────────────────
def chunk_text(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=75,
        separators=["\n\n", "\n", ".", " "]
    )
    return splitter.split_text(text)

# ── Retrieval ──────────────────────────────────────────
def semantic_search(collection, query_embedding, top_k=20):
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    chunks = []
    for i, doc in enumerate(results["documents"][0]):
        chunks.append({
            "text": doc,
            "score": results["distances"][0][i],
            "filename": results["metadatas"][0][i]["filename"]
        })
    return chunks

def get_relevant_chunks(rfp_text, collection, top_k_retrieve=20, top_k_final=7):
    """
    Embeds the RFP query (single call), searches chromadb by cosine similarity,
    returns top_k_final chunks. Caches RFP chunk embeddings by file hash.
    """
    file_hash = get_file_hash(rfp_text)

    # Embed just the query text for chromadb search (1 API call)
    query_embedding = embed_text(rfp_text[:2000], task_type="RETRIEVAL_QUERY")
    time.sleep(1)  # small buffer after query embed before any further calls

    # Cosine similarity search in chromadb — no LLM involved
    chunks = semantic_search(collection, query_embedding, top_k=top_k_retrieve)

    return chunks[:top_k_final]

def get_relevant_chunks_with_cache(rfp_text, collection, top_k_retrieve=20, top_k_final=7):
    """
    Full version: chunks the RFP, caches those embeddings, then also does
    the query embed + chromadb search. Returns (relevant_chunks, cache_hit).
    Use this if you also want to store/reuse RFP chunk embeddings.
    """
    file_hash = get_file_hash(rfp_text)
    rfp_chunks = chunk_text(rfp_text)

    # Embed (or retrieve from cache) the RFP's own chunks
    _, cache_hit = get_or_embed_chunks(rfp_chunks, file_hash)

    # Embed query for chromadb search
    query_embedding = embed_text(rfp_text[:2000], task_type="RETRIEVAL_QUERY")
    time.sleep(1)

    # Cosine similarity search
    chunks = semantic_search(collection, query_embedding, top_k=top_k_retrieve)

    return chunks[:top_k_final], cache_hit
