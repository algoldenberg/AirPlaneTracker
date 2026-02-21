import { useState, useEffect } from "react";
import FlightBoard from "./components/FlightBoard";

const API_URL = "http://localhost:8000";

function App() {
  const [flights, setFlights] = useState([]);
  const [updatedAt, setUpdatedAt] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchFlights = async () => {
      try {
        const res = await fetch(`${API_URL}/flights`);
        const data = await res.json();
        setFlights(data.flights);
        setUpdatedAt(data.updated_at);
        setError(null);
      } catch (e) {
        setError("Нет связи с сервером");
      }
    };

    fetchFlights();
    const interval = setInterval(fetchFlights, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="app">
      <FlightBoard flights={flights} updatedAt={updatedAt} error={error} />
    </div>
  );
}

export default App;