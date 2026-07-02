import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.settings import settings
from processing.extractor import Extractor
from processing.chunker import Chunker
from processing.metadata import MetadataManager
from database.sync import DatabaseSync
from embeddings.encoder import DocumentEncoder
from vector_store.store import FaissStore
from vector_store.bm25_store import BM25Store

def run_ingestion(docx_path: str, version_id: str):
    print("=== Phase 1: Database Sync (SQL) ===")
    db_sync = DatabaseSync()
    db_sync.sync_document(docx_path, version_id)

    print("\n=== Phase 2: Hierarchical Chunking ===")
    extractor = Extractor(docx_path)
    elements = extractor.extract()
    chunks = Chunker.chunk_document(elements, version_id)
    print(f"Generated {len(chunks)} text chunks.")

    print("\n=== Phase 3: Metadata Storage ===")
    meta_manager = MetadataManager()
    meta_manager.save_metadata(chunks)
    print("Metadata populated in metadata.db.")

    print("\n=== Phase 4: Dense Indexing (FAISS) ===")
    encoder = DocumentEncoder()
    chunk_texts = [chunk.text for chunk in chunks]
    vectors = encoder.encode(chunk_texts)
    
    faiss_store = FaissStore()
    faiss_store.clear()
    faiss_store.add(vectors, [chunk.chunk_index for chunk in chunks])
    faiss_store.save()
    print("FAISS index populated and saved.")

    print("\n=== Phase 5: Sparse Indexing (BM25) ===")
    bm25_store = BM25Store()
    bm25_store.clear()
    bm25_store.index_chunks(chunks)
    print("BM25 index populated and saved.")
    
    print("\nIngestion pipeline completed successfully.")

if __name__ == "__main__":
    docx_file = os.path.join(settings.VERSIONS_DIR, "Synthetic manual_Boeing_737-800_Maintenance_1.docx")
    run_ingestion(docx_file, "v1")
