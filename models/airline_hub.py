# models/airline_hub.py
from db import db

class AirlineHub(db.Model):
    """
    Table for storing airline hubs.
    """
    __tablename__ = "airline_hub"

    id = db.Column(db.Integer, primary_key=True)
    airline_id = db.Column(db.Integer, db.ForeignKey("airline.id"), nullable=False)
    airport_code = db.Column(db.String(4), nullable=False)  # e.g., "DFW", "FRA"
    hub_type = db.Column(db.String(20), nullable=True)  # e.g., "Main", "Secondary"

    def to_dict(self):
        return {
            "id": self.id,
            "airline_id": self.airline_id,
            "airport_code": self.airport_code,
            "hub_type": self.hub_type,
        }