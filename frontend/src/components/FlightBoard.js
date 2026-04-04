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
  "בדקות הקרובות צפויות להתקבל התרעות באזורך": "Alerts expected in your area soon",
  "האירוע הסתיים": "Event Ended",
};

function translateArea(area) {
  return AREA_TRANSLATIONS[area] || area;
}

function translateTitle(title) {
  return TITLE_TRANSLATIONS[title] || title;
}

function getAlertConfig(cat, title, areas) {
  const cat_s = String(cat);
  const areasEn = areas.map(translateArea).join(", ");

  if (cat_s === "10" || cat_s === "13") {  // event ended
    return {
      className: "alert-inside alert-green",
      icon: "✅",
      heading: "ALL CLEAR — Event Has Ended",
      sub: "See you next time! 🐕",
      areas: areasEn,
    };
  }
  if (cat_s === "14") {
    return {
      className: "alert-inside alert-orange",
      icon: "⚠️",
      heading: "PRE-ALERT — " + translateTitle(title),
      sub: "Please proceed to the nearest shelter!",
      areas: areasEn,
    };
  }
  // cat=1 и остальные — основная сирена
  return {
    className: "alert-inside alert-red",
    icon: "🚨",
    heading: "RED ALERT — " + translateTitle(title),
    sub: null,
    areas: areasEn,
  };
}

function FlightBoard({ flights, updatedAt, error, alert }) {
  const time = updatedAt ? new Date(updatedAt).toLocaleTimeString() : "—";
  const cfg  = alert ? getAlertConfig(alert.cat, alert.title, alert.areas) : null;

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
          <div className={cfg.className}>
            <span className="alert-icon">{cfg.icon}</span>
            <div className="alert-content">
              <span className="alert-title">{cfg.heading}</span>
              <span className="alert-areas">{cfg.areas}</span>
              {cfg.sub && <span className="alert-sub">{cfg.sub}</span>}
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