import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DB_DIR = Path(__file__).resolve().parent / "data"
DB_PATH = DB_DIR / "aircraftDb.json"

_aircraft_db = {}


def _load_db():
    global _aircraft_db
    if not DB_PATH.exists():
        print("[aircraft_cache] No existing aircraftDb.json, starting with empty.")
        _aircraft_db = {}
        return

    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            _aircraft_db = json.load(f)
        print(f"[aircraft_cache] Loaded {len(_aircraft_db)} aircraft from JSON cache.")
    except Exception as e:
        print(f"[aircraft_cache] Error reading aircraftDb.json, starting empty: {e}")
        _aircraft_db = {}


def _save_db():
    global _aircraft_db
    DB_DIR.mkdir(exist_ok=True)
    try:
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(_aircraft_db, f, indent=2)
        print(f"[aircraft_cache] Saved aircraftDb.json with {len(_aircraft_db)} entries.")
    except Exception as e:
        print(f"[aircraft_cache] Error writing aircraftDb.json: {e}")


def get_all_aircraft():
    """
    Returns a list (or dict) of all aircraft records in the DB.
    The internal structure is a dict keyed by registration or some 'identifier'.
    """
    global _aircraft_db
    return _aircraft_db


def get_aircraft_by_reg(reg: str):
    """
    Get a single aircraft record by its 'registration' (or unique key).
    Returns dict if found, else None.
    """
    global _aircraft_db
    reg = reg.upper().strip()
    return _aircraft_db.get(reg)


def create_or_update_aircraft(record: dict):
    """
    Create or update an aircraft record in the DB.
    We assume 'registration' is our unique key.
    Example 'record':
    {
      "registration": "N123AB",
      "icao24": "A0B1C2",
      "selcal": "AB-CD",
      "type": "B737-800",
      "operator": "Test Airline",
      "serialNumber": "XYZ12345",
      ...
    }
    """
    global _aircraft_db
    reg = record.get("registration")
    if not reg:
        # No registration key => can't store it
        return False, "Missing 'registration' field."

    reg = reg.upper().strip()
    _aircraft_db[reg] = record
    _save_db()
    return True, f"Aircraft {reg} saved/updated."


def delete_aircraft(reg: str):
    """
    Delete an aircraft record by 'registration' key if it exists.
    """
    global _aircraft_db
    reg = reg.upper().strip()
    if reg in _aircraft_db:
        del _aircraft_db[reg]
        _save_db()
        return True
    return False


# Load DB once on import
_load_db()
