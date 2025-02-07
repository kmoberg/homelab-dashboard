# models/aircraft.py
from db import db
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import Date

class Aircraft(db.Model):
    """
    Aircraft table with relationships to AircraftType and Airline.
    """
    __tablename__ = "aircraft"

    registration = db.Column(db.String(20), primary_key=True)
    icao24 = db.Column(db.String(10), nullable=True)
    selcal = db.Column(db.String(10), nullable=True)
    type_id = db.Column(db.Integer, db.ForeignKey("aircraft_type.id"), nullable=False)  # FK to AircraftType
    operator_id = db.Column(db.Integer, db.ForeignKey("airline.id"), nullable=False)  # FK to Airline
    serial_number = db.Column(db.String(50), nullable=True)
    year_built = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), nullable=True)
    name = db.Column(db.String(100), nullable=True)
    construction_number = db.Column(db.Integer, nullable=True)
    test_reg = db.Column(db.String(20), nullable=True)
    delivery_date = db.Column(Date, nullable=True)
    remarks_json = db.Column(JSONB, nullable=True)
    previous_reg_json = db.Column(JSONB, nullable=True)

    def to_dict(self):
        return {
            "registration": self.registration,
            "icao24": self.icao24,
            "selcal": self.selcal,
            "type_id": self.type_id,
            "operator_id": self.operator_id,
            "serial_number": self.serial_number,
            "year_built": self.year_built,
            "status": self.status,
            "name": self.name,
            "construction_number": self.construction_number,
            "test_reg": self.test_reg,
            "delivery_date": self.delivery_date,
            "remarks": self.remarks_json,
            "previous_reg": self.previous_reg_json,
        }