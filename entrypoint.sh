#!/usr/bin/env bash
set -e  # Exit on error

echo "Running any pending migrations..."
# If you haven't installed flask-migrate or set up migrations,
# this command won't do anything. But once you have, it will apply them:
flask db upgrade || echo "No migrations to run or error applying migrations."

echo "Starting Flask app..."
exec python app.py