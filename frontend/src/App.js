import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import FlightBoard from "./components/FlightBoard";
import HistoryBoard from "./components/HistoryBoard";

const API_URL = "/api";

function LivePage() {
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

  return <FlightBoard flights={flights} updatedAt={updatedAt} error={error} />;
}

function HistoryPage() {
  const [flights, setFlights] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await fetch(`${API_URL}/flights/history`);
        const data = await res.json();
        setFlights(data.flights);
        setError(null);
      } catch (e) {
        setError("Нет связи с сервером");
      }
    };

    fetchHistory();
  }, []);

  return <HistoryBoard flights={flights} error={error} />;
}

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <nav className="nav">
          <Link to="/">Live</Link>
          <Link to="/history">History</Link>
        </nav>
        <Routes>
          <Route path="/" element={<LivePage />} />
          <Route path="/history" element={<HistoryPage />} />
        </Routes>
        <footer className="footer">
          <a href="https://github.com/algoldenberg/AirPlaneTracker" target="_blank" rel="noreferrer">GitHub</a>
          {" · "}
          <a href="https://github.com/algoldenberg/AirPlaneTracker/blob/master/LICENSE" target="_blank" rel="noreferrer">MIT License</a>
          {" · "}
          © 2026 Alex Goldenberg
        </footer>
      </div>
    </BrowserRouter>
  );
}

export default App;