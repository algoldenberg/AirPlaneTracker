import FlightRow from "./FlightRow";

const AREA_TRANSLATIONS = {
  "תל אביב - דרום": "Tel Aviv - South",
  "תל אביב - מרכז העיר": "Tel Aviv - City Center",
  "תל אביב - מזרח": "Tel Aviv - East",
  "תל אביב - יפו": "Tel Aviv - Jaffa",
  "תל אביב - דרום העיר ויפו": "Tel Aviv - South & Jaffa",
};

const TITLE_TRANSLATIONS = {
  "ירי רקטות וטילים": "Rocket & Missile Fire",
  "חדירת כלי טיס עוין": "Hostile Aircraft Intrusion",
  "רעידת אדמה": "Earthquake",
  "חשד לחדירת מחבלים": "Suspected Terrorist Infiltration",
  "אירוע חומרים מסוכנים": "Hazardous Materials Incident",
  "התרעה בשל גל צונמי": "Tsunami Warning",
};

function translateArea(area) {
  return AREA_TRANSLATIONS[area] || area;
}

function translateTitle(title) {
  return TITLE_TRANSLATIONS[title] || title;
}

function FlightBoard({ flights, updatedAt, error, alert }) {
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
        {alert ? (
          <div className="alert-inside">
            <span className="alert-icon">🚨</span>
            <div className="alert-content">
              <span className="alert-title">
                RED ALERT — {translateTitle(alert.title)}
              </span>
              <span className="alert-areas">
                {alert.areas.map(translateArea).join(", ")}
              </span>
            </div>
          </div>
        ) : flights.length === 0 ? (
          <div className="no-flights">No flights overhead right now</div>
        ) : (
          flights.map((f) => <FlightRow key={f.id} flight={f} />)
        )}
      </div>
    </div>
  );
}

export default FlightBoard;