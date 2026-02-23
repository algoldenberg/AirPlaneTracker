RADIUS_METERS   = int(os.getenv("RADIUS_METERS"))
UPDATE_INTERVAL = int(os.getenv("UPDATE_INTERVAL"))
REDIS_HOST      = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT      = int(os.getenv("REDIS_PORT", 6379))

# Фильтры посадочной глиссады
MIN_ALT = 1600
MAX_ALT = 2500
MIN_HDG = 85
MAX_HDG = 130


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
    alt = flight.get("altitude_ft") or 0
    hdg = flight.get("heading_deg") or 0
    origin = flight.get("origin") or ""
    destination = flight.get("destination") or ""

    # Высота в диапазоне глиссады
    if not (MIN_ALT <= alt <= MAX_ALT):
        return False

    # Курс в диапазоне посадки
    if not (MIN_HDG <= hdg <= MAX_HDG):
        return False

    # Летит в TLV или destination неизвестен
    if destination and destination != "TLV":
        return False

    # Не вылетает из TLV
    if origin == "TLV":
        return False

    return True


def main():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    fr = FlightRadar24API()
    log.info(f"Tracker started. Radius: {RADIUS_METERS}m, interval: {UPDATE_INTERVAL}s")

    while True:
        try:
            bounds   = fr.get_bounds_by_point(HOME_LAT, HOME_LON, RADIUS_METERS)
            flights  = fr.get_flights(bounds=bounds)
            airborne = [parse_flight(f) for f in flights if not getattr(f, "on_ground", False)]

            # Фильтруем только посадочные рейсы
            landing = [f for f in airborne if is_landing(f)]

            # Текущие рейсы
            r.set("flights:current", json.dumps(landing))
            r.set("flights:updated_at", datetime.now(tz=__import__('zoneinfo').ZoneInfo("Asia/Jerusalem")).isoformat())

            # История — каждый новый самолёт пишем один раз
            for flight in landing:
                key = f"flights:history:{flight['id']}"
                if not r.exists(key):
                    r.lpush("flights:history:list", json.dumps(flight))
                    r.set(key, "1")
                    r.expire(key, 86400)
                    log.info(f"📝 Logged: {flight['callsign']}  {flight['origin']} → {flight['destination']}  {flight['altitude_ft']}ft")

            log.info(f"✈  {len(landing)} flights overhead")

        except Exception as e:
            log.error(f"Error: {e}")

        time.sleep(UPDATE_INTERVAL)


if __name__ == "__main__":
    main()