from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import FuelStation
from .services.geocoding import geocode
from .services.routing import get_route
from .services.geo_utils import build_waypoints, project_stations
from .services.optimizer import optimize


class FuelPlanView(APIView):
    def post(self, request):
        start = request.data.get("start", "").strip()
        end = request.data.get("end", "").strip()

        if not start or not end:
            return Response(
                {"error": "Both 'start' and 'end' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cache_key = f"fuelplan:{start.lower()}:{end.lower()}"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        try:
            start_lat, start_lon = geocode(start)
            end_lat, end_lon = geocode(end)

            route_data = get_route(start_lat, start_lon, end_lat, end_lon)
            coordinates = route_data["coordinates"]
            total_miles = route_data["distance_miles"]

            waypoints = build_waypoints(coordinates)

            # Pre-filter by bounding box in DB before Python processing
            lats = [w[1] for w in waypoints]
            lons = [w[0] for w in waypoints]
            stations = list(FuelStation.objects.filter(
                lat__gte=min(lats) - 0.5,
                lat__lte=max(lats) + 0.5,
                lon__gte=min(lons) - 0.5,
                lon__lte=max(lons) + 0.5,
            ))

            if not stations:
                return Response(
                    {"error": "No fuel stations found near this route. Make sure data is loaded with: python manage.py load_fuel_data data/<your-file>.csv"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            stations_on_route = project_stations(waypoints, stations)
            stops = optimize(stations_on_route, total_miles)

            total_cost = round(sum(s["stop_cost_usd"] for s in stops), 2)
            total_gallons = round(sum(s["gallons_filled"] for s in stops), 2)

            result = {
                "route": {
                    "type": "LineString",
                    "coordinates": coordinates,
                },
                "summary": {
                    "start": start,
                    "end": end,
                    "total_distance_miles": round(total_miles, 1),
                    "total_fuel_cost_usd": total_cost,
                    "total_gallons": total_gallons,
                    "stops_count": len(stops),
                },
                "fuel_stops": stops,
            }
            cache.set(cache_key, result, 3600)
            return Response(result)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
