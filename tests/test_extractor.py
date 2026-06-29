import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from processing.extractor import Extractor

def test_extraction():
    file_path = "data/versions/Synthetic manual_Boeing_737-800_Maintenance_1.docx"
    extractor = Extractor(file_path)
    elements = extractor.extract()
    
    print(f"Total elements extracted: {len(elements)}")
    
    warnings = [e for e in elements if e.content_type.value == "warning"]
    print(f"Total warnings found: {len(warnings)}")
    
    tables = [e for e in elements if e.content_type.value in ("table_lookup", "table_narrative")]
    print(f"Total tables found: {len(tables)}")
    
    print("\nFirst 10 elements:")
    for e in elements[:10]:
        print(f"[{e.content_type.value}] {e.text[:50]}... (Heading: {e.heading_level}, Sec: {e.section})")
        
if __name__ == "__main__":
    test_extraction()
