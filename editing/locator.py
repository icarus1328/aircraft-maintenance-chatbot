import docx
from typing import Optional, Tuple
from docx.text.paragraph import Paragraph
from docx.table import Table

class DocumentLocator:
    @staticmethod
    def find_paragraph_by_id(doc: docx.document.Document, paragraph_idx: int) -> Optional[Paragraph]:
        """Finds paragraph by its 0-based sequential index in doc.paragraphs."""
        if 0 <= paragraph_idx < len(doc.paragraphs):
            return doc.paragraphs[paragraph_idx]
        return None

    @staticmethod
    def find_table_by_id(doc: docx.document.Document, table_idx: int) -> Optional[Table]:
        """Finds table by its 0-based sequential index in doc.tables."""
        if 0 <= table_idx < len(doc.tables):
            return doc.tables[table_idx]
        return None

    @staticmethod
    def find_step_paragraph(doc: docx.document.Document, section_title: str, step_num: str) -> Optional[Paragraph]:
        """
        Locates a specific numbered step within a section.
        Iterates paragraphs, finds the section heading, then looks for the step number (e.g. '1.').
        """
        in_section = False
        target_step_prefix = f"{step_num}."
        
        for p in doc.paragraphs:
            text = p.text.strip()
            style_name = p.style.name if p.style else ""
            
            # Check if entering section
            if style_name.startswith("Heading") and section_title.lower() in text.lower():
                in_section = True
                continue
                
            # If we hit another heading of same or higher level, we exited the section
            if in_section and style_name.startswith("Heading"):
                # Check if it's Heading 1 or Heading 2 (outer sections)
                if style_name in ("Heading 1", "Heading 2"):
                    break
            
            if in_section and text.startswith(target_step_prefix):
                return p
                
        return None

    @staticmethod
    def find_section_end_paragraph(doc: docx.document.Document, section_title: str) -> Tuple[Optional[Paragraph], int]:
        """
        Finds the last paragraph of a section (Heading 2 or 3) to allow appending content.
        Returns (paragraph, index) of the last paragraph in that section.
        """
        start_idx = -1
        end_idx = -1
        
        # 1. Find section start
        for idx, p in enumerate(doc.paragraphs):
            style_name = p.style.name if p.style else ""
            if style_name.startswith("Heading") and section_title.lower() in p.text.strip().lower():
                start_idx = idx
                break
                
        if start_idx == -1:
            return None, -1
            
        # 2. Find next heading at same or higher level to locate end of section
        start_style = doc.paragraphs[start_idx].style.name # e.g. Heading 2
        for idx in range(start_idx + 1, len(doc.paragraphs)):
            p = doc.paragraphs[idx]
            style_name = p.style.name if p.style else ""
            if style_name.startswith("Heading"):
                # If Heading level is same or higher (numerically lower level means higher heading)
                # E.g. Heading 2 -> Heading 2 or Heading 1 exits.
                if style_name <= start_style:
                    end_idx = idx - 1
                    break
                    
        if end_idx == -1:
            end_idx = len(doc.paragraphs) - 1
            
        # Find the last non-empty paragraph in this range
        for idx in range(end_idx, start_idx, -1):
            if doc.paragraphs[idx].text.strip():
                return doc.paragraphs[idx], idx
                
        return doc.paragraphs[start_idx], start_idx
