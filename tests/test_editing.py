import os
import sys
import shutil
import docx
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from versioning.manager import VersionManager
from versioning.validator import DocumentValidator
from editing.operations import InsertWarning, ReplaceStep, UpdateTableCell
from editing.validator import EditValidator
from config.settings import settings

def test_editing_workflow():
    vm = VersionManager()
    
    # 1. Fetch current active version docx
    active_docx_path = vm.get_active_docx_path()
    print(f"Active version docx path: {active_docx_path}")
    
    # Create a temporary copy to apply edits
    temp_docx_path = os.path.join(settings.DATA_DIR, "temp_edits.docx")
    shutil.copy(active_docx_path, temp_docx_path)
    
    try:
        # 2. Define operations
        # Let's insert a warning after paragraph 10
        op1 = InsertWarning(
            after_paragraph_id=20,
            warning_text="FLAMMABLE LIQUID. Keep away from ignition sources during maintenance.",
            section="1.5 Hazardous Materials",
            description="Added flammable warning for hazmat handling"
        )
        
        # Let's replace Step 1 in Section 5.2.1
        op2 = ReplaceStep(
            section="5.2.1 Tire Pressure Servicing",
            step_number="1",
            new_text="Allow the tire to cool for at least 3 hours (increased from 2 hours for safety) after the last landing.",
            description="Increased tire cooling time to 3 hours"
        )
        
        # Let's update table cell: Table 116 (Hydraulic Torque), row 1, col 1 (Aluminum 1/4 inch torque range)
        # Table index: 116 is in Appendix A.2
        # Let's find table ID. The dump tables output listed Table 116.
        # But wait! In docx.Document, Table 116 is at table index?
        # Let's look up Table 116's index.
        # Let's find it by loading document and searching.
        doc = docx.Document(temp_docx_path)
        table_idx = -1
        for idx, t in enumerate(doc.tables):
            # Check headers
            first_cell = t.rows[0].cells[0].text.strip()
            if "Tube OD" in first_cell:
                table_idx = idx
                break
        
        if table_idx == -1:
            raise ValueError("Could not find Hydraulic Torque table by header.")
            
        print(f"Found Hydraulic Torque table at index {table_idx}")
        
        op3 = UpdateTableCell(
            table_id=table_idx,
            row=1,
            col=1,
            new_value="45 – 70 (updated)",
            section="Appendix A.2",
            description="Updated aluminum torque for 1/4 inch tube"
        )
        
        # 3. Pre-edit validations
        print("Running pre-edit validations...")
        EditValidator.validate_insert_warning(temp_docx_path, op1.after_paragraph_id)
        EditValidator.validate_replace_step(temp_docx_path, op2.section, op2.step_number)
        EditValidator.validate_update_table_cell(temp_docx_path, op3.table_id, op3.row, op3.col)
        print("Pre-edit validations passed.")
        
        # 4. Apply operations
        print("Applying operations to temp docx...")
        doc = docx.Document(temp_docx_path)
        op1.apply(doc)
        op2.apply(doc)
        op3.apply(doc)
        doc.save(temp_docx_path)
        print("Operations applied and saved.")
        
        # 5. Pre-commit validation
        print("Running pre-commit validation...")
        DocumentValidator.validate_docx(temp_docx_path)
        print("Pre-commit validation passed.")
        
        # 6. Commit version upgrade
        print("Upgrading version in manifest...")
        changes = [
            {"operation": "InsertWarning", "description": op1.description, "section": op1.section},
            {"operation": "ReplaceStep", "description": op2.description, "section": op2.section},
            {"operation": "UpdateTableCell", "description": op3.description, "section": op3.section}
        ]
        
        vm.upgrade(
            new_version_id="v3",
            author="maintenance_lead",
            description="Applied safety updates to warnings, cooling times, and torque specs.",
            changes=changes,
            temp_docx_path=temp_docx_path
        )
        
        print(f"Active version is now: {vm.get_active_version_id()}")
        
    finally:
        # Cleanup
        if os.path.exists(temp_docx_path):
            os.remove(temp_docx_path)

if __name__ == "__main__":
    test_editing_workflow()
