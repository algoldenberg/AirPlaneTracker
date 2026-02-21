# ✈️ AirPlaneTracker

Real-time flight tracker that monitors aircraft flying over a specific location and displays them on an airport-style departure board.

Built as a microservices portfolio project.

---

## 🏠 Tracked Location

**Tel Aviv, Rosh Pina 28**  
Coordinates: `32.0586944213453, 34.78301621182533`  
Radius: `1 km`

---

## 🏗️ Architecture
```
┌─────────────┐     ┌───────┐     ┌─────────────┐     ┌──────────┐
│   tracker   │────▶│ Redis │────▶│     api     │────▶│ frontend │
│  (Python)   │     │       │     │  (FastAPI)  │     │  (React) │
└─────────────┘     └───────┘     └─────────────┘     └──────────┘
```

- **tracker** — polls FlightRadar24 every 10 seconds, saves flights to Redis
- **api** — FastAPI service, reads from Redis and exposes REST endpoints  
- **frontend** — React app, polls the API every 10 seconds and displays a live board
- **redis** — message store between tracker and api

---

## 🚀 Getting Started

### Requirements
- Docker + Docker Compose
- Node.js 18+

### Run backend
```bash
docker-compose up --build
```

### Run frontend
```bash
cd frontend && npm start
```

Frontend: `http://localhost:3000`  
API: `http://localhost:8000`

---

## 📡 API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/flights` | All current flights overhead |
| GET | `/flights/history` | All flights seen in last 24h |
| GET | `/flights/{id}` | Single flight by ID |
| GET | `/status` | Tracker status |

---

## 🙏 Credits

Flight data powered by [FlightRadarAPI](https://github.com/JeanExtreme002/FlightRadarAPI) — unofficial SDK for FlightRadar24 by [@JeanExtreme002](https://github.com/JeanExtreme002).