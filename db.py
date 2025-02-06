# db.py
import os
from flask_sqlalchemy import SQLAlchemy

# We'll instantiate db here, but not bind it to an app just yet.
db = SQLAlchemy()

def init_db_uri(app):
    """
    Configures the app's SQLALCHEMY_DATABASE_URI to use 'aircraft.db' (SQLite).
    If you want a different path or a PostgreSQL URI, adjust here.
    """
    base_dir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(base_dir, "data/aircraft.db")
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    return app