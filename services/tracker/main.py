import os
import time
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
import redis
from FlightRadar24 import FlightRadar24API

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("tracker")

HOME_LAT        = float(os.getenv("HOME_LAT"))
HOME_LON        = float(os.getenv("HOME_LON"))
RADIUS_METERS   = int(os.getenv("RADIUS_METERS"))
UPDATE_INTERVAL = int(os.getenv("UPDATE_INTERVAL"))
REDIS_HOST      = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT      = int(os.getenv("REDIS_PORT", 6379))


def parse_flight(flight) -> dict:
    return {
        "id":           flight.id,
        "callsign":     getattr(flight, "callsign", None) or "—",
        "airline_icao": getattr(flight, "airline_icao", None),
        "aircraft":     getattr(flight, "aircraft_code", None),
        "registration": getattr(flight, "registration", None),
        "origin":       getattr(flight, "origin_airport_iata", None),
        "destination":  getattr(flight, "destination_airport_iata", None),
        "latitude":     getattr(flight, "latitude", None),
        "longitude":    getattr(flight, "longitude", None),
        "altitude_ft":  getattr(flight, "altitude", None),
        "speed_kts":    getattr(flight, "ground_speed", None),
        "heading_deg":  getattr(flight, "heading", None),
        "vertical_speed": getattr(flight, "vertical_speed", None),
        "on_ground":    bool(getattr(flight, "on_ground", False)),
        "updated_at":   datetime.now().isoformat(),
    }


def main():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    fr = FlightRadar24API()
    log.info(f"Tracker started. Radius: {RADIUS_METERS}m, interval: {UPDATE_INTERVAL}s")

    while True:
        try:
            bounds  = fr.get_bounds_by_point(HOME_LAT, HOME_LON, RADIUS_METERS)
            flights = fr.get_flights(bounds=bounds)

            airborne = [parse_flight(f) for f in flights if not getattr(f, "on_ground", False)]

            r.set("flights:current", json.dumps(airborne))
            r.set("flights:updated_at", datetime.now().isoformat())

            log.info(f"✈  {len(airborne)} flights saved to Redis")

        except Exception as e:
            log.error(f"Error: {e}")

        time.sleep(UPDATE_INTERVAL)


if __name__ == "__main__":
    main()