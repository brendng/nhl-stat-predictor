import React, { useState } from "react";
import SearchBar from "../components/SearchBar.jsx";
import PredictionCard from "../components/PredictionCard.jsx";
import rawPlayers from "../../player_id_mapping.json";

export default function App() {
  // normalize the input mapping into an array formatted as { id, fullName, team, shortName }
  const playersArray = Array.isArray(rawPlayers) ? rawPlayers.map((p) => ({
        id: Number(p.id),
        fullName: p.fullName || p.name || p.shortName || String(p.id),
        team: p.team || p.teamAbbrev || null,
        shortName: p.shortName || p.name || p.fullName || null,
      })): Object.entries(rawPlayers).map(([id, shortName]) => ({
        id: Number(id),
        fullName: shortName, // fallback in case full name isn't obtained
        team: null,
        shortName,
      }));

  const [selectedPlayer, setSelectedPlayer] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const handleSelect = async (player) => {
    setSelectedPlayer(player);
    setPrediction(null);
    setError(null);
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:5000/predict/${player.id}`);
      if (!res.ok) throw new Error(`status ${res.status}`);
      const data = await res.json();
      setPrediction(data);
    } 
    catch (err) {
      setError(String(err));
    } 
    finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <div className="app-header">
        <img src="../src/images/nhl_logo.png" alt="NHL Logo"/>
        <div className="app-title">
          <span>NHL Statline Predictor</span>
          <span className="app-subtitle">- by Brendan Ng</span>
        </div>
      </div>
      <p className="app-description">Search for players from the 2024-2025 NHL season! (sorry no goalies stats yet :( )<br></br><br></br><i>(Note: Please be patient while the backend loads data :) )</i></p>
      <SearchBar players={playersArray} onSelect={handleSelect} />
      {loading && <div className="loading">Loading…</div>}
      {error && <div className="error">Error: {error}</div>}
      {prediction && (
        <PredictionCard player={selectedPlayer} prediction={prediction} />
      )}
    </div>
  );
}