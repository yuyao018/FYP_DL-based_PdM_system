"""
storage_utils.py
================
Utilities for downloading files from Supabase Storage.
Falls back to local disk if files exist locally (for development).

Buckets:
  - "models"      → .h5 model files, path: <model_type>/<filename>.h5
  - "engine-data" → engine JSON files, path: <model_type>/<filename>.json
                    or orgs/<org_folder>/<filename>.json
"""
from assets import database_integration as db

import os
import tempfile
from pathlib import Path

# Local cache directory for downloaded files
_CACHE_DIR = Path(tempfile.gettempdir()) / "pdm_cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)

MODELS_BUCKET = "models"
ENGINE_DATA_BUCKET = "engine-data"


def _get_supabase_admin():
    """Get a Supabase client with service role key for storage access."""
    from supabase import create_client
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        return None
    return create_client(url, key)




def download_engine_json(storage_path: str, local_fallback: str = None) -> str | None:
    """
    Download an engine JSON file from Supabase Storage.
    storage_path: e.g. "FD001/engine_test_42.json" or "orgs/<folder>/engine_xxx.json"
    
    Returns the local file path, or None if download failed.
    """
    # Check local fallback first
    if local_fallback and os.path.exists(local_fallback):
        return local_fallback

    # Download from storage
    cache_path = _CACHE_DIR / "engine-data" / storage_path
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    if cache_path.exists():
        return str(cache_path)

    try:
        sb = _get_supabase_admin()
        if not sb:
            return None

        data = db.download_file(sb, ENGINE_DATA_BUCKET, storage_path)
        
        with open(cache_path, "wb") as f:
            f.write(data)
        print(f"[STORAGE] Downloaded engine data: {storage_path} → {cache_path}")
        return str(cache_path)
    except Exception as e:
        print(f"[STORAGE] Failed to download engine data {storage_path}: {e}")
        return None




