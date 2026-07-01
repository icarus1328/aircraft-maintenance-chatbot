import os
import sys
import shutil
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from versioning.manager import VersionManager
from versioning.validator import DocumentValidator
from config.settings import settings

def test_versioning_flow():
    vm = VersionManager()
    
    print("\n1. Verification of Active Version ID:")
    active_id = vm.get_active_version_id()
    print(f"   Active Version ID: {active_id}")
    
    print("\n2. History Retrieval:")
    history = vm.get_history()
    for entry in history:
        print(f"   - {entry['version_id']} (Active: {entry['is_active']}, Original: {entry['is_original']}) description: {entry['description']}")
        
    # Copy v1 docx as a mockup v2 docx
    active_docx = vm.get_active_docx_path()
    mock_v2_temp = os.path.join(settings.DATA_DIR, "temp_mock_v2.docx")
    shutil.copy(active_docx, mock_v2_temp)
    
    print("\n3. Validating mockup docx...")
    DocumentValidator.validate_docx(mock_v2_temp)
    print("   Document passes validation.")
    
    print("\n4. Upgrading to mock version v2...")
    vm.upgrade(
        new_version_id="v2",
        author="test_engineer",
        description="Mock version for testing version control",
        changes=[{"operation": "mock_replace", "description": "No-op mock change"}],
        temp_docx_path=mock_v2_temp
    )
    
    print(f"   Active version after upgrade: {vm.get_active_version_id()}")
    
    print("\n5. Downgrading back to v1...")
    vm.downgrade("v1")
    print(f"   Active version after downgrade: {vm.get_active_version_id()}")
    
    print("\n6. Checking history preservation:")
    history = vm.get_history()
    for entry in history:
        print(f"   - {entry['version_id']} (Active: {entry['is_active']}) description: {entry['description']}")

    # Clean up mock v2 files to keep clean state
    # Wait, the prompt says "Downgrade never deletes history. All versions are permanently preserved."
    # So we don't delete the committed files from versions dir. We can keep v2 in versions.json for the next steps!
    # Let's remove the temporary file we created:
    if os.path.exists(mock_v2_temp):
        os.remove(mock_v2_temp)

if __name__ == "__main__":
    test_versioning_flow()
