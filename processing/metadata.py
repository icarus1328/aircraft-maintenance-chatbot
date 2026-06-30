import os
import sqlite3
import json
from typing import List, Optional
from config.settings import settings
from processing.models import Chunk

class MetadataManager:
    def __init__(self, db_path: str = settings.METADATA_DB_PATH):
        self.db_path = db_path

    def init_db(self):
        """Initializes the metadata SQLite database."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunk_metadata (
                    chunk_id TEXT PRIMARY KEY,
                    version_id TEXT,
                    chapter TEXT,
                    ata_code TEXT,
                    section TEXT,
                    subsection TEXT,
                    heading TEXT,
                    content_type TEXT,
                    procedure_phase TEXT,
                    has_warning INTEGER,
                    has_caution INTEGER,
                    step_numbers TEXT,
                    effectivity TEXT,
                    revision TEXT,
                    related_procedures TEXT,
                    chunk_index INTEGER,
                    text TEXT
                )
            """)
            conn.commit()

    def clear_db(self):
        """Clears all metadata rows."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM chunk_metadata")
            conn.commit()

    def save_metadata(self, chunks: List[Chunk]):
        """Saves a list of Chunk models to the metadata DB."""
        self.init_db()
        self.clear_db()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for chunk in chunks:
                cursor.execute(
                    """INSERT OR REPLACE INTO chunk_metadata 
                       (chunk_id, version_id, chapter, ata_code, section, subsection, heading, content_type, 
                        procedure_phase, has_warning, has_caution, step_numbers, effectivity, revision, 
                        related_procedures, chunk_index, text)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        chunk.chunk_id,
                        chunk.version_id,
                        chunk.chapter,
                        chunk.ata_code,
                        chunk.section,
                        chunk.subsection,
                        chunk.heading,
                        chunk.content_type.value,
                        chunk.procedure_phase.value,
                        1 if chunk.has_warning else 0,
                        1 if chunk.has_caution else 0,
                        json.dumps(chunk.step_numbers),
                        chunk.effectivity,
                        chunk.revision,
                        json.dumps(chunk.related_procedures),
                        chunk.chunk_index,
                        chunk.text
                    )
                )
            conn.commit()
            
    def get_metadata(self, chunk_id: str) -> Optional[dict]:
        """Retrieves metadata dict for a specific chunk_id."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chunk_metadata WHERE chunk_id = ?", (chunk_id,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                d["step_numbers"] = json.loads(d["step_numbers"])
                d["related_procedures"] = json.loads(d["related_procedures"])
                return d
        return None
