function FlightRow({ flight }) {
    return (
      <div className="flight-row">
        <span className="callsign">{flight.callsign}</span>
        <span className="route">
          {flight.origin || "???"} → {flight.destination || "???"}
        </span>
        <span className="aircraft">{flight.aircraft || "—"}</span>
        <span className="altitude">{flight.altitude_ft} ft</span>
        <span className="speed">{flight.speed_kts} kts</span>
        <span className="heading">{flight.heading_deg}°</span>
      </div>
    );
  }
  
  export default FlightRow;