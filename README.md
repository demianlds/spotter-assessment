# Spotter Labs — Fuel Stop Optimizer API

Django REST API that calculates the optimal fuel stops along a US driving route, minimizing total fuel cost based on real station prices.

## Setup

### 1. Add fuel data

Copy the provided CSV file into the `data/` folder:

```
data/fuel-prices-2023-10-23.csv   (or whatever the file is named)
```

### 2. Configure environment

```bash
cp .env.example .env
```

### 3. Start with Docker

```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`.

### 4. Load fuel stations

In a separate terminal, while the containers are running:

```bash
docker-compose exec web python manage.py load_fuel_data data/<your-file>.csv
```

This runs once. Stations are stored in PostgreSQL.

---

## API

### `POST /api/fuel-plan/`

**Request:**
```json
{
  "start": "Chicago, IL",
  "end": "Los Angeles, CA"
}
```

**Response:**
```json
{
  "route": {
    "type": "LineString",
    "coordinates": [[-87.6298, 41.8781], ...]
  },
  "summary": {
    "start": "Chicago, IL",
    "end": "Los Angeles, CA",
    "total_distance_miles": 2015.3,
    "total_fuel_cost_usd": 312.45,
    "total_gallons": 100.2,
    "stops_count": 4
  },
  "fuel_stops": [
    {
      "station_name": "Pilot Travel Center",
      "city": "Joliet",
      "state": "IL",
      "lat": 41.5,
      "lon": -88.1,
      "route_mile": 38.2,
      "gallons_filled": 22.5,
      "price_per_gallon": 3.459,
      "stop_cost_usd": 77.83
    }
  ]
}
```

The `route.coordinates` field is a GeoJSON LineString — paste it into [geojson.io](https://geojson.io) to visualize the route.

---

## How it works

1. **Geocode** start/end with Nominatim (OpenStreetMap) — cached.
2. **Route** via OSRM free API — single call, cached by coordinates.
3. **Project** stations onto route: find nearest waypoint for each station within 25 miles.
4. **Optimize**: greedy algorithm — at each position, pick the cheapest station within the 500-mile range, fill to full tank there.

**Assumptions:**
- Vehicle range: 500 miles
- Fuel efficiency: 10 MPG (50-gallon tank)
- Starts with a full tank

---

## Running tests

```bash
docker-compose exec web python manage.py test api.tests
```

---

## Local development (without Docker)

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# Set DATABASE_URL in .env to a local PostgreSQL instance
python manage.py migrate
python manage.py load_fuel_data data/<your-file>.csv
python manage.py runserver
```
