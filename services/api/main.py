import os
import json
import time
import logging
import sqlite3
import aiohttp
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
import redis
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("api")

REDIS_HOST   = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT   = int(os.getenv("REDIS_PORT", 6379))
DB_PATH      = os.getenv("DB_PATH", "/data/flights.db")
OREF_URL     = "https://www.oref.org.il/WarningMessages/alert/alerts.json"
TARGET_AREAS = ["תל אביב - דרום", "תל אביב"]

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

app = FastAPI(title="✈️ AirPlaneTracker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_flight(row) -> dict:
    seen_at = row["seen_at"]
    dt = datetime.fromtimestamp(seen_at, tz=ZoneInfo("Asia/Jerusalem"))
    return {
        "id":             row["id"],
        "callsign":       row["callsign"],
        "airline_icao":   row["airline_icao"],
        "aircraft":       row["aircraft"],
        "registration":   row["registration"],
        "origin":         row["origin"],
        "destination":    row["destination"],
        "latitude":       row["latitude"],
        "longitude":      row["longitude"],
        "altitude_ft":    row["altitude_ft"],
        "speed_kts":      row["speed_kts"],
        "heading_deg":    row["heading_deg"],
        "vertical_speed": row["vertical_speed"],
        "updated_at":     dt.isoformat(),
    }


@app.get("/flights")
def get_flights():
    data       = r.get("flights:current")
    updated_at = r.get("flights:updated_at")
    if data is None:
        return {"count": 0, "flights": [], "updated_at": None}
    flights = json.loads(data)
    return {"count": len(flights), "flights": flights, "updated_at": updated_at}


@app.get("/flights/history")
def get_history():
    cutoff_ts = time.time() - 86400
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM history WHERE seen_at > ? ORDER BY seen_at DESC",
            (cutoff_ts,)
        ).fetchall()
        flights = [row_to_flight(row) for row in rows]
    finally:
        conn.close()
    return {"count": len(flights), "flights": flights}


@app.get("/alerts")
async def get_alerts():
    try:
        async with aiohttp.ClientSession(headers={
            "Referer": "https://www.oref.org.il/",
            "X-Requested-With": "XMLHttpRequest",
        }) as session:
            async with session.get(OREF_URL, timeout=aiohttp.ClientTimeout(total=4)) as resp:
                if resp.status != 200:
                    return {"active": False, "areas": []}
                text = await resp.text()
                if not text.strip():
                    return {"active": False, "areas": []}
                data = await resp.json(content_type=None)
                areas = data.get("data", [])
                matched = [a for a in areas if any(t in a for t in TARGET_AREAS)]
                return {"active": bool(matched), "areas": matched}
    except Exception as e:
        log.error(f"Oref error: {e}")
        return {"active": False, "areas": []}


@app.get("/flights/{flight_id}")
def get_flight(flight_id: str):
    data = r.get("flights:current")
    if data is None:
        raise HTTPException(status_code=404, detail="No data yet")
    flights = json.loads(data)
    for f in flights:
        if f["id"] == flight_id:
            return f
    raise HTTPException(status_code=404, detail="Flight not found")


@app.get("/status")
def get_status():
    updated_at = r.get("flights:updated_at")
    data       = r.get("flights:current")
    count      = len(json.loads(data)) if data else 0
    return {"status": "ok", "flights_count": count, "updated_at": updated_at}