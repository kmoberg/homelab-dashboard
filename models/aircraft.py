# models/aircraft.py
import json
from db import db
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import Date

class Aircraft(db.Model):
    """
    Extended 'aircraft' table with columns for:
      - registration (PK)
      - icao24, selcal, type, operator, name, engines, etc.
      - plus new columns: model, construction_number (cn), test_reg, delivery_date
      - plus JSON-text columns to store 'remarks' (list) and 'previous_reg' (object)
    """
    __tablename__ = "aircraft"

    registration = db.Column(db.String(20), primary_key=True)
    icao24       = db.Column(db.String(10), nullable=True)
    selcal       = db.Column(db.String(10), nullable=True)
    ac_type      = db.Column(db.String(50), nullable=True)  # e.g. "A21N" in your example
    operator     = db.Column(db.String(100), nullable=True)
    serial_number= db.Column(db.String(50), nullable=True)
    year_built   = db.Column(db.Integer, nullable=True)
    status       = db.Column(db.String(20), nullable=True)
    name         = db.Column(db.String(100), nullable=True)
    engines      = db.Column(db.String(100), nullable=True)
    model         = db.Column(db.String(50), nullable=True)  # e.g. "A321-253NX"
    construction_number = db.Column(db.Integer, nullable=True)  # "cn": 9541
    test_reg      = db.Column(db.String(20), nullable=True)  # "testreg": "D-AVZA"
    delivery_date = db.Column(Date, nullable=True)  # "delivery": "2020.10.15" as string

    # We'll store 'remarks' array and 'previous-reg' object in JSON format
    remarks_json      = db.Column(JSONB, nullable=True)   # text column, we'll store JSON
    previous_reg_json = db.Column(JSONB, nullable=True)   # text column, we'll store JSON

    def to_dict(self):
        """
        Convert the DB fields into a Python dictionary. We'll parse
        the JSON fields back to Python objects if present.
        """
        data = {"registration": self.registration, "icao24": self.icao24, "selcal": self.selcal, "type": self.ac_type,
                "operator": self.operator, "serial_number": self.serial_number, "year_built": self.year_built,
                "status": self.status, "name": self.name, "engines": self.engines, "model": self.model,
                "cn": self.construction_number, "testreg": self.test_reg, "delivery": self.delivery_date,
                "remarks": self.remarks_json, "previous-reg": self.previous_reg_json}

        # Parse JSON fields if they exist

        return data