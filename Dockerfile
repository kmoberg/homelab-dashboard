FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Force unbuffered output so you see all logs immediately
ENV PYTHONUNBUFFERED=1

# If you use Flask-Migrate, you'll need `pip install flask-migrate` in requirements.txt
# Also set FLASK_APP if needed, e.g.:
ENV FLASK_APP=app.py

# Copy our entrypoint script into the container
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 3000

# The entrypoint runs migrations first, then starts `python app.py`
ENTRYPOINT ["/entrypoint.sh"]