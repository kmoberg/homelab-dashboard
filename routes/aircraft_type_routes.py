from flask import Blueprint, jsonify
from models.aircraft_type import AircraftType

aircraft_type_bp = Blueprint("aircraft_type", __name__)

@aircraft_type_bp.route("/", methods=["GET"])
def get_aircraft_types():
    aircraft_types = AircraftType.query.all()
    return jsonify([at.to_dict() for at in aircraft_types])