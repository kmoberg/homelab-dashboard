# models/airline.py
from db import db

class Airline(db.Model):
    """
    Table for storing airline details.
    """
    __tablename__ = "airline"

    id = db.Column(db.Integer, primary_key=True)
    iata_code = db.Column(db.String(3), unique=True, nullable=False)  # e.g., "AA", "LH"
    icao_code = db.Column(db.String(3), unique=True, nullable=False)  # e.g., "AAL", "DLH"
    name = db.Column(db.String(100), nullable=False)  # e.g., "American Airlines"
    country = db.Column(db.String(100), nullable=True)

    # Relationships
    aircraft = db.relationship("Aircraft", backref="airline", lazy=True)
    hubs = db.relationship("AirlineHub", backref="airline", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "iata_code": self.iata_code,
            "icao_code": self.icao_code,
            "name": self.name,
            "country": self.country,
        }