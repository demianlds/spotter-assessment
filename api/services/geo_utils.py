import math


def haversine_miles(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Straight-line distance in miles between two lon/lat points."""
    R = 3958.8
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def build_waypoints(coordinates: list) -> list[tuple[float, float, float]]:
    """
    Given [[lon, lat], ...] route coordinates, return
    [(lon, lat, cumulative_miles), ...] with running distance.
    """
    waypoints = []
    cumulative = 0.0
    for i, coord in enumerate(coordinates):
        lon, lat = coord[0], coord[1]
        if i > 0:
            prev = coordinates[i - 1]
            cumulative += haversine_miles(prev[0], prev[1], lon, lat)
        waypoints.append((lon, lat, cumulative))
    return waypoints


def project_stations(waypoints: list, stations, buffer_miles: float = 25.0) -> list:
    """
    For each station, find the nearest route waypoint.
    Return [(route_miles, station), ...] sorted by route position,
    only for stations within buffer_miles of the route.
    """
    if not waypoints or not stations:
        return []

    lons = [w[0] for w in waypoints]
    lats = [w[1] for w in waypoints]
    lat_buf = buffer_miles / 69.0
    lon_buf = buffer_miles / 55.0
    min_lat, max_lat = min(lats) - lat_buf, max(lats) + lat_buf
    min_lon, max_lon = min(lons) - lon_buf, max(lons) + lon_buf

    result = []
    for station in stations:
        if not (min_lat <= station.lat <= max_lat and min_lon <= station.lon <= max_lon):
            continue

        best_dist = float("inf")
        best_pos = 0.0
        for wp_lon, wp_lat, wp_miles in waypoints:
            d = haversine_miles(wp_lon, wp_lat, station.lon, station.lat)
            if d < best_dist:
                best_dist = d
                best_pos = wp_miles

        if best_dist <= buffer_miles:
            result.append((best_pos, station))

    result.sort(key=lambda x: x[0])
    return result
