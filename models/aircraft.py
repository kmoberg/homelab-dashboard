from db import db
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import Date

class Aircraft(db.Model):
    """
    Aircraft table with relationships to AircraftType and Airline.
    """
    __tablename__ = "aircraft"

    registration = db.Column(db.String(20), primary_key=True)
    normalized_registration = db.Column(db.String(20), unique=True, index=True, nullable=False)  # Explicit column
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

    # Relationships
    aircraft_type = db.relationship("AircraftType", backref="aircraft_list", lazy="joined")

    # Backref to Airline using the operator_id FK
    operator = db.relationship("Airline", backref="aircraft_list", lazy="joined")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure normalized registration is stored in DB
        self.normalized_registration = kwargs.get("registration", "").replace("-", "").upper()

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
            "normalized_registration": self.normalized_registration,  # Stored in DB now
            "aircraft_type": {
                "id": self.aircraft_type.id,
                "type_code": self.aircraft_type.type_code,
                "manufacturer": self.aircraft_type.manufacturer,
                "model_name": self.aircraft_type.model_name,
                "engines": self.aircraft_type.engines,
                "description": self.aircraft_type.description,
            } if self.aircraft_type else None,
            "operator": {
                "id": self.operator.id,
                "icao_code": self.operator.icao_code,
                "iata_code": self.operator.iata_code,
                "name": self.operator.name,
                "country": self.operator.country,
            } if self.operator else None,
        }