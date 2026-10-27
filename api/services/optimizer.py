MAX_RANGE_MILES = 500.0
MPG = 10.0
TANK_GALLONS = MAX_RANGE_MILES / MPG  # 50 gallons


def optimize(stations_on_route: list, total_miles: float) -> list[dict]:
    """
    Greedy fuel stop optimizer.

    Strategy: at each position, scan all reachable stations (within current range).
    Pick the cheapest one. If destination is reachable without stopping, done.
    Fill to full tank at each stop.

    stations_on_route: [(route_miles, FuelStation), ...] sorted by route_miles
    Returns: list of stop dicts ready for API response.
    """
    stops = []
    pos = 0.0
    fuel_miles = MAX_RANGE_MILES  # start with full tank

    while True:
        if pos + fuel_miles >= total_miles:
            break  # can reach destination

        reachable = [
            (dist, s)
            for dist, s in stations_on_route
            if pos < dist <= pos + fuel_miles
        ]

        if not reachable:
            raise ValueError(
                f"No fuel stations found within {MAX_RANGE_MILES:.0f} miles of mile marker "
                f"{pos:.0f}. Add more station data or increase buffer distance."
            )

        cheapest_dist, station = min(reachable, key=lambda x: x[1].price_per_gallon)

        miles_to_station = cheapest_dist - pos
        fuel_on_arrival_gallons = (fuel_miles - miles_to_station) / MPG
        gallons_to_fill = round(TANK_GALLONS - fuel_on_arrival_gallons, 3)
        stop_cost = round(gallons_to_fill * station.price_per_gallon, 2)

        stops.append({
            "station_name": station.name,
            "address": station.address,
            "city": station.city,
            "state": station.state,
            "lat": station.lat,
            "lon": station.lon,
            "route_mile": round(cheapest_dist, 1),
            "gallons_filled": gallons_to_fill,
            "price_per_gallon": station.price_per_gallon,
            "stop_cost_usd": stop_cost,
        })

        fuel_miles = MAX_RANGE_MILES
        pos = cheapest_dist

    return stops
