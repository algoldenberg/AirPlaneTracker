# ✈️ AirPlaneTracker

Real-time flight tracker that monitors aircraft flying over a specific location and displays them on an airport-style departure board.

Built as a microservices portfolio project.

🌐 **Live:** [roshpinaoverhead.online](https://roshpinaoverhead.online)

---

## 🏗️ Architecture
```
┌─────────────┐     ┌───────┐     ┌─────────────┐     ┌──────────┐
│   tracker   │────▶│ Redis │────▶│     api     │────▶│ frontend │
│  (Python)   │     │       │     │  (FastAPI)  │     │  (React) │
└─────────────┘     └───────┘     └─────────────┘     └──────────┘
                                                              │
                                                       ┌──────────┐
                                                       │  nginx   │
                                                       │ (proxy)  │
                                                       └──────────┘
```

- **tracker** — polls FlightRadar24 every 5 seconds, saves flights to Redis
- **api** — FastAPI service, reads from Redis and exposes REST endpoints
- **frontend** — React app, production build served by nginx
- **redis** — message store between tracker and api
- **nginx** — reverse proxy, routes `/api/` to backend and `/` to frontend

---

## 🚀 Getting Started

### Requirements
- Docker + Docker Compose

### Run
```bash
docker-compose up --build
```

App will be available at `http://localhost:8080`  
API will be available at `http://localhost:8080/api`

---

## 📡 API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/flights` | All current flights overhead |
| GET | `/api/flights/history` | All flights seen in last 24h |
| GET | `/api/flights/{id}` | Single flight by ID |
| GET | `/api/status` | Tracker status |

---

## 🔄 CI/CD

Automatically deploys to VPS on every push to `master` via GitHub Actions.

---

## 🙏 Credits

Flight data powered by [FlightRadarAPI](https://github.com/JeanExtreme002/FlightRadarAPI) — unofficial SDK for FlightRadar24 by [@JeanExtreme002](https://github.com/JeanExtreme002).