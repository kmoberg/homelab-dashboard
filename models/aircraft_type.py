# models/aircraft_type.py
from db import db

class AircraftType(db.Model):
    """
    Aircraft Type table storing information about aircraft types.
    """
    __tablename__ = "aircraft_type"

    id = db.Column(db.Integer, primary_key=True)
    type_code = db.Column(db.String(10), nullable=False, unique=True)  # ICAO aircraft code
    manufacturer = db.Column(db.String(100), nullable=False)
    model_name = db.Column(db.String(100), nullable=False)
    engines = db.Column(db.String(100), nullable=True)
    type_designator = db.Column(db.String(10), nullable=True)  # ICAO aircraft code
    description = db.Column(db.Text(), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "type_code": self.type_code,
            "manufacturer": self.manufacturer,
            "model_name": self.model_name,
            "engines": self.engines,
            "type_designator": self.type_code,
            "description": self.description,
        }