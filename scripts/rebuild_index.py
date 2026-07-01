import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from versioning.manager import VersionManager

def rebuild():
    vm = VersionManager()
    active_id = vm.get_active_version_id()
    print(f"Rebuilding index for active version: {active_id}")
    # Downgrade to active_id itself triggers a full clean and rebuild
    vm.downgrade(active_id)

if __name__ == "__main__":
    rebuild()
