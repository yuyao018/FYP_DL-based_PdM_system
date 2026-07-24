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


def download_model_file(model_type: str, filename: str, local_dir: str = None) -> str | None:
    """
    Download a model .h5 file from Supabase Storage.
    Returns the local file path, or None if download failed.
    
    Checks local disk first (for development), then falls back to storage.
    """
    # Check local first
    if local_dir:
        local_path = os.path.join(local_dir, filename)
        if os.path.exists(local_path):
            return local_path

    # Check default local path
    base_dir = Path(__file__).parent / "data" / "shared_models" / model_type
    local_path = base_dir / filename
    if local_path.exists():
        return str(local_path)

    # Download from Supabase Storage
    cache_path = _CACHE_DIR / "models" / model_type / filename
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    # Use cached version if exists
    if cache_path.exists():
        return str(cache_path)

    try:
        sb = _get_supabase_admin()
        if not sb:
            return None

        storage_path = f"{model_type}/{filename}"
        data = sb.storage.from_(MODELS_BUCKET).download(storage_path)
        
        with open(cache_path, "wb") as f:
            f.write(data)
        print(f"[STORAGE] Downloaded model: {storage_path} → {cache_path}")
        return str(cache_path)
    except Exception as e:
        print(f"[STORAGE] Failed to download model {model_type}/{filename}: {e}")
        return None


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

        data = sb.storage.from_(ENGINE_DATA_BUCKET).download(storage_path)
        
        with open(cache_path, "wb") as f:
            f.write(data)
        print(f"[STORAGE] Downloaded engine data: {storage_path} → {cache_path}")
        return str(cache_path)
    except Exception as e:
        print(f"[STORAGE] Failed to download engine data {storage_path}: {e}")
        return None


def list_model_files(model_type: str) -> list[str]:
    """List all .h5 files available for a model type (local + storage)."""
    files = set()

    # Check local
    local_dir = Path(__file__).parent / "data" / "shared_models" / model_type
    if local_dir.exists():
        for f in local_dir.glob("*.h5"):
            files.add(f.name)

    # Check cache
    cache_dir = _CACHE_DIR / "models" / model_type
    if cache_dir.exists():
        for f in cache_dir.glob("*.h5"):
            files.add(f.name)

    # If no local files, try listing from storage
    if not files:
        try:
            sb = _get_supabase_admin()
            if sb:
                result = sb.storage.from_(MODELS_BUCKET).list(model_type)
                for item in result:
                    name = item.get("name", "")
                    if name.endswith(".h5"):
                        files.add(name)
        except Exception:
            pass

    return sorted(files)


def get_model_path(model_type: str, filename: str = None) -> str | None:
    """
    Get the path to a model file, downloading from storage if needed.
    If filename is None, returns the most recent .h5 file.
    """
    if filename:
        return download_model_file(model_type, filename)

    # Find the most recent model file
    # First check local
    local_dir = Path(__file__).parent / "data" / "shared_models" / model_type
    if local_dir.exists():
        h5_files = sorted(
            [f for f in local_dir.iterdir() if f.suffix == ".h5"],
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        if h5_files:
            return str(h5_files[0])

    # Try storage
    files = list_model_files(model_type)
    if files:
        return download_model_file(model_type, files[-1])

    return None
