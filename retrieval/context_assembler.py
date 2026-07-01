from typing import Dict, Any, List
from retrieval.retriever import HybridRetriever
from retrieval.sql_retriever import SQLRetriever

class ContextAssembler:
    def __init__(self):
        self.rag_retriever = HybridRetriever()
        self.sql_retriever = SQLRetriever()

    def assemble(self, query: str, top_k_rag: int = 5) -> Dict[str, Any]:
        """
        Retrieves from both SQL and RAG pathways and constructs the formatted
        prompts for the QA pipeline.
        """
        # 1. SQL retrieval
        sql_data = self.sql_retriever.retrieve(query)
        sql_rows = sql_data.get("results", [])
        sql_query = sql_data.get("query", "")

        # 2. RAG retrieval
        rag_chunks = self.rag_retriever.search(query, top_k=top_k_rag)

        # 3. Format SQL output
        sql_formatted = ""
        if sql_rows:
            sql_formatted = "### SQL Lookup Table Results\n"
            # Group by table name if multiple or just format them
            # Since the query normally targets one table, we just list rows
            for idx, row in enumerate(sql_rows):
                # Pull out metadata cols for header
                sec = row.pop("source_section", "Unknown")
                ver = row.pop("document_version", "Unknown")
                # Remaining columns are the actual data
                cols = ", ".join([f"{k}: {v}" for k, v in row.items() if k != "id"])
                sql_formatted += f"- Record {idx+1} [Source Section: {sec}, Version: {ver}]: {cols}\n"
        else:
            sql_formatted = "### SQL Lookup Table Results\nNo exact database lookup matches found.\n"

        # 4. Format RAG output
        rag_formatted = "### RAG Procedural Context Chunks\n"
        if rag_chunks:
            for idx, chunk in enumerate(rag_chunks):
                rag_formatted += f"#### Chunk {idx+1} [ID: {chunk['chunk_id']}, Chapter: {chunk['chapter']}, Section: {chunk['section']}, Subsection: {chunk['subsection']}]\n"
                rag_formatted += f"Text:\n{chunk['text']}\n\n"
        else:
            rag_formatted += "No procedural RAG matches found.\n"

        # 5. Assemble final user prompt
        user_prompt = f"""User Query: {query}

Please answer the user query based ONLY on the following context:

--- CONTEXT ---
{sql_formatted}

{rag_formatted}
--- END CONTEXT ---
"""
        return {
            "user_prompt": user_prompt,
            "sql_query": sql_query,
            "sql_results": sql_rows,
            "rag_chunks": rag_chunks
        }
