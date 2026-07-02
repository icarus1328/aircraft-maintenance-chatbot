import os
import sqlite3
from typing import List, Dict, Any
from config.settings import settings
from llm.client import GroqClient
from llm.prompts import NL_TO_SQL_SYSTEM_PROMPT

class SQLRetriever:
    def __init__(self):
        self.db_path = settings.DB_PATH
        self.client = GroqClient()

    def retrieve(self, query: str) -> Dict[str, Any]:
        """
        Translates query to SQL using Groq, executes it, and returns the query text
        and raw results (list of dictionaries).
        """
        # 1. Translate NL to SQL
        try:
            sql_query = self.client.generate(
                system_prompt=NL_TO_SQL_SYSTEM_PROMPT,
                user_prompt=f"Translate this query to SQLite: '{query}'",
                temperature=0.0
            )
        except Exception as e:
            print(f"Failed to generate SQL query: {str(e)}")
            return {"query": "", "results": [], "error": str(e)}

        sql_query = sql_query.strip()
        # Clean markdown code blocks if the LLM wrapped it despite instructions
        if sql_query.startswith("```"):
            sql_query = sql_query.split("\n")[1:-1]
            sql_query = "\n".join(sql_query).strip()
            if sql_query.lower().startswith("sql"):
                sql_query = sql_query[3:].strip()

        if sql_query.upper() == "NONE" or not sql_query:
            return {"query": "", "results": []}

        print(f"Executing SQL query: {sql_query}")
        
        # 2. Execute SQL query
        if not os.path.exists(self.db_path):
            return {"query": sql_query, "results": [], "error": "Database file not found."}

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(sql_query)
                rows = cursor.fetchall()
                results = [dict(row) for row in rows]
                return {"query": sql_query, "results": results}
        except Exception as e:
            print(f"SQL execution failed: {str(e)}")
            return {"query": sql_query, "results": [], "error": str(e)}
