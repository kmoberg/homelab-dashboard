# models/aircraft_type.py
from db import db

class AircraftType(db.Model):
    """
    Table for storing information about aircraft types.
    """
    __tablename__ = "aircraft_type"

    id = db.Column(db.Integer, primary_key=True)
    type_code = db.Column(db.String(10), unique=True, nullable=False)  # e.g., "A321", "B738"
    manufacturer = db.Column(db.String(100), nullable=False)  # e.g., "Airbus", "Boeing"
    model_name = db.Column(db.String(100), nullable=False)  # e.g., "A321-253NX"
    engines = db.Column(db.String(100), nullable=True)  # e.g., "2x PW1000G"
    description = db.Column(db.Text, nullable=True)  # Optional description

    # Relationships
    aircraft = db.relationship("Aircraft", backref="aircraft_type", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "type_code": self.type_code,
            "manufacturer": self.manufacturer,
            "model_name": self.model_name,
            "engines": self.engines,
            "description": self.description,
        }