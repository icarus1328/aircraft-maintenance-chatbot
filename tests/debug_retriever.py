import sys
import os
import sqlite3
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.settings import settings
from embeddings.encoder import DocumentEncoder
from vector_store.store import FaissStore
from vector_store.bm25_store import BM25Store

def debug():
    query = "Skydrol handling warning or PPE requirements"
    print("1. Initializing components...")
    encoder = DocumentEncoder()
    faiss_store = FaissStore()
    bm25_store = BM25Store()
    
    print("2. Encoding query...")
    query_vector = encoder.encode([query])[0]
    print(f"   Query vector shape: {query_vector.shape}")
    
    print("3. Searching FAISS...")
    dense_results = faiss_store.search(query_vector, top_k=6)
    print(f"   FAISS results: {dense_results}")
    
    print("4. Searching BM25...")
    sparse_results = bm25_store.search(query, top_k=6)
    print(f"   BM25 results: {sparse_results}")
    
    print("5. Connecting to metadata DB...")
    with sqlite3.connect(settings.METADATA_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM chunk_metadata")
        count = cursor.fetchone()[0]
        print(f"   Metadata DB chunk count: {count}")

if __name__ == "__main__":
    debug()
