import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import docx
from processing.extractor import Extractor, iter_block_items

def dump_all_tables():
    doc = docx.Document("data/versions/Synthetic manual_Boeing_737-800_Maintenance_1.docx")
    table_idx = 0
    current_chapter = None
    for block in iter_block_items(doc):
        if isinstance(block, docx.text.paragraph.Paragraph):
            style_name = block.style.name if block.style else ""
            if style_name.startswith("Heading 1"):
                current_chapter = block.text.strip()
        elif isinstance(block, docx.table.Table):
            table_idx += 1
            if len(block.rows) == 1 and len(block.columns) == 1:
                continue
            
            # get all text
            text_content = "\n".join([" | ".join([cell.text.strip() for cell in row.cells]) for row in block.rows])
            
            lookup_keywords = ["torque", "ppe", "hazmat", "interval", "zone"]
            is_lookup = any(kw in text_content.lower() for kw in lookup_keywords) or (current_chapter and "appendix a" in current_chapter.lower())
            
            if is_lookup:
                print(f"\n==============================")
                print(f"Table {table_idx} in Chapter: {current_chapter}")
                print(f"Headers: {[cell.text.strip() for cell in block.rows[0].cells]}")
                print(f"Sample Row: {[cell.text.strip() for cell in block.rows[1].cells] if len(block.rows) > 1 else 'None'}")
                print(f"Rows count: {len(block.rows)}")

if __name__ == "__main__":
    dump_all_tables()
