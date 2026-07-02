from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel,Field 


class ContentType(str, Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    STEP = "step"
    WARNING = "warning"
    CAUTION = "caution"
    NOTE = "note"
    TABLE_LOOKUP = "table_lookup"
    TABLE_NARRATIVE = "table_narrative"
    
    
class ProcedurePhase(str,Enum):
    PREPARATION = "preparation"
    EXECUTION = "execution"
    VERIFICATION = "verification"
    UNKNOWN = "unknown"
    
class DocumentElement(BaseModel):
    element_index: int
    content_type: ContentType
    text: str
    heading_level: Optional[str] = None
    ata_code: Optional[str] = None
    chapter: Optional[str] = None
    section: Optional[str] = None
    subsection: Optional[str] = None
    style_name: Optional[str] = None
    raw_xml: Optional[str] = None
    table_data: Optional[list[list[str]]] = None
    
    
class Chunk(BaseModel):
    chunk_id: str
    version_id: str
    chapter: Optional[str] = None
    ata_code: Optional[str] = None
    section: Optional[str] = None
    subsection: Optional[str] = None
    heading: Optional[str] = None
    content_type: ContentType = ContentType.PARAGRAPH
    procedure_phase: ProcedurePhase = ProcedurePhase.UNKNOWN
    has_warning: bool = False
    has_caution: bool = False
    step_numbers: list[str] = Field(default_factory=list)
    effectivity: Optional[str] = None
    revision: Optional[str] = None
    related_procedures: list[str] = Field(default_factory=list)
    chunk_index: int = 0
    text: str = ""
    
class VersionEntry(BaseModel):
    version_id: str
    filename: str
    created_at: str
    parent_id: Optional[str]
    description: str = ""
    is_active: bool = False