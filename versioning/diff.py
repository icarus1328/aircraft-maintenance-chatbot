from typing import List, Dict, Any
from versioning.manager import VersionManager

class VersionDiff:
    @staticmethod
    def get_diff(version_a: str, version_b: str) -> str:
        """
        Computes a human-readable difference list between two versions.
        Accumulates the 'changes' logs in the manifest from version_a to version_b.
        """
        vm = VersionManager()
        manifest = vm.load_manifest()
        
        # Build lookup of versions
        versions_by_id = {v["version_id"]: v for v in manifest["versions"]}
        
        if version_a not in versions_by_id or version_b not in versions_by_id:
            raise ValueError(f"One or both versions ({version_a}, {version_b}) not found in manifest.")
            
        # Trace path from version_b back to version_a (assuming vA is older than vB)
        # If vA is newer, swap them for diff trace
        # Let's check sequence. In versions list, index tells us order.
        idx_a = manifest["versions"].index(versions_by_id[version_a])
        idx_b = manifest["versions"].index(versions_by_id[version_b])
        
        if idx_a == idx_b:
            return f"No changes between active version {version_a} and target {version_b}."
            
        is_downgrade = idx_a > idx_b
        start_idx = min(idx_a, idx_b)
        end_idx = max(idx_a, idx_b)
        
        # Gather all changes in the range (excluding start_idx)
        diff_entries = []
        for i in range(start_idx + 1, end_idx + 1):
            ver = manifest["versions"][i]
            diff_entries.append({
                "version_id": ver["version_id"],
                "author": ver["author"],
                "timestamp": ver["timestamp"],
                "description": ver["description"],
                "changes": ver["changes"]
            })
            
        # Format human-readable output
        direction = "downgrade" if is_downgrade else "upgrade"
        title = f"Diff Report ({version_a} to {version_b} - {direction.upper()}):\n"
        output = [title, "=" * 60]
        
        for entry in diff_entries:
            output.append(f"\nVersion: {entry['version_id']} | Author: {entry['author']} | Date: {entry['timestamp']}")
            output.append(f"Summary: {entry['description']}")
            output.append("-" * 40)
            if not entry["changes"]:
                output.append("  * No structured changes logged.")
            else:
                for idx, chg in enumerate(entry["changes"], 1):
                    op = chg.get("operation", "Unknown")
                    desc = chg.get("description", "No description")
                    sec = chg.get("section", "N/A")
                    output.append(f"  {idx}. [{op}] in Section '{sec}': {desc}")
            output.append("=" * 60)
            
        return "\n".join(output)
