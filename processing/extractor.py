import re
from typing import List, Optional
import docx
from docx.document import Document as _Document
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph

from processing.models import DocumentElement, ContentType

def iter_block_items(parent):
    """
    Yield each paragraph and table child within *parent*, in document order.
    Each returned value is an instance of either Table or Paragraph.
    """
    if isinstance(parent, _Document):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    else:
        raise ValueError("Unsupported parent type")

    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)

class Extractor:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.doc = docx.Document(file_path)

    def extract(self) -> List[DocumentElement]:
        elements = []
        current_chapter = None
        current_section = None
        current_subsection = None
        current_ata = None
        
        element_idx = 0

        for block in iter_block_items(self.doc):
            if isinstance(block, Paragraph):
                text = block.text.strip()
                if not text:
                    continue
                
                style_name = block.style.name if block.style else ""
                
                # Determine ContentType and Update Hierarchies
                content_type = ContentType.PARAGRAPH
                heading_level = None
                
                if style_name.startswith("Heading"):
                    content_type = ContentType.HEADING
                    level = style_name.split()[-1]
                    heading_level = level
                    
                    if level == "1":
                        current_chapter = text
                        current_section = None
                        current_subsection = None
                        # Extract ATA code if present (e.g., "ATA 32" or "32-xx")
                        ata_match = re.search(r'ATA\s*(\d{2})', text, re.IGNORECASE)
                        if ata_match:
                            current_ata = ata_match.group(1)
                    elif level == "2":
                        current_section = text
                        current_subsection = None
                    elif level == "3":
                        current_subsection = text
                elif style_name.startswith("List Paragraph") or re.match(r'^(\d+\.|[a-zA-Z]\.)\s', text):
                    content_type = ContentType.STEP
                
                el = DocumentElement(
                    element_index=element_idx,
                    content_type=content_type,
                    text=text,
                    heading_level=heading_level,
                    ata_code=current_ata,
                    chapter=current_chapter,
                    section=current_section,
                    subsection=current_subsection,
                    style_name=style_name,
                    raw_xml=block._p.xml
                )
                elements.append(el)
                element_idx += 1
                
            elif isinstance(block, Table):
                # Check if it's a WARNING/CAUTION/NOTE single-cell table
                is_advisory = False
                if len(block.rows) == 1 and len(block.columns) == 1:
                    cell_text = block.rows[0].cells[0].text.strip()
                    upper_text = cell_text.upper()
                    if upper_text.startswith("WARNING"):
                        content_type = ContentType.WARNING
                        is_advisory = True
                    elif upper_text.startswith("CAUTION"):
                        content_type = ContentType.CAUTION
                        is_advisory = True
                    elif upper_text.startswith("NOTE"):
                        content_type = ContentType.NOTE
                        is_advisory = True
                        
                    if is_advisory:
                        el = DocumentElement(
                            element_index=element_idx,
                            content_type=content_type,
                            text=cell_text,
                            ata_code=current_ata,
                            chapter=current_chapter,
                            section=current_section,
                            subsection=current_subsection,
                        )
                        elements.append(el)
                        element_idx += 1
                        continue
                
                # Distinguish lookup vs narrative tables
                # Lookup tables have specific headers or are in specific sections
                raw_rows = []
                for row in block.rows:
                    raw_rows.append([cell.text.strip() for cell in row.cells])
                
                text_content = "\n".join([" | ".join(r) for r in raw_rows])
                
                # Heuristic: If headers contain "Torque", "PPE", "Hazmat", "Interval", "Zone", "Hazard" -> LOOKUP
                # Also, any table in Appendix A is a lookup table.
                header_text = " ".join(raw_rows[0]).lower() if raw_rows else ""
                lookup_keywords = ["torque", "ppe", "hazmat", "interval", "zone", "hazard"]
                
                is_lookup = any(kw in header_text for kw in lookup_keywords)
                is_appendix_a = (current_chapter and "appendix a" in current_chapter.lower())
                
                if is_lookup or is_appendix_a:
                    content_type = ContentType.TABLE_LOOKUP
                else:
                    content_type = ContentType.TABLE_NARRATIVE
                    
                el = DocumentElement(
                    element_index=element_idx,
                    content_type=content_type,
                    text=text_content,
                    ata_code=current_ata,
                    chapter=current_chapter,
                    section=current_section,
                    subsection=current_subsection,
                    table_data=raw_rows
                )
                elements.append(el)
                element_idx += 1

        return elements
