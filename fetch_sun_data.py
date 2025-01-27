#!/usr/bin/env python3

"""
fetch_sun_data.py

A simple Python script to fetch sunrise/sunset data for every day of a chosen year
from the MET Norway Sunrise 3.0 API, for Stavanger, Norway.

Usage:
  python fetch_sun_data.py 2025
Outputs:
  A file 'sun_data.json' with an array of:
  [
    {
      "date": "YYYY-MM-DD",
      "sunrise": "HH:MM",
      "sunset": "HH:MM"
    },
    ...
  ]
"""

import sys
import json
import requests
from datetime import date, timedelta

# Coordinates for Stavanger, Norway
LAT = 58.970052
LON = 5.733395

# Default to +01:00 (might be off during summer DST).
OFFSET = "+01:00"

# "User-Agent" header required by MET Norway
HEADERS = {
    "User-Agent": "StavangerSunData/1.0 (https://kmoberg.io)",
    "Accept": "application/json"
}

def fetch_sunrise_one_day(yyyy_mm_dd):
    """
    Fetch sunrise/sunset for a single date string (YYYY-MM-DD) from MET Sunrise 3.0 ("/sun").
    Returns (sunrise_str, sunset_str) in "HH:MM" 24-hour format.
    """
    url = (
        "https://api.met.no/weatherapi/sunrise/3.0/sun"
        f"?lat={LAT}&lon={LON}&date={yyyy_mm_dd}&offset={OFFSET}"
    )

    resp = requests.get(url, headers=HEADERS)
    if not resp.ok:
        raise RuntimeError(f"Sunrise API failed for {yyyy_mm_dd}: {resp.status_code}")

    data = resp.json()
    if data.get("type") != "Feature":
        raise ValueError(f"Unexpected format for {yyyy_mm_dd}: {data}")

    sunrise_iso = data.get("properties", {}).get("sunrise", {}).get("time")
    sunset_iso = data.get("properties", {}).get("sunset", {}).get("time")

    sunrise_str = "00:00"
    sunset_str = "00:00"

    if sunrise_iso:
        sr_dt = parse_iso_to_datetime(sunrise_iso)
        sunrise_str = sr_dt.strftime("%H:%M")
    if sunset_iso:
        ss_dt = parse_iso_to_datetime(sunset_iso)
        sunset_str = ss_dt.strftime("%H:%M")

    return sunrise_str, sunset_str

def parse_iso_to_datetime(iso_str):
    """
    Convert ISO datetime string (e.g. "2025-06-01T04:12:00+01:00") to a Python datetime.
    """
    # Python 3.11+ can parse the offset natively with strptime and %z,
    # but for broad compatibility, let's use fromisoformat (3.7+).
    return dateutil_parser(iso_str)

def dateutil_parser(iso_str):
    """
    Minimal fallback if you don't have dateutil:
    - For Python 3.11+, you can do: datetime.fromisoformat(iso_str)
    - For older versions or portability, we can do a quick parse.
    Here, let's assume the user has 'datetime.fromisoformat' (Python 3.7+).
    If that doesn't work, install python-dateutil or adapt as needed.
    """
    from datetime import datetime
    return datetime.fromisoformat(iso_str)

def main():
    if len(sys.argv) < 2:
        print("Usage: python fetch_sun_data.py <YEAR>")
        sys.exit(1)

    year = int(sys.argv[1])
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    all_data = []
    current = start_date
    while current <= end_date:
        yyyy_mm_dd = current.isoformat()  # "YYYY-MM-DD"
        print(f"Fetching for {yyyy_mm_dd} ...", end=" ")
        try:
            sunrise, sunset = fetch_sunrise_one_day(yyyy_mm_dd)
            all_data.append({
                "date": yyyy_mm_dd,
                "sunrise": sunrise,
                "sunset": sunset
            })
            print("OK")
        except Exception as e:
            print(f"Error: {e}")

        current += timedelta(days=1)

    # Write to sun_data.json
    with open("sun_data.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2)

    print(f"Done. Wrote {len(all_data)} entries to sun_data.json.")

if __name__ == "__main__":
    # If you rely on python-dateutil, add "import dateutil.parser"
    # or adapt parse logic for older Pythons.
    # For Python 3.7+ with fromisoformat, the above fallback should be enough.
    main()