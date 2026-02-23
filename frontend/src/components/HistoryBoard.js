import FlightRow from "./FlightRow";

function HistoryBoard({ flights, error }) {
  return (
    <div className="board">
      <div className="board-header">
        <h1>✈ History — Rosh Pina 28</h1>
        <span className="updated">{flights.length} flights in last 24h</span>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="board-columns">
        <span>Flight</span>
        <span>Route</span>
        <span>Aircraft</span>
        <span>Altitude</span>
        <span>Speed</span>
        <span>Heading</span>
        <span>Time</span>
      </div>

      <div className="board-body">
        {flights.length === 0 ? (
          <div className="no-flights">No flight history yet</div>
        ) : (
          flights.map((f) => (
            <div className="flight-row" key={f.id}>
              <span className="callsign">{f.callsign}</span>
              <span className="route">
                {f.origin || "???"} → {f.destination || "???"}
              </span>
              <span className="aircraft">{f.aircraft || "—"}</span>
              <span className="altitude">{f.altitude_ft ? `${f.altitude_ft.toLocaleString()} ft` : "—"}</span>
              <span className="speed">{f.speed_kts ? `${f.speed_kts} kts` : "—"}</span>
              <span className="heading">{f.heading_deg ? `${f.heading_deg}°` : "—"}</span>
              <span className="time">
                {f.updated_at
                  ? new Date(f.updated_at).toLocaleTimeString("he-IL", {
                      hour: "2-digit",
                      minute: "2-digit",
                      timeZone: "Asia/Jerusalem",
                    })
                  : "—"}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default HistoryBoard;