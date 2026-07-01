import sqlite3
import json
from typing import List, Dict, Any, Tuple
from config.settings import settings
from embeddings.encoder import DocumentEncoder
from vector_store.store import FaissStore
from vector_store.bm25_store import BM25Store
from processing.models import Chunk, ContentType, ProcedurePhase

class HybridRetriever:
    def __init__(self):
        self.encoder = DocumentEncoder()
        self.faiss_store = FaissStore()
        self.bm25_store = BM25Store()
        self.metadata_db_path = settings.METADATA_DB_PATH

    def search(self, query: str, top_k: int = 5, k_constant: int = 60) -> List[Dict[str, Any]]:
        """
        Retrieves top_k chunks by performing dense and sparse search and fusing them using
        Reciprocal Rank Fusion (RRF).
        """
        # 1. Perform Dense Search
        query_vector = self.encoder.encode([query])[0]
        dense_results = self.faiss_store.search(query_vector, top_k=top_k * 3) # search more to merge
        
        # 2. Perform Sparse Search
        sparse_results = self.bm25_store.search(query, top_k=top_k * 3)

        # 3. Apply Reciprocal Rank Fusion (RRF)
        # dense_results and sparse_results are lists of (chunk_index, score)
        rrf_scores: Dict[int, float] = {}

        # Dense rank processing
        for rank, (chunk_idx, _) in enumerate(dense_results, start=1):
            rrf_scores[chunk_idx] = rrf_scores.get(chunk_idx, 0.0) + 1.0 / (k_constant + rank)

        # Sparse rank processing
        for rank, (chunk_idx, _) in enumerate(sparse_results, start=1):
            rrf_scores[chunk_idx] = rrf_scores.get(chunk_idx, 0.0) + 1.0 / (k_constant + rank)

        # Sort chunk indices by fused RRF score descending
        fused_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        if not fused_results:
            return []

        # 4. Fetch chunk metadata from SQLite for selected chunk indices
        retrieved_chunks = []
        with sqlite3.connect(self.metadata_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Query sequentially or with IN
            placeholders = ",".join(["?"] * len(fused_results))
            chunk_indices = [idx for idx, _ in fused_results]
            
            cursor.execute(
                f"SELECT * FROM chunk_metadata WHERE chunk_index IN ({placeholders})",
                chunk_indices
            )
            rows = cursor.fetchall()
            
            # Map by chunk_index for correct ordering
            rows_by_idx = {row["chunk_index"]: row for row in rows}
            
            for idx, rrf_score in fused_results:
                row = rows_by_idx.get(idx)
                if row:
                    chunk_dict = dict(row)
                    # Deserialize JSON lists
                    chunk_dict["step_numbers"] = json.loads(chunk_dict["step_numbers"])
                    chunk_dict["related_procedures"] = json.loads(chunk_dict["related_procedures"])
                    chunk_dict["rrf_score"] = rrf_score
                    retrieved_chunks.append(chunk_dict)

        return retrieved_chunks
