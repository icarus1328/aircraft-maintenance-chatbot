import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import docx
from processing.extractor import Extractor, iter_block_items

def dump():
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
                # advisory
                continue
            print(f"\n--- Table {table_idx} in Chapter: {current_chapter} ---")
            print(f"Rows: {len(block.rows)}, Cols: {len(block.columns)}")
            for i in range(min(5, len(block.rows))):
                row = block.rows[i]
                print(f"Row {i}: {[cell.text.strip().replace('\n', ' ') for cell in row.cells]}")

if __name__ == "__main__":
    dump()
