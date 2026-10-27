import requests
from django.core.cache import cache


OSRM_URL = "http://router.project-osrm.org/route/v1/driving"


def get_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> dict:
    """
    Single OSRM call. Returns:
      {
        "coordinates": [[lon, lat], ...],   # full route polyline
        "distance_miles": float,
        "duration_seconds": float,
      }
    Cached by rounded coordinates to avoid duplicate calls.
    """
    cache_key = f"route:{start_lat:.4f},{start_lon:.4f}:{end_lat:.4f},{end_lon:.4f}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    url = f"{OSRM_URL}/{start_lon},{start_lat};{end_lon},{end_lat}"
    response = requests.get(
        url,
        params={"overview": "simplified", "geometries": "geojson", "steps": "false"},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    if data.get("code") != "Ok":
        raise ValueError(f"Routing error: {data.get('message', 'unknown')}")

    route = data["routes"][0]
    result = {
        "coordinates": route["geometry"]["coordinates"],
        "distance_miles": route["distance"] * 0.000621371,
        "duration_seconds": route["duration"],
    }

    cache.set(cache_key, result, 3600)
    return result
