from flask import Blueprint, jsonify
from models.airline import Airline

airline_bp = Blueprint("airline", __name__)

@airline_bp.route("/", methods=["GET"])
def get_airlines():
    airlines = Airline.query.all()
    return jsonify([airline.to_dict() for airline in airlines])