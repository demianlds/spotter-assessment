import requests
from django.core.cache import cache


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "SpotterFuelOptimizer/1.0 (assessment)"}


def geocode(location: str) -> tuple[float, float]:
    """Return (lat, lon) for a US city/state string. Cached for 24h."""
    cache_key = f"geo:{location.lower().strip()}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    response = requests.get(
        NOMINATIM_URL,
        params={"q": location, "format": "json", "limit": 1, "countrycodes": "us"},
        headers=HEADERS,
        timeout=10,
    )
    response.raise_for_status()
    results = response.json()

    if not results:
        raise ValueError(f"Could not geocode '{location}'. Try a more specific US location.")

    lat = float(results[0]["lat"])
    lon = float(results[0]["lon"])
    cache.set(cache_key, (lat, lon), 86400)
    return lat, lon
