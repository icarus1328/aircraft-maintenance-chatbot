import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from retrieval.retriever import HybridRetriever

def verify_retrieval():
    retriever = HybridRetriever()
    queries = [
        "Skydrol handling warning or PPE requirements",
        "Engine-driven pump installation pressure line torque",
        "Corrosion Level 3 required actions",
        "ATA 32 landing gear wheel and tire pressure maintenance",
        "Lockout tagout LOTO procedures"
    ]
    
    for q in queries:
        print(f"\n==========================================")
        print(f"QUERY: {q}")
        results = retriever.search(q, top_k=2)
        print(f"Retrieved {len(results)} results:")
        for idx, res in enumerate(results):
            print(f"\n  Result {idx + 1} (Score: {res['rrf_score']:.4f}):")
            print(f"    Chunk ID: {res['chunk_id']}")
            print(f"    Section: {res['section']} | Subsection: {res['subsection']}")
            print(f"    Chapter: {res['chapter']}")
            print(f"    Has Warning: {res['has_warning']} | Has Caution: {res['has_caution']}")
            print(f"    ATA Code: {res['ata_code']} | Related: {res['related_procedures']}")
            print(f"    Text Preview:\n{res['text'][:300]}...")

if __name__ == "__main__":
    verify_retrieval()
