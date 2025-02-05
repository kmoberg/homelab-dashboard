import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CHECKWX_API_KEY = os.getenv("CHECKWX_API_KEY")
DB_DIR = Path(__file__).resolve().parent / "data"
DB_PATH = DB_DIR / "airportDb.json"

_airport_db = {}


def _load_db():
    global _airport_db
    if not DB_PATH.exists():
        print("[airport_cache] No existing airportDb.json, starting with empty.")
        _airport_db = {}
        return

    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            _airport_db = json.load(f)
        print(f"[airport_cache] Loaded {len(_airport_db)} airports from JSON cache.")
    except Exception as e:
        print(f"[airport_cache] Error reading airportDb.json, starting empty: {e}")
        _airport_db = {}


def _save_db():
    global _airport_db
    DB_DIR.mkdir(exist_ok=True)  # ensure folder exists
    try:
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(_airport_db, f, indent=2)
        print(f"[airport_cache] Saved airportDb.json with {len(_airport_db)} entries.")
    except Exception as e:
        print(f"[airport_cache] Error writing airportDb.json: {e}")


def _fetch_coords_from_checkwx(icao: str):
    """
    Queries CheckWX's airport endpoint:
    GET https://api.checkwx.com/airport/{icao}
    Header: X-API-Key: <your key>
    Returns dict {"lat": <float>, "lon": <float>} or None if not found.
    """
    url = f"https://api.checkwx.com/airport/{icao}"
    headers = {"X-API-Key": CHECKWX_API_KEY}

    # Log which key you're using. If you're worried about security, you can mask part of it:
    masked_key = (CHECKWX_API_KEY[:4] + "****") if CHECKWX_API_KEY else "(None)"
    print(f"[airport_cache] _fetch_coords_from_checkwx: icao={icao}, URL={url}, KEY={masked_key}")

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"[airport_cache]  CheckWX response: {resp.status_code}")
        resp.raise_for_status()

        data = resp.json()
        print(f"[airport_cache]  CheckWX JSON keys: {list(data.keys())}")  # e.g. ['results', 'data']

        arr = data.get("data", [])
        if not arr:
            print(f"[airport_cache]  No 'data' array returned for ICAO={icao}. Full JSON = {data}")
            return None

        first = arr[0]
        loc = first.get("location", {})
        lat = loc.get("latitude")
        lon = loc.get("longitude")

        if lat is None or lon is None:
            print(f"[airport_cache]  No lat/lon in record for {icao}. Record = {first}")
            return None

        print(f"[airport_cache]  => Found lat={lat}, lon={lon} for {icao}")
        return {"lat": lat, "lon": lon}

    except requests.RequestException as e:
        # You can print the entire response text for debugging if you want
        print(f"[airport_cache]  CheckWX API call failed for {icao}: {e}")
        return None


def get_airport_coords(icao: str):
    """
    Main function to get lat/lon from local DB or fetch from CheckWX if missing.
    Returns dict {"lat": float, "lon": float} or None if not found/fetch failed.
    """
    global _airport_db
    icao = icao.upper().strip()
    print(f"[airport_cache] get_airport_coords called for {icao}")

    if icao in _airport_db:
        print(f"[airport_cache]  Found {icao} in local DB: {_airport_db[icao]}")
        return _airport_db[icao]

    print(f"[airport_cache]  {icao} not in local DB; querying CheckWX.")
    coords = _fetch_coords_from_checkwx(icao)

    if coords:
        _airport_db[icao] = coords
        _save_db()
        print(f"[airport_cache]  => Stored new coords for {icao}: {coords}")
    else:
        print(f"[airport_cache]  => Could NOT find coords for {icao} (None returned)")

    return coords


# Load DB upon module import
_load_db()