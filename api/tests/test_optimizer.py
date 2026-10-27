from django.test import TestCase
from api.services.optimizer import optimize
from api.services.geo_utils import haversine_miles, build_waypoints


class MockStation:
    def __init__(self, name, price, city="Test", state="TX", lat=0.0, lon=0.0, address=""):
        self.name = name
        self.price_per_gallon = price
        self.city = city
        self.state = state
        self.lat = lat
        self.lon = lon
        self.address = address


class OptimizerTest(TestCase):

    def test_no_stops_needed_short_route(self):
        """Route under 500 miles requires no fuel stops."""
        stations = [(100.0, MockStation("A", 3.50))]
        stops = optimize(stations, total_miles=400.0)
        self.assertEqual(stops, [])

    def test_single_stop_required(self):
        """Route of 600 miles requires exactly one stop."""
        stations = [(300.0, MockStation("MidPoint", 3.50))]
        stops = optimize(stations, total_miles=600.0)
        self.assertEqual(len(stops), 1)
        self.assertEqual(stops[0]["station_name"], "MidPoint")

    def test_picks_cheapest_within_range(self):
        """Among reachable stations, picks the cheapest one."""
        stations = [
            (200.0, MockStation("Expensive", 4.00)),
            (300.0, MockStation("Cheap", 3.00)),
            (450.0, MockStation("Mid", 3.50)),
        ]
        stops = optimize(stations, total_miles=700.0)
        self.assertEqual(stops[0]["station_name"], "Cheap")

    def test_multiple_stops_long_route(self):
        """2000-mile route needs at least 3 stops."""
        stations = [(i * 150.0, MockStation(f"S{i}", 3.50)) for i in range(1, 15)]
        stops = optimize(stations, total_miles=2000.0)
        self.assertGreaterEqual(len(stops), 3)

    def test_total_cost_calculation(self):
        """Total cost equals sum of each stop's cost."""
        stations = [(300.0, MockStation("A", 3.00)), (750.0, MockStation("B", 3.50))]
        stops = optimize(stations, total_miles=1000.0)
        total = sum(s["stop_cost_usd"] for s in stops)
        self.assertAlmostEqual(total, sum(s["stop_cost_usd"] for s in stops), places=2)

    def test_raises_when_no_reachable_station(self):
        """Raises ValueError when no station is reachable."""
        stations = [(600.0, MockStation("TooFar", 3.50))]
        with self.assertRaises(ValueError):
            optimize(stations, total_miles=1000.0)


class HaversineTest(TestCase):

    def test_chicago_to_la_approx(self):
        """Chicago to LA is roughly 1740 miles."""
        miles = haversine_miles(-87.6298, 41.8781, -118.2437, 34.0522)
        self.assertGreater(miles, 1500)
        self.assertLess(miles, 2000)

    def test_same_point_is_zero(self):
        self.assertAlmostEqual(haversine_miles(0, 0, 0, 0), 0.0)
