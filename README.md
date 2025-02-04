# Homelab Dashboard
This is a simple dashboard for my homelab. It is a simple web page that displays the status of various services running on my homelab server. It is built using Flask and Bootstrap.

## Features
- Displays the status of various services running on my homelab server
- Displays weather and airport information for my local area
- Displays VATSIM data because I'm a nerd.

## Usage
1. Clone the repository
2. Add the following environment variables either to a .env file or to your environment:
```bash
INFLUX_URL=<influxdb url>
INFLUX_API_TOKEN=<influxdb api token>
INFLUX_ORG=<influxdb org>
INFLUX_BUCKET=<influxdb bucket>
CONTACT_EMAIL=<email address> (Used for querying met.no API)
APP_NAME=<app name> (Used for querying met.no API)
APP_VERSION=<app version> (Used for querying met.no API)
CHECKWX_API_KEY=<checkwx api key> (Used for querying checkwx API)
```

3. Build and run the Docker container using docker-compose
```bash
docker-compose up --build
```
3. Access the dashboard at `http://localhost:3000`