import FlightRow from "./FlightRow";

function FlightBoard({ flights, updatedAt, error }) {
  const time = updatedAt ? new Date(updatedAt).toLocaleTimeString() : "—";

  return (
    <div className="board">
      <div className="board-header">
        <h1>✈ Tel Aviv — Rosh Pina 28</h1>
        <span className="updated">Last update: {time}</span>
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
          <div className="no-flights">No flights overhead right now</div>
        ) : (
          flights.map((f) => <FlightRow key={f.id} flight={f} />)
        )}
      </div>
    </div>
  );
}

export default FlightBoard;