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

def _fetch_station_data(icao: str):
    """
    Queries CheckWX's station endpoint:
      GET https://api.checkwx.com/station/{icao}
    Header: X-API-Key: <your key>

    Example station JSON in data["data"][0]:
    {
      "icao": "KLAX",
      "latitude":  { "decimal": 33.942501, ... },
      "longitude": { "decimal": -118.407997, ... },
      "geometry": {
        "coordinates": [ -118.407997, 33.942501 ],
        ...
      },
      ...
    }

    Returns the 'first' station dict or None if not found/fetch failed.
    """
    url = f"https://api.checkwx.com/station/{icao}"
    headers = {"X-API-Key": CHECKWX_API_KEY}

    masked_key = (CHECKWX_API_KEY[:4] + "****") if CHECKWX_API_KEY else "(None)"
    print(f"[airport_cache] _fetch_station_data: icao={icao}, URL={url}, KEY={masked_key}")

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"[airport_cache]  CheckWX response: {resp.status_code}")
        resp.raise_for_status()

        data = resp.json()
        print(f"[airport_cache]  CheckWX JSON keys: {list(data.keys())}")

        arr = data.get("data", [])
        if not arr:
            print(f"[airport_cache]  No 'data' array returned for ICAO={icao}. Full JSON = {data}")
            return None

        first_station = arr[0]
        return first_station  # We'll store this entire record
    except requests.RequestException as e:
        print(f"[airport_cache]  CheckWX API call failed for {icao}: {e}")
        return None

def get_airport_coords(icao: str):
    """
    Main function to retrieve lat/lon from local DB or from CheckWX if missing.
    Returns dict {"lat": float, "lon": float} or None if not found/fetch failed.

    Now we store the entire station record from CheckWX in _airport_db[icao],
    but only return lat/lon to the caller. (You can expand this in your code.)
    """
    global _airport_db
    icao = icao.upper().strip()
    print(f"[airport_cache] get_airport_coords called for {icao}")

    if icao in _airport_db:
        print(f"[airport_cache]  Found {icao} in local DB")
        station = _airport_db[icao]
    else:
        print(f"[airport_cache]  {icao} not in local DB; querying CheckWX.")
        station = _fetch_station_data(icao)
        if station:
            _airport_db[icao] = station
            _save_db()
            print(f"[airport_cache]  => Stored new station record for {icao}")
        else:
            print(f"[airport_cache]  => Could NOT find station for {icao} (None returned)")
            return None

    # Extract lat/lon from the station record
    lat = station.get("latitude", {}).get("decimal")
    lon = station.get("longitude", {}).get("decimal")
    if lat is None or lon is None:
        print(f"[airport_cache]  Missing lat/lon in stored record for {icao}.")
        return None

    return {"lat": lat, "lon": lon}

def get_airport_data(icao: str):
    """
    Returns the entire station record for the given ICAO
    from the local DB or CheckWX if missing.
    Example keys: 'icao', 'iata', 'city', 'country', 'latitude', 'longitude', 'geometry', etc.
    If not found, returns None.
    """
    global _airport_db
    icao = icao.upper().strip()
    print(f"[airport_cache] get_airport_data called for {icao}")

    # If we already have it, return it
    if icao in _airport_db:
        print(f"[airport_cache]  Found {icao} in local DB")
        return _airport_db[icao]

    print(f"[airport_cache]  {icao} not in local DB; querying CheckWX.")
    station = _fetch_station_data(icao)  # the function that calls /station/<icao>
    if station:
        _airport_db[icao] = station
        _save_db()
        print(f"[airport_cache]  => Stored new station record for {icao}")
    else:
        print(f"[airport_cache]  => Could NOT find station for {icao} (None returned)")
        return None

    return station

# Load DB upon module import
_load_db()