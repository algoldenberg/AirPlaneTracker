import os
import json
import time
import logging
import redis
import sqlite3

from datetime import datetime
from FlightRadar24 import FlightRadar24API
from dotenv import load_dotenv

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
DB_PATH         = os.getenv("DB_PATH", "/data/flights.db")

MIN_ALT = 1200
MAX_ALT = 3000
MIN_HDG = 85
MAX_HDG = 130


def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id          TEXT PRIMARY KEY,
            callsign    TEXT,
            airline_icao TEXT,
            aircraft    TEXT,
            registration TEXT,
            origin      TEXT,
            destination TEXT,
            latitude    REAL,
            longitude   REAL,
            altitude_ft INTEGER,
            speed_kts   INTEGER,
            heading_deg INTEGER,
            vertical_speed INTEGER,
            seen_at     REAL  -- unix timestamp
        )
    """)
    conn.commit()


def parse_flight(flight) -> dict:
    return {
        "id":             flight.id,
        "callsign":       getattr(flight, "callsign", None) or "—",
        "airline_icao":   getattr(flight, "airline_icao", None),
        "aircraft":       getattr(flight, "aircraft_code", None),
        "registration":   getattr(flight, "registration", None),
        "origin":         getattr(flight, "origin_airport_iata", None),
        "destination":    getattr(flight, "destination_airport_iata", None),
        "latitude":       getattr(flight, "latitude", None),
        "longitude":      getattr(flight, "longitude", None),
        "altitude_ft":    getattr(flight, "altitude", None),
        "speed_kts":      getattr(flight, "ground_speed", None),
        "heading_deg":    getattr(flight, "heading", None),
        "vertical_speed": getattr(flight, "vertical_speed", None),
        "on_ground":      bool(getattr(flight, "on_ground", False)),
        "updated_at":     datetime.now(tz=__import__('zoneinfo').ZoneInfo("Asia/Jerusalem")).isoformat(),
    }


def is_landing(flight: dict) -> bool:
    alt         = flight.get("altitude_ft") or 0
    hdg         = flight.get("heading_deg") or 0
    origin      = flight.get("origin") or ""
    destination = flight.get("destination") or ""

    if not (MIN_ALT <= alt <= MAX_ALT):
        return False
    if not (MIN_HDG <= hdg <= MAX_HDG):
        return False
    if destination and destination != "TLV":
        return False
    if origin == "TLV":
        return False

    return True


def main():
    r   = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    fr  = FlightRadar24API()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    init_db(conn)

    log.info(f"Tracker started. Radius: {RADIUS_METERS}m, interval: {UPDATE_INTERVAL}s")

    while True:
        try:
            bounds   = fr.get_bounds_by_point(HOME_LAT, HOME_LON, RADIUS_METERS)
            flights  = fr.get_flights(bounds=bounds)
            airborne = [parse_flight(f) for f in flights if not getattr(f, "on_ground", False)]
            landing  = [f for f in airborne if is_landing(f)]

            r.set("flights:current", json.dumps(landing))
            r.set("flights:updated_at", datetime.now(tz=__import__('zoneinfo').ZoneInfo("Asia/Jerusalem")).isoformat())

            now_ts = time.time()

            for flight in landing:
                existing = conn.execute(
                    "SELECT id FROM history WHERE id = ?", (flight["id"],)
                ).fetchone()
                if not existing:
                    conn.execute("""
                        INSERT INTO history VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (
                        flight["id"], flight["callsign"], flight["airline_icao"],
                        flight["aircraft"], flight["registration"],
                        flight["origin"], flight["destination"],
                        flight["latitude"], flight["longitude"],
                        flight["altitude_ft"], flight["speed_kts"],
                        flight["heading_deg"], flight["vertical_speed"],
                        now_ts
                    ))
                    conn.commit()
                    log.info(f"📝 Logged: {flight['callsign']}  {flight['origin']} → {flight['destination']}  {flight['altitude_ft']}ft")

            # Удаляем записи старше 24 часов
            cutoff_ts = now_ts - 86400
            removed = conn.execute(
                "DELETE FROM history WHERE seen_at < ?", (cutoff_ts,)
            ).rowcount
            conn.commit()
            if removed:
                log.info(f"🗑  Removed {removed} old records at {datetime.now(tz=__import__('zoneinfo').ZoneInfo('Asia/Jerusalem')).strftime('%Y-%m-%d %H:%M:%S')}")

            log.info(f"✈  {len(landing)} flights overhead")

        except Exception as e:
            log.error(f"Error: {e}")

        time.sleep(UPDATE_INTERVAL)


if __name__ == "__main__":
    main()