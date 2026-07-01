import os
import json
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional
from config.settings import settings

class VersionManager:
    def __init__(self, data_dir: str = settings.DATA_DIR):
        self.data_dir = data_dir
        self.versions_json_path = settings.VERSIONS_JSON
        self.active_version_txt_path = settings.ACTIVE_VERSION_TXT
        self.versions_dir = settings.VERSIONS_DIR
        
        # Ensure directories exist
        os.makedirs(self.versions_dir, exist_ok=True)
        self._init_manifest_if_needed()

    def _init_manifest_if_needed(self):
        """Initializes the versions.json and active_version.txt if not present or empty."""
        # Check if active_version.txt exists and has content
        has_active = os.path.exists(self.active_version_txt_path) and os.path.getsize(self.active_version_txt_path) > 0
        has_manifest = os.path.exists(self.versions_json_path) and os.path.getsize(self.versions_json_path) > 0

        if not has_manifest or not has_active:
            print("Initializing version control manifest...")
            
            # The original docx is in the versions folder
            orig_filename = "Synthetic manual_Boeing_737-800_Maintenance_1.docx"
            orig_path = os.path.join(self.versions_dir, orig_filename)
            
            if not os.path.exists(orig_path):
                # If it's not in data/versions/, check if we can copy it from a parent directory
                parent_data_path = os.path.join(settings.BASE_DIR, "data", orig_filename)
                if os.path.exists(parent_data_path):
                    shutil.copy(parent_data_path, orig_path)
                else:
                    # Let's see if we can find it in workspace root
                    workspace_path = os.path.join(settings.BASE_DIR, orig_filename)
                    if os.path.exists(workspace_path):
                        shutil.copy(workspace_path, orig_path)
            
            manifest = {
                "head": "v1",
                "versions": [
                    {
                        "version_id": "v1",
                        "parent_id": None,
                        "timestamp": "2026-03-15T09:00:00Z",
                        "author": "system",
                        "description": "Original document ingested",
                        "filename": orig_filename,
                        "is_original": True,
                        "changes": []
                    }
                ]
            }
            
            with open(self.versions_json_path, "w") as f:
                json.dump(manifest, f, indent=2)
                
            with open(self.active_version_txt_path, "w") as f:
                f.write("v1")

    def load_manifest(self) -> Dict[str, Any]:
        with open(self.versions_json_path, "r") as f:
            return json.load(f)

    def save_manifest(self, manifest: Dict[str, Any]):
        with open(self.versions_json_path, "w") as f:
            json.dump(manifest, f, indent=2)

    def get_active_version_id(self) -> str:
        with open(self.active_version_txt_path, "r") as f:
            return f.read().strip()

    def set_active_version_id(self, version_id: str):
        with open(self.active_version_txt_path, "w") as f:
            f.write(version_id)

    def get_active_docx_path(self) -> str:
        active_id = self.get_active_version_id()
        manifest = self.load_manifest()
        for v in manifest["versions"]:
            if v["version_id"] == active_id:
                return os.path.join(self.versions_dir, v["filename"])
        raise FileNotFoundError(f"Active version {active_id} not found in manifest.")

    def get_history(self) -> List[Dict[str, Any]]:
        manifest = self.load_manifest()
        active_id = self.get_active_version_id()
        # Add is_active flag for UI/utility
        history = []
        for v in manifest["versions"]:
            entry = dict(v)
            entry["is_active"] = (v["version_id"] == active_id)
            history.append(entry)
        return history

    def upgrade(self, new_version_id: str, author: str, description: str, changes: List[Dict[str, Any]], temp_docx_path: str):
        """
        Commits a new version derived from the current active version.
        Moves the temporary docx file into data/versions/ permanently, updates the manifest,
        and triggers a full reindex.
        """
        manifest = self.load_manifest()
        
        # Check if version already exists
        if any(v["version_id"] == new_version_id for v in manifest["versions"]):
            raise ValueError(f"Version {new_version_id} already exists.")
            
        parent_id = self.get_active_version_id()
        
        # Save file to permanent location
        filename = f"boeing_737_{new_version_id}.docx"
        dest_path = os.path.join(self.versions_dir, filename)
        shutil.copy(temp_docx_path, dest_path)
        
        new_entry = {
            "version_id": new_version_id,
            "parent_id": parent_id,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "author": author,
            "description": description,
            "filename": filename,
            "is_original": False,
            "changes": changes
        }
        
        manifest["versions"].append(new_entry)
        manifest["head"] = new_version_id
        
        self.save_manifest(manifest)
        self.set_active_version_id(new_version_id)
        
        # Trigger index rebuild
        self._rebuild_indices(new_version_id, dest_path)
        print(f"Successfully upgraded to version {new_version_id}.")

    def downgrade(self, target_version_id: str):
        """
        Switches the active document to target_version_id, updating active_version.txt,
        and rebuilds indexes to match it. Does not delete any version history.
        """
        manifest = self.load_manifest()
        
        # Check if target version exists
        target_entry = None
        for v in manifest["versions"]:
            if v["version_id"] == target_version_id:
                target_entry = v
                break
                
        if not target_entry:
            raise ValueError(f"Target version {target_version_id} not found in manifest.")
            
        self.set_active_version_id(target_version_id)
        docx_path = os.path.join(self.versions_dir, target_entry["filename"])
        
        # Trigger index rebuild
        self._rebuild_indices(target_version_id, docx_path)
        print(f"Successfully downgraded active version to {target_version_id}.")

    def _rebuild_indices(self, version_id: str, docx_path: str):
        """Internal helper to invoke ingestion index rebuild."""
        from scripts.ingest import run_ingestion
        run_ingestion(docx_path, version_id)
