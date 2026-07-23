"""
data_utils.py
─────────────
Helpers for resolving local JSON data file paths.

Folder convention:
    data/[org_name]_[org_id]/engine_001.json

The path is fully deterministic from org_name + org_id + engine_id,
so no extra column is needed in the database.
"""

import os
import json
import random

# Base data directory (same folder as this file)
BASE_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Folder that holds seed JSON files per model type
ENGINE_SEEDS_DIR = os.path.join(BASE_DATA_DIR, "engines")


def sanitize_name(name: str) -> str:
    """Convert an org name to a safe folder name segment."""
    return (
        name.strip()
            .lower()
            .replace(" ", "_")
            .replace("/", "_")
            .replace("\\", "_")
            .replace(":", "_")
    )


def get_org_folder(org_name: str, org_id: str) -> str:
    """
    Return the folder name for an organization.
    Format: acme_aviation_3f7a1c2d-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    """
    return f"{sanitize_name(org_name)}_{org_id}"


def get_engine_file_path(org_name: str, org_id: str, engine_id: int, db_id: str = None) -> str:
    """
    Return the absolute path to an engine's JSON data file.
    If db_id (UUID from engines table) is provided, uses engine_<db_id>.json
    Otherwise falls back to engine_<engine_id>.json for backwards compatibility.
    """
    folder = get_org_folder(org_name, org_id)
    if db_id:
        filename = f"engine_{db_id}.json"
    else:
        filename = f"engine_{str(engine_id).zfill(3)}.json"
    return os.path.join(BASE_DATA_DIR, folder, filename)


def load_engine_data(org_name: str, org_id: str, engine_id: int) -> dict:
    """
    Load and return the JSON data for an engine.
    Returns an empty dict with a 'cycles' key if the file doesn't exist yet.
    """
    path = get_engine_file_path(org_name, org_id, engine_id)

    if not os.path.exists(path):
        print(f"[WARN] Data file not found: {path}")
        return {"engine_id": engine_id, "cycles": []}

    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load {path}: {e}")
        return {"engine_id": engine_id, "cycles": []}


def _pick_seed_data(model_type: str, engine_id: int) -> list:
    """
    Randomly select one JSON file from data/engines/<model_type>/
    and return its cycle list.
    Returns an empty list if no seed files exist for that model type.
    """
    seed_dir = os.path.join(ENGINE_SEEDS_DIR, model_type)
    if not os.path.isdir(seed_dir):
        print(f"[WARN] No seed directory for model_type '{model_type}': {seed_dir}")
        return []

    candidates = [f for f in os.listdir(seed_dir) if f.endswith(".json")]
    if not candidates:
        print(f"[WARN] No seed JSON files found in {seed_dir}")
        return []

    chosen = random.choice(candidates)
    chosen_path = os.path.join(seed_dir, chosen)
    try:
        with open(chosen_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Accept both a bare list and a dict with a 'cycles' key
        cycles = data if isinstance(data, list) else data.get("cycles", [])
        print(f"[OK] Seeded engine {engine_id} from {chosen} ({len(cycles)} cycles)")
        return cycles
    except Exception as e:
        print(f"[ERROR] Failed to read seed file {chosen_path}: {e}")
        return []


def create_engine_data_file(
    org_name: str,
    org_id: str,
    engine_id: int,
    model_type: str = "",
    db_id: str = None,
) -> str:
    """
    Create the org folder and populate the engine JSON file with cycle data
    randomly selected from data/engines/<model_type>/.
    Uses engine_<db_id>.json if db_id provided, else engine_<engine_id>.json.
    Returns the absolute path to the created file.
    Skips creation if the file already exists.
    """
    path    = get_engine_file_path(org_name, org_id, engine_id, db_id=db_id)
    org_dir = os.path.dirname(path)

    os.makedirs(org_dir, exist_ok=True)

    if not os.path.exists(path):
        cycles = _pick_seed_data(model_type, engine_id) if model_type else []

        payload = cycles if cycles else {
            "engine_id":   engine_id,
            "model_type":  model_type,
            "org_id":      org_id,
            "description": f"Sensor data for ENGINE-{str(engine_id).zfill(2)}",
            "cycles": [],
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        if cycles:
            print(f"[OK] Created engine data file with {len(cycles)} seeded cycles: {path}")
        else:
            print(f"[OK] Created empty engine data file (no seed available): {path}")
    else:
        print(f"[INFO] Engine data file already exists: {path}")

    return path
