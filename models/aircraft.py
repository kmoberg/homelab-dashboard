# models/aircraft.py
from db import db

class Aircraft(db.Model):
    """
    A sample 'aircraft' table with columns:
      - registration (PK)
      - icao24, selcal, type, operator, etc.
    """
    __tablename__ = "aircraft"

    registration = db.Column(db.String(20), primary_key=True)
    icao24       = db.Column(db.String(10), nullable=True)
    selcal       = db.Column(db.String(10), nullable=True)
    ac_type      = db.Column(db.String(50), nullable=True)
    operator     = db.Column(db.String(100), nullable=True)
    serial_number= db.Column(db.String(50), nullable=True)
    year_built   = db.Column(db.Integer, nullable=True)
    status       = db.Column(db.String(20), nullable=True)
    name        = db.Column(db.String(100), nullable=True)
    engines     = db.Column(db.String(100), nullable=True)

    def to_dict(self):
        return {
            "registration": self.registration,
            "icao24": self.icao24,
            "selcal": self.selcal,
            "type": self.ac_type,
            "operator": self.operator,
            "serial_number": self.serial_number,
            "year_built": self.year_built,
            "name": self.name,
            "engines": self.engines,
            "status": self.status
        }