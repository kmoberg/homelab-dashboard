#!/usr/bin/env python3
"""
app.py - Main Flask app

This file:
  - Loads environment variables
  - Configures and initializes the database (SQLite)
  - Registers the aircraft blueprint at /api/aircraft
  - Defines your existing routes for weather, prices, etc.
"""

import os
import json
from datetime import datetime, timedelta, date
import requests

from flask import Flask, send_from_directory, request, jsonify
from flask_migrate import Migrate

from influxdb_client import InfluxDBClient
from airport_cache import get_airport_coords, get_airport_data
from aircraft_cache import (
    get_all_aircraft,
    get_aircraft_by_reg,
    create_or_update_aircraft,
    delete_aircraft
)
from dotenv import load_dotenv
from db import db, init_db_uri
from routes.aircraft_routes import aircraft_bp




###############################
# 1) Load ENV, create Flask
###############################
load_dotenv()
app = Flask(__name__, static_folder='public', static_url_path='')
app = init_db_uri(app)  # Initialize the SQLite database

db.init_app(app)  # Bind the SQLAlchemy db to the Flask app
with app.app_context():
    migrate = Migrate(app, db)

    # db.create_all()  # Create the tables if they don't exist


###############################
# 2) Register the aircraft blueprint
###############################
# Now all routes in `aircraft_bp` are available under /api/aircraft
app.register_blueprint(aircraft_bp, url_prefix="/api/aircraft")

# Load your pre-fetched sunrise/sunset data from local JSON
# Example structure: [{ "date": "2025-01-01", "sunrise": "08:47", "sunset": "16:11" }, ...]
with open('sun_data.json', 'r', encoding='utf-8') as f:
    SUN_DATA = json.load(f)

# APP SETUP
APP_NAME = os.getenv("APP_NAME")
APP_VERSION = os.getenv("APP_VERSION")
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL")

# ------------------------------------------------------
# InfluxDB setup
INFLUX_URL = os.getenv("INFLUX_URL")
INFLUX_API_TOKEN = os.getenv("INFLUX_API_TOKEN")
INFLUX_ORG = os.getenv("INFLUX_ORG")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET")

# Check if any of the required environment variables are missing or empty, if so kill the app
if not INFLUX_URL or not INFLUX_API_TOKEN or not INFLUX_ORG or not INFLUX_BUCKET:
    raise ValueError("Missing InfluxDB environment variables. Please check your environment variables.")

# Create a single InfluxDB client & Query API outside the route for reuse
influx_client = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_API_TOKEN,
    org=INFLUX_ORG
)
query_api = influx_client.query_api()


# ------------------------------------------------------
# 1. Serve the front-end (index.html) from public/
# ------------------------------------------------------
@app.route('/')
def index():
    # Serve index.html at root
    return send_from_directory('public', 'index.html')


# If you have other static assets (CSS, JS, images),
# Flask can serve them automatically if you place them in `public/`.
# E.g. /public/style.css => /style.css

