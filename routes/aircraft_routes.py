# routes/aircraft_routes.py
from flask import Blueprint, request, jsonify
from db import db
from models.aircraft import Aircraft

aircraft_bp = Blueprint('aircraft_bp', __name__)  # We'll register this at /api/aircraft

@aircraft_bp.route("", methods=["GET"])
def list_aircraft():
    """
    GET /api/aircraft
    Return all aircraft in the DB.
    """
    all_aircraft = Aircraft.query.all()
    results = [a.to_dict() for a in all_aircraft]
    return jsonify({"count": len(results), "aircraft": results})

@aircraft_bp.route("", methods=["POST"])
def create_aircraft():
    """
    POST /api/aircraft
    Body:
      { "registration": "N123AB", "icao24": "A0B1C2", ... }
    Creates a new aircraft, 409 if registration already exists.
    """
    data = request.json or {}
    reg = data.get("registration", "").strip().upper()
    if not reg:
        return jsonify({"error": "Missing registration"}), 400

    existing = Aircraft.query.get(reg)
    if existing:
        return jsonify({"error": f"Aircraft {reg} already exists."}), 409

    ac = Aircraft(
        registration=reg,
        icao24=data.get("icao24", ""),
        selcal=data.get("selcal", ""),
        ac_type=data.get("type", ""),
        operator=data.get("operator", ""),
        serial_number=data.get("serial_number", ""),
        year_built=data.get("year_built"),
        status=data.get("status", "")
    )
    db.session.add(ac)
    db.session.commit()
    return jsonify({"status": f"Created aircraft {reg}"}), 201

@aircraft_bp.route("/<reg>", methods=["GET"])
def get_aircraft(reg):
    """
    GET /api/aircraft/<reg>
    """
    key = reg.strip().upper()
    ac = Aircraft.query.get(key)
    if not ac:
        return jsonify({"error": f"No aircraft found for {key}"}), 404
    return jsonify(ac.to_dict())

@aircraft_bp.route("/<reg>", methods=["PUT"])
def update_aircraft(reg):
    """
    PUT /api/aircraft/<reg>
    If it doesn't exist, create it. (Or you can 404 if you prefer.)
    """
    data = request.json or {}
    key = reg.strip().upper()
    ac = Aircraft.query.get(key)
    if not ac:
        ac = Aircraft(registration=key)
        db.session.add(ac)

    ac.icao24        = data.get("icao24", ac.icao24)
    ac.selcal        = data.get("selcal", ac.selcal)
    ac.ac_type       = data.get("type", ac.ac_type)
    ac.operator      = data.get("operator", ac.operator)
    ac.serial_number = data.get("serial_number", ac.serial_number)
    ac.year_built    = data.get("year_built", ac.year_built)
    ac.status        = data.get("status", ac.status)

    db.session.commit()
    return jsonify({"status": f"Aircraft {key} updated/created."})

@aircraft_bp.route("/<reg>", methods=["DELETE"])
def delete_aircraft(reg):
    """
    DELETE /api/aircraft/<reg>
    """
    key = reg.strip().upper()
    ac = Aircraft.query.get(key)
    if not ac:
        return jsonify({"error": f"No aircraft found for {key}"}), 404
    db.session.delete(ac)
    db.session.commit()
    return jsonify({"status": f"Aircraft {key} deleted."})