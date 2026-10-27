import csv
import io
import requests
from django.core.management.base import BaseCommand, CommandError
from api.models import FuelStation

_geo_cache: dict = {}
_city_lookup: dict = {}

US_CITIES_CSV = (
    "https://raw.githubusercontent.com/kelvins/US-Cities-Database/main/csv/us_cities.csv"
)


def build_lookup():
    """Download US cities lat/lon from GitHub once and build lookup dict."""
    global _city_lookup
    if _city_lookup:
        return

    r = requests.get(US_CITIES_CSV, timeout=30)
    r.raise_for_status()

    reader = csv.DictReader(io.StringIO(r.text))
    for row in reader:
        key = (row["CITY"].lower().strip(), row["STATE_CODE"].lower().strip())
        if key not in _city_lookup:
            try:
                _city_lookup[key] = (float(row["LATITUDE"]), float(row["LONGITUDE"]))
            except (ValueError, KeyError):
                pass


def geocode_city_state(city: str, state: str) -> tuple[float, float] | None:
    key = f"{city.lower().strip()},{state.lower().strip()}"
    if key in _geo_cache:
        return _geo_cache[key]

    result = _city_lookup.get((city.lower().strip(), state.lower().strip()))
    _geo_cache[key] = result
    return result


def detect_columns(headers: list[str]) -> dict:
    """Detect CSV column names flexibly (case-insensitive)."""
    h = {col.strip().lower(): i for i, col in enumerate(headers)}

    def find(*candidates):
        for c in candidates:
            if c in h:
                return h[c]
        return None

    return {
        "name":  find("truckstop name", "opis truckstop name", "name", "station name", "truckstopname"),
        "address": find("address", "street", "addr"),
        "city":  find("city"),
        "state": find("state"),
        "price": find("retail price", "rack price", "price", "price_per_gallon", "retail"),
        "lat":   find("latitude", "lat"),
        "lon":   find("longitude", "lon", "lng"),
    }


class Command(BaseCommand):
    help = "Load fuel stations from the provided CSV file."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Path to the fuel prices CSV")
        parser.add_argument("--clear", action="store_true", help="Clear existing data before loading")

    def handle(self, *args, **options):
        csv_path = options["csv_path"]

        if options["clear"]:
            deleted, _ = FuelStation.objects.all().delete()
            self.stdout.write(f"Cleared {deleted} existing stations.")

        try:
            f = open(csv_path, newline="", encoding="utf-8-sig")
        except FileNotFoundError:
            raise CommandError(f"File not found: {csv_path}")

        with f:
            reader = csv.reader(f)
            headers = next(reader)
            cols = detect_columns(headers)

            if cols["name"] is None or cols["city"] is None or cols["state"] is None or cols["price"] is None:
                raise CommandError(
                    f"Could not detect required columns (name, city, state, price).\n"
                    f"Found: {headers}"
                )

            has_coords = cols["lat"] is not None and cols["lon"] is not None

            rows = list(reader)

            if not has_coords:
                self.stdout.write("No lat/lon columns — downloading US cities lookup from GitHub...")
                build_lookup()
                self.stdout.write(f"Lookup ready: {len(_city_lookup)} cities.")

            stations = []
            skipped = 0

            for i, row in enumerate(rows):
                try:
                    name  = row[cols["name"]].strip()
                    city  = row[cols["city"]].strip()
                    state = row[cols["state"]].strip()
                    price = float(row[cols["price"]].replace("$", "").strip())
                    addr  = row[cols["address"]].strip() if cols["address"] is not None else ""

                    if has_coords:
                        lat = float(row[cols["lat"]])
                        lon = float(row[cols["lon"]])
                    else:
                        coords = geocode_city_state(city, state)
                        if coords is None:
                            skipped += 1
                            continue
                        lat, lon = coords

                    stations.append(FuelStation(
                        name=name, address=addr, city=city,
                        state=state, lat=lat, lon=lon,
                        price_per_gallon=price,
                    ))

                    if len(stations) % 500 == 0:
                        FuelStation.objects.bulk_create(stations, ignore_conflicts=True)
                        self.stdout.write(f"  Inserted {len(stations)} stations...")
                        stations = []

                except (ValueError, IndexError):
                    skipped += 1

            if stations:
                FuelStation.objects.bulk_create(stations, ignore_conflicts=True)

        total = FuelStation.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f"Done. {total} stations in DB. ({skipped} rows skipped)"
        ))
