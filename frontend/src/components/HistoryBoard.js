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
      </div>

      <div className="board-body">
        {flights.length === 0 ? (
          <div className="no-flights">No flight history yet</div>
        ) : (
          flights.map((f) => <FlightRow key={f.id} flight={f} />)
        )}
      </div>
    </div>
  );
}

export default HistoryBoard;