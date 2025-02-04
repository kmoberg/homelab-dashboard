import os
import json
import requests

from pathlib import Path

# Get the API key from environment variable or .env file
from dotenv import load_dotenv
load_dotenv()

CHECKWX_API_KEY = os.getenv("CHECKWX_API_KEY")
DB_DIR = Path(__file__).resolve().parent / "data"  # e.g. directory "data" next to this file
DB_PATH = DB_DIR / "airportDb.json"

# In-memory store
_airport_db = {}

def _load_db():
    global _airport_db
    if not DB_PATH.exists():
        print("No existing airportDb.json, starting with empty.")
        _airport_db = {}
        return

    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            _airport_db = json.load(f)
        print(f"Loaded {_airport_db.__len__()} airports from JSON cache.")
    except Exception as e:
        print(f"Error reading airportDb.json, starting empty: {e}")
        _airport_db = {}

def _save_db():
    global _airport_db
    DB_DIR.mkdir(exist_ok=True)  # ensure folder exists
    try:
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(_airport_db, f, indent=2)
        print(f"Saved airportDb.json with {_airport_db.__len__()} entries.")
    except Exception as e:
        print(f"Error writing airportDb.json: {e}")

def _fetch_coords_from_checkwx(icao: str):
    """
    Queries CheckWX's airport endpoint:
    GET https://api.checkwx.com/airport/{icao}
    Header: X-API-Key: <your key>

    Expecting JSON like:
    {
      "results": 1,
      "data": [{
        "icao": "ENGM",
        "location": {
          "latitude": 60.1939,
          "longitude": 11.1004
        },
        ...
      }]
    }
    Return a dict {"lat": <float>, "lon": <float>} or None if not found.
    """
    url = f"https://api.checkwx.com/airport/{icao}"
    headers = {
        "X-API-Key": CHECKWX_API_KEY
    }
    print(f"Fetching coords for {icao} from CheckWX: {url}")

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # data["data"] is a list, e.g. data["data"][0]["location"]["latitude"]
        arr = data.get("data", [])
        if not arr:
            print(f"No 'data' for ICAO={icao} from CheckWX response.")
            return None

        first = arr[0]
        loc = first.get("location", {})
        lat = loc.get("latitude")
        lon = loc.get("longitude")
        if lat is None or lon is None:
            print(f"No lat/lon in record for {icao}.")
            return None

        return {"lat": lat, "lon": lon}

    except requests.RequestException as e:
        print(f"CheckWX API call failed for {icao}: {e}")
        return None

def get_airport_coords(icao: str):
    """
    Main function to get lat/lon from local DB or fetch from CheckWX if missing.
    Returns dict {"lat": float, "lon": float} or None if not found/fetch failed.
    """
    global _airport_db
    icao = icao.upper().strip()
    if icao in _airport_db:
        return _airport_db[icao]

    coords = _fetch_coords_from_checkwx(icao)
    if coords:
        _airport_db[icao] = coords
        _save_db()
    return coords

# Load DB upon module import
_load_db()