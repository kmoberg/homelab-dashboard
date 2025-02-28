from flask import Blueprint, jsonify
from models.aircraft_type import AircraftType

aircraft_type_bp = Blueprint("aircraft_types", __name__)


@aircraft_type_bp.route("/", methods=["GET"])
def get_aircraft_types():
    """
    GET /api/aircraft_types
    List all aircraft types.

    Returns:
    - JSON list of aircraft types

    Example:
    [
        {
            "id": 1,
            "type_code": "A21N",
            "manufacturer": "Airbus",
            "model_name": "A321-253NX",
            "engines": "CFMI LEAP-1A33",
            "type_designator": null,
            "description": "Narrow-body jet airliner"
        },
        ...
    ]
    """
    aircraft_types = AircraftType.query.all()
    return jsonify([at.to_dict() for at in aircraft_types])
