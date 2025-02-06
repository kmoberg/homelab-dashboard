# models/airport.py
import json
from db import db
from sqlalchemy.dialects.postgresql import JSONB

class Airport(db.Model):
    __tablename__ = "airport"

    # You can store a top-level PK (ICAO)
    icao = db.Column(db.String(10), primary_key=True)
    iata = db.Column(db.String(10), nullable=True)
    name = db.Column(db.String(200), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    # A JSONB column for the *entire* CheckWX response or additional details
    details = db.Column(JSONB, nullable=True)

    def to_dict(self):
        """
        Return a dictionary of the core columns plus the JSONB 'details'.
        If 'details' includes additional fields, you can expose them here or pass them as-is.
        """
        data = {
            "icao": self.icao,
            "iata": self.iata,
            "name": self.name,
            "city": self.city,
            "country": self.country,
            "lat": self.latitude,
            "lon": self.longitude,
        }
        # Include the entire details JSON if present
        if self.details:
            data["details"] = self.details  # Already a dict if stored as JSONB
        return data