# ------------------------------------------------------
# 2. /api/weather
#    Now extracts symbol_code for next_1, next_6, next_12
# ------------------------------------------------------
@app.route('/api/weather')
def api_weather():
    lat = request.args.get('lat', '58.970052')
    lon = request.args.get('lon', '5.733395')
    url = f"https://api.met.no/weatherapi/locationforecast/2.0/complete?lat={lat}&lon={lon}"

    headers = {
        'User-Agent': f'{APP_NAME}/{APP_VERSION} ({CONTACT_EMAIL})',
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # Extract symbol codes from first timeseries
        timeseries = data.get("properties", {}).get("timeseries", [])
        if not timeseries:
            return jsonify({"error": "No timeseries returned from MET"}), 500

        first_ts = timeseries[0]
        symbol_1h = None
        symbol_6h = None
        symbol_12h = None

        next1 = first_ts["data"].get("next_1_hours")
        if next1 and "summary" in next1:
            symbol_1h = next1["summary"].get("symbol_code")

        next6 = first_ts["data"].get("next_6_hours")
        if next6 and "summary" in next6:
            symbol_6h = next6["summary"].get("symbol_code")

        next12 = first_ts["data"].get("next_12_hours")
        if next12 and "summary" in next12:
            symbol_12h = next12["summary"].get("symbol_code")

        # Add them to the JSON
        out = data
        out["symbol_1h"] = symbol_1h
        out["symbol_6h"] = symbol_6h
        out["symbol_12h"] = symbol_12h

        return jsonify(out)

    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


# ------------------------------------------------------
# 3. /api/prices -> hvakosterstrommen.no
#    e.g. GET /api/prices?region=NO2
# ------------------------------------------------------
@app.route('/api/prices')
def api_prices():
    region = request.args.get('region', 'NO2')

    now = datetime.now()
    year = now.year
    month = f"{now.month:02d}"
    day = f"{now.day:02d}"

    # Build today's URL
    url_today = f"https://www.hvakosterstrommen.no/api/v1/prices/{year}/{month}-{day}_{region}.json"

    # We'll store results in a dict to return
    result = {
        "today": None,
        "tomorrow": None
    }

    try:
        # 1) Fetch today's data
        resp_today = requests.get(url_today, timeout=10)
        resp_today.raise_for_status()
        data_today = resp_today.json()

        # Compute average
        avg_today = compute_average_price(data_today)
        # We'll store today's data
        result["today"] = {
            "date": f"{year}-{month}-{day}",
            "average": avg_today,
            "prices": data_today
        }
    except requests.RequestException as e:
        return jsonify({"error": f"Failed to fetch today's prices: {e}"}), 500

    # 2) After 13:15 local time, attempt tomorrow
    #    We also build the next day's URL
    #    E.g. if now=2025-01-24, tomorrow=2025-01-25
    #    If the request fails or not found, we skip it
    local_now = datetime.now()
    # Check if local time >= 13:15
    cutoff_time = local_now.replace(hour=13, minute=15, second=0, microsecond=0)
    if local_now >= cutoff_time:
        # Build tomorrow's date
        tomorrow = local_now + timedelta(days=1)
        year_tom = tomorrow.year
        month_tom = f"{tomorrow.month:02d}"
        day_tom = f"{tomorrow.day:02d}"
        url_tomorrow = f"https://www.hvakosterstrommen.no/api/v1/prices/{year_tom}/{month_tom}-{day_tom}_{region}.json"

        try:
            resp_tom = requests.get(url_tomorrow, timeout=10)
            if resp_tom.status_code == 200:
                data_tom = resp_tom.json()
                avg_tom = compute_average_price(data_tom)
                result["tomorrow"] = {
                    "date": f"{year_tom}-{month_tom}-{day_tom}",
                    "average": avg_tom,
                    "prices": data_tom
                }
            else:
                # Not available or 404 => just ignore
                pass
        except requests.RequestException:
            pass

    return jsonify(result)


def compute_average_price(price_data):
    """
    Given an array of price entries from hvakosterstrommen,
    each with "NOK_per_kWh" field,
    return average * 100 in øre if you like, or keep in NOK.
    """
    if not price_data:
        return None

    total = 0.0
    count = 0
    for item in price_data:
        val = item.get("NOK_per_kWh")
        if val is not None:
            try:
                num = float(val)
                total += num
                count += 1
            except ValueError:
                pass

    if count == 0:
        return None

    avg = total / count
    # you can return in NOK or øre
    # e.g. return round(avg * 100, 1) for øre
    return round(avg * 100, 1)  # e.g. "42.3" meaning 42.3 øre


# ------------------------------------------------------
# 4. /api/sun -> local sunrise/sunset from sun_data.json
#    e.g. GET /api/sun?date=2025-01-24
# ------------------------------------------------------
@app.route('/api/sun')
def api_sun():
    # If date not provided, default to "today"
    date_str = request.args.get('date')
    if not date_str:
        date_str = date.today().isoformat()  # "YYYY-MM-DD"

    # Find matching entry in SUN_DATA
    found = next((d for d in SUN_DATA if d['date'] == date_str), None)
    if not found:
        # If no match, return a placeholder or error
        return jsonify({
            "date": date_str,
            "sunrise": None,
            "sunset": None,
            "note": "No local data stored for this date"
        })

    # Return an object shaped similarly to Sunrise 3.0's "Feature"
    return {
        "type": "Feature",
        "properties": {
            "date": found["date"],
            "sunrise": {"time": f"{found['date']}T{found['sunrise']}:00+01:00"},
            "sunset": {"time": f"{found['date']}T{found['sunset']}:00+01:00"}
        }
    }


# ------------------------------------------------------
# 5. /api/influx -> Query InfluxDB for weather data

@app.route("/api/enzv")
def api_enzv():
    """
    Returns JSON like:
    {
      "current": {
        "time": "2025-01-24T08:00:00+00:00",
        "altim_hpa": 1013.2,
        "altim_in_hg": 29.91,
        "dewpoint_c": 3.0,
        "temp_c": 5.0,
        "visibility_statute_mi": 8,
        "wind_dir_deg": 150,
        "wind_speed_kt": 12
      },
      "history": [
        {
          "time": "2025-01-24T02:00:00+00:00",
          "altim_hpa": 1012.2,
          "temp_c": 4.3,
          ...
        },
        ...
      ],
      "trend": "up" | "down" | "steady"
    }
    """

    try:
        # 1) Flux query for the last 6h, measurement=metar, station_id=ENZV
        # We'll filter for each _field we want, then pivot so each row has all fields.
        flux_query = f"""
        from(bucket: "{INFLUX_BUCKET}")
          |> range(start: -6h)
          |> filter(fn: (r) => r["_measurement"] == "metar")
          |> filter(fn: (r) => r["station_id"] == "ENZV")
          |> filter(fn: (r) =>
            r["_field"] == "altim_hpa" or
            r["_field"] == "altim_in_hg" or
            r["_field"] == "dewpoint_c" or
            r["_field"] == "temp_c" or
            r["_field"] == "visibility_statute_mi" or
            r["_field"] == "wind_dir_deg" or
            r["_field"] == "wind_speed_kt"
          )
          |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
          |> sort(columns: ["_time"], desc: false)
        """

        tables = query_api.query(flux_query)

        # We'll collect all rows into `points`.
        # Each row is a "record" with record.values dict including
        # { ... altim_hpa, altim_in_hg, dewpoint_c, temp_c, visibility_statute_mi, wind_dir_deg, wind_speed_kt, ... }
        points = []
        for table in tables:
            for record in table.records:
                # record.get_time() => datetime object
                # We'll store "time" as ISO string
                dt_iso = record.get_time().isoformat()
                row = {
                    "time": dt_iso,
                    "altim_hpa": record.values.get("altim_hpa"),
                    "altim_in_hg": record.values.get("altim_in_hg"),
                    "dewpoint_c": record.values.get("dewpoint_c"),
                    "temp_c": record.values.get("temp_c"),
                    "visibility_statute_mi": record.values.get("visibility_statute_mi"),
                    "wind_dir_deg": record.values.get("wind_dir_deg"),
                    "wind_speed_kt": record.values.get("wind_speed_kt")
                }
                points.append(row)

        if not points:
            return jsonify({"error": "No ENZV data in last 6h"}), 404

        # 2) The "current" data is the last row (since sort desc:false)
        current = points[-1]

        current_data = {
            "time": current["time"],
            "altim_hpa": current["altim_hpa"],
            "altim_in_hg": current["altim_in_hg"],
            "dewpoint_c": current["dewpoint_c"],
            "temp_c": current["temp_c"],
            "visibility_statute_mi": current["visibility_statute_mi"],
            "wind_dir_deg": current["wind_dir_deg"],
            "wind_speed_kt": current["wind_speed_kt"]
        }

        # 3) We'll build a "history" array for the chart. We can keep all fields,
        # or just a subset. Let's keep them all, or at least altim_hpa & temp_c, etc.
        history = []
        for p in points:
            history.append({
                "time": p["time"],
                "altim_hpa": p["altim_hpa"],
                "altim_in_hg": p["altim_in_hg"],
                "dewpoint_c": p["dewpoint_c"],
                "temp_c": p["temp_c"],
                "visibility_statute_mi": p["visibility_statute_mi"],
                "wind_dir_deg": p["wind_dir_deg"],
                "wind_speed_kt": p["wind_speed_kt"]
            })

        # 4) Trend based on altim_hpa changes over last hour
        trend = compute_altim_trend(points)

        return jsonify({
            "current": current_data,
            "history": history,
            "trend": trend
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def compute_altim_trend(points):
    """
    Compare altim_hpa ~1 hour ago vs now to see if it's up/down/steady.
    points is a time-ascending list of dicts with 'time' and 'altim_hpa'.
    """
    if len(points) < 2:
        return "steady"

    now_utc = datetime.utcnow()
    one_hour_ago = now_utc - timedelta(hours=1)

    # We'll parse the row times, filter out only those in last hour
    # (Note: If data is sparse, you might have only the latest row. Adjust as needed.)
    filtered = []
    for p in points:
        t = datetime.fromisoformat(p["time"])
        if t.replace(tzinfo=None) > one_hour_ago:
            filtered.append(p)

    if len(filtered) < 2:
        return "steady"

    start_val = filtered[0].get("altim_hpa") or 0
    end_val = filtered[-1].get("altim_hpa") or 0
    diff = end_val - start_val

    if diff > 0.2:
        return "up"
    elif diff < -0.2:
        return "down"
    else:
        return "steady"


@app.route("/api/metars")
def api_metars():
    """
    Fetch raw METAR data for KJFK, KLAX, ENZV, ENGM from FAA:
      https://aviationweather.gov/api/data/metar?ids=kjfk,klax,enzv,engm&format=json

    Returns JSON array, e.g.
    [
      {
        "icaoId": "KJFK",
        "rawOb": "KJFK 241351Z 28009KT 10SM FEW070 M02/M09 A3020 ..."
        ...
      },
      { ... KLAX ... },
      { ... ENZV ... },
      { ... ENGM ... }
    ]
    """

    url = "https://aviationweather.gov/api/data/metar?ids=kjfk,klax,enzv,engm&format=json"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()  # raise exception if not 2xx
        data = resp.json()  # parse JSON array
        # data is a list of dictionaries, one per station

        # Optionally, you can transform or filter out fields you don’t need.
        # For example, if you only want the rawOb and icaoId, do:
        #
        #   trimmed = []
        #   for item in data:
        #       trimmed.append({
        #           "icaoId": item["icaoId"],
        #           "rawOb": item["rawOb"]
        #       })
        #   return jsonify(trimmed)
        #
        # Otherwise, just return the entire array:

        return jsonify(data)

    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/distance")
def api_distance():
    icao = request.args.get("icao", "ENGM")
    lat = request.args.get("lat", None, float)
    lon = request.args.get("lon", None, float)

    print(f"[/api/distance] Received request: icao={icao}, lat={lat}, lon={lon}")

    if lat is None or lon is None:
        err_msg = "[/api/distance] Missing lat/lon in query params"
        print(err_msg)
        return jsonify({"error": err_msg}), 400

    coords = get_airport_coords(icao)
    if not coords:
        err_msg = f"[/api/distance] No coords found for {icao}"
        print(err_msg)
        return jsonify({"error": err_msg}), 404

    dist_nm = distance_nm(lat, lon, coords["lat"], coords["lon"])
    print(f"[/api/distance] Computed distance {dist_nm:.1f} nm from ({lat},{lon}) to {coords}")

    return jsonify({
        "icao": icao,
        "yourPos": [lat, lon],
        "airportPos": [coords["lat"], coords["lon"]],
        "distanceNm": round(dist_nm, 1)
    })


def distance_nm(lat1, lon1, lat2, lon2):
    # same formula as your code
    import math
    R = 6371.0  # Earth radius in km
    toRad = math.pi / 180.0
    dLat = (lat2 - lat1) * toRad
    dLon = (lon2 - lon1) * toRad
    a = (math.sin(dLat / 2) ** 2
         + math.cos(lat1 * toRad) * math.cos(lat2 * toRad)
         * math.sin(dLon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    dist_km = R * c
    dist_nm = dist_km / 1.852
    return dist_nm


# ------------------------------------------------------
# 6. /api/airport/<icao> -> Full station record
#    /api/airport/<icao>/iata -> Just IATA code
#    /api/airport/<icao>/location -> Basic location info
# ------------------------------------------------------

@app.route("/api/airport/<icao>")
def api_airport_full(icao):
    """
    Returns the entire station record from local DB or CheckWX if missing.
    If not found, return 404.
    """
    station = get_airport_data(icao)
    if not station:
        return jsonify({"error": f"No station data found for {icao}"}), 404
    # Return the full object exactly as stored
    return jsonify(station)


@app.route("/api/airport/<icao>/iata")
def api_airport_iata(icao):
    """
    Returns just the IATA code (and ICAO) for the given airport.
    Example JSON: { "icao": "KLAX", "iata": "LAX" }
    """
    station = get_airport_data(icao)
    if not station:
        return jsonify({"error": f"No station data found for {icao}"}), 404

    iata = station.get("iata", "N/A")  # might be missing
    return jsonify({"icao": icao.upper(), "iata": iata})


@app.route("/api/airport/<icao>/location")
def api_airport_location(icao):
    """
    Returns location info: city, country, lat, lon, etc.
    Example JSON:
    {
      "icao": "KLAX",
      "city": "Los Angeles",
      "country": "United States",
      "lat": 33.942501,
      "lon": -118.407997
    }
    """
    station = get_airport_data(icao)
    if not station:
        return jsonify({"error": f"No station data found for {icao}"}), 404

    # Some fields might be missing for certain airports. Use .get() safely.
    city = station.get("city", "Unknown")
    # station["country"] could be a dict { "code": "US", "name": "United States" }
    country_obj = station.get("country", {})
    country_name = country_obj.get("name", "Unknown")

    lat = station.get("latitude", {}).get("decimal")
    lon = station.get("longitude", {}).get("decimal")

    return jsonify({
        "icao": icao.upper(),
        "city": city,
        "country": country_name,
        "lat": lat,
        "lon": lon
    })

# ------------------------------------------------------
# Run the Flask app
# ------------------------------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
