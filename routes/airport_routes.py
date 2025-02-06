# routes/airport_routes.py
import json
import requests
from flask import Blueprint, jsonify, request
from db import db
from models.airport import Airport
from dotenv import load_dotenv
import os

airport_bp = Blueprint('airport_bp', __name__)
load_dotenv()
CHECKWX_API_KEY = os.getenv("CHECKWX_API_KEY")

@airport_bp.route("/<icao>", methods=["GET"])
def get_airport(icao):
    """
    GET /api/airport/<icao>
    If not in DB => fetch from CheckWX => store as JSONB + top-level columns
    """
    icao = icao.strip().upper()
    ap = Airport.query.get(icao)
    if ap:
        return jsonify(ap.to_dict())

    # Not found => fetch from CheckWX
    station_data = fetch_station_data_checkwx(icao)
    if not station_data:
        return jsonify({"error": f"No station data found for {icao}"}), 404

    # Parse lat/lon from station_data
    lat = station_data.get("latitude", {}).get("decimal")
    lon = station_data.get("longitude", {}).get("decimal")

    # city might come from station_data["city"] or from station_data["location"] logic
    city = station_data.get("city", "")
    # Maybe parse country name (some data might be nested in station_data["country"]["name"])
    country_obj = station_data.get("country", {})
    country_name = country_obj.get("name", "")

    iata = station_data.get("iata", "")
    name = station_data.get("name", "")

    new_ap = Airport(
        icao=icao,
        iata=iata,
        name=name,
        city=city,
        country=country_name,
        latitude=lat,
        longitude=lon,
        details=station_data  # store entire dictionary in JSONB
    )
    db.session.add(new_ap)
    db.session.commit()

    return jsonify(new_ap.to_dict())


@airport_bp.route("", methods=["GET"])
def list_airports():
    """
    GET /api/airport
    Return all airports in the DB
    """
    airports = Airport.query.all()
    results = [a.to_dict() for a in airports]
    return jsonify({"count": len(results), "airports": results})

@airport_bp.route("", methods=["POST"])
def create_airport():
    """
    POST /api/airport
    Create an airport manually with JSON body.
    {
      "icao": "ENGM",
      "iata": "OSL",
      "name": "Oslo Airport, Gardermoen",
      "city": "Ullensaker",
      "country": "Norway",
      "lat": 60.193901,
      "lon": 11.1004,
      "details": { ... }  // optional
    }
    """
    data = request.json or {}
    icao = data.get("icao", "").strip().upper()
    if not icao:
        return jsonify({"error": "Missing ICAO"}), 400

    existing = Airport.query.get(icao)
    if existing:
        return jsonify({"error": f"Airport {icao} already exists"}), 409

    ap = Airport(
        icao=icao,
        iata=data.get("iata", ""),
        name=data.get("name", ""),
        city=data.get("city", ""),
        country=data.get("country", ""),
        latitude=data.get("lat"),
        longitude=data.get("lon"),
        details=data.get("details")  # store entire dict if present
    )
    db.session.add(ap)
    db.session.commit()
    return jsonify({"status": f"Created airport {icao}"}), 201

@airport_bp.route("/<icao>", methods=["PUT"])
def update_airport(icao):
    """
    PUT /api/airport/<icao>
    Upsert fields, including 'details' if you like
    """
    data = request.json or {}
    key = icao.strip().upper()
    ap = Airport.query.get(key)
    if not ap:
        ap = Airport(icao=key)
        db.session.add(ap)

    if "iata" in data:    ap.iata = data["iata"]
    if "name" in data:    ap.name = data["name"]
    if "city" in data:    ap.city = data["city"]
    if "country" in data: ap.country = data["country"]
    if "lat" in data:     ap.latitude = data["lat"]
    if "lon" in data:     ap.longitude = data["lon"]

    # If we want to update details partially or overwrite fully, we can do either:
    if "details" in data:
        ap.details = data["details"]

    db.session.commit()
    return jsonify({"status": f"Airport {key} updated/created"})

@airport_bp.route("/<icao>", methods=["DELETE"])
def delete_airport(icao):
    """
    DELETE /api/airport/<icao>
    """
    key = icao.strip().upper()
    ap = Airport.query.get(key)
    if not ap:
        return jsonify({"error": f"No airport found for {key}"}), 404
    db.session.delete(ap)
    db.session.commit()
    return jsonify({"status": f"Airport {key} deleted."})

def fetch_station_data_checkwx(icao: str):
    """
    Example usage: GET https://api.checkwx.com/station/{icao} with JSONB
    """
    url = f"https://api.checkwx.com/station/{icao}"
    key = CHECKWX_API_KEY or ""
    headers = {"X-API-Key": key}
    print(f"[airport_routes] fetch_station_data_checkwx => {url}")
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        arr = data.get("data", [])
        if arr:
            return arr[0]
        return None
    except requests.RequestException as e:
        print(f"[airport_routes] CheckWX error: {e}")
        return None