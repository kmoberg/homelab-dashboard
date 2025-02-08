# routes/aircraft_routes.py
import json
from flask import Blueprint, request, jsonify
from db import db
from models.aircraft import Aircraft

aircraft_bp = Blueprint('aircraft_bp', __name__)  # Will be registered at /api/aircraft


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
    Creates a new aircraft. If 'registration' already exists, returns 409.

    Example JSON:
    {
      "registration": "SE-DMO",
      "icao24": "4A91AF",
      "type": "A21N",
      "model": "A321-253NX",
      "cn": 9541,
      "selcal": "ADCP",
      "built": 2020,
      "testreg": "D-AVZA",
      "delivery": "2020.10.15",
      "operator": "Scandinavian Airlines",
      "status": "active",
      "previous-reg": { ... },
      "engines": "CFMI LEAP-1A33",
      "name": "Jarl Viking",
      "remarks": [
        "Named \"Jarl Viking\"",
        "Leased from ALC"
      ]
    }
    """
    data = request.json or {}
    reg = data.get("registration", "").strip().upper()
    if not reg:
        return jsonify({"error": "Missing registration"}), 400

    existing = Aircraft.query.get(reg)
    if existing:
        return jsonify({"error": f"Aircraft {reg} already exists."}), 409

    # Convert numeric fields
    year_built = None
    if "built" in data or "year_built" in data:
        raw = data.get("built", data.get("year_built"))
        try:
            year_built = int(raw)
        except (TypeError, ValueError):
            year_built = None

    cn_val = None
    if "cn" in data:
        try:
            cn_val = int(data["cn"])
        except (TypeError, ValueError):
            cn_val = None

    ac = Aircraft(
        registration=reg,
        normalized_registration=reg.replace("-", ""),  # Store normalized version
        icao24=data.get("icao24", ""),
        selcal=data.get("selcal", ""),
        type_id=data.get("type", ""),
        operator_id=data.get("operator", ""),
        serial_number=data.get("serial_number", ""),
        year_built=year_built,
        status=data.get("status", ""),
        name=data.get("name", ""),
        construction_number=cn_val,
        test_reg=data.get("testreg", ""),
        delivery_date=data.get("delivery", "")
    )

    # Store JSON fields
    if "remarks" in data:
        ac.remarks_json = json.dumps(data["remarks"])
    if "previous-reg" in data:
        ac.previous_reg_json = json.dumps(data["previous-reg"])

    db.session.add(ac)
    db.session.commit()
    return jsonify({"status": f"Created aircraft {reg}"}), 201


@aircraft_bp.route("/<reg>", methods=["GET"])
def get_aircraft(reg):
    """
    GET /api/aircraft/<reg>
    Returns the aircraft record if found, else 404.
    Supports looking up registrations without dashes.
    """
    key = reg.strip().upper().replace("-", "")  # Normalize input
    ac = Aircraft.query.filter(Aircraft.normalized_registration == key).first()

    if not ac:
        return jsonify({"error": f"No aircraft found for {key}"}), 404

    return jsonify(ac.to_dict())


@aircraft_bp.route("/<reg>", methods=["PUT"])
def update_aircraft(reg):
    """
    PUT /api/aircraft/<reg>
    If it doesn't exist, create it (upsert). Otherwise, update fields present in JSON.
    """
    data = request.json or {}
    key = reg.strip().upper()
    ac = Aircraft.query.get(key)
    if not ac:
        ac = Aircraft(registration=key)
        db.session.add(ac)

    # Overwrite fields if provided
    if "icao24" in data:         ac.icao24 = data["icao24"]
    if "selcal" in data:         ac.selcal = data["selcal"]
    if "type" in data:           ac.ac_type = data["type"]
    if "operator" in data:       ac.operator = data["operator"]
    if "serial_number" in data:  ac.serial_number = data["serial_number"]
    if "status" in data:         ac.status = data["status"]
    if "name" in data:           ac.name = data["name"]
    if "engines" in data:        ac.engines = data["engines"]
    if "model" in data:          ac.model = data["model"]
    if "testreg" in data:        ac.test_reg = data["testreg"]
    if "delivery" in data:       ac.delivery_date = data["delivery"]

    # Convert or ignore if invalid
    if "built" in data or "year_built" in data:
        raw_built = data.get("built", data.get("year_built"))
        try:
            ac.year_built = int(raw_built)
        except (TypeError, ValueError):
            ac.year_built = None

    if "cn" in data:
        try:
            ac.construction_number = int(data["cn"])
        except (TypeError, ValueError):
            ac.construction_number = None

    # JSON fields
    if "remarks" in data:
        ac.remarks_json = json.dumps(data["remarks"])
    if "previous-reg" in data:
        ac.previous_reg_json = json.dumps(data["previous-reg"])

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