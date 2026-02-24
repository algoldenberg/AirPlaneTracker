import os
import json
import logging
from datetime import datetime, timedelta, timezone
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

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

app = FastAPI(
    title="✈️ AirPlaneTracker API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/flights")
def get_flights():
    data = r.get("flights:current")
    updated_at = r.get("flights:updated_at")
    if data is None:
        return {"count": 0, "flights": [], "updated_at": None}
    flights = json.loads(data)
    return {
        "count": len(flights),
        "flights": flights,
        "updated_at": updated_at,
    }


@app.get("/flights/history")
def get_history():
    items = r.lrange("flights:history:list", 0, -1)
    flights = [json.loads(item) for item in items]

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    filtered = []
    for f in flights:
        try:
            updated = datetime.fromisoformat(f["updated_at"])
            if updated.tzinfo is None:
                updated = updated.replace(tzinfo=timezone.utc)
            if updated > cutoff:
                filtered.append(f)
        except:
            filtered.append(f)

    return {
        "count": len(filtered),
        "flights": filtered,
    }


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
    data = r.get("flights:current")
    count = len(json.loads(data)) if data else 0
    return {
        "status": "ok",
        "flights_count": count,
        "updated_at": updated_at,
    }