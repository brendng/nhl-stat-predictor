import React, { useState } from "react";

export default function SearchBar({ players = [], onSelect }) {
  const [query, setQuery] = useState("");

  // players: [{ id, fullName, team, shortName }]
  const list =
    query.trim().length > 0 ? players.filter((p) => {
            const name = (p.fullName || p.shortName || "").toLowerCase();
            return name.includes(query.toLowerCase());
          }).slice(0, 5): []; // change to limit search bar results

  return (
    <div className="search-container">
      <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search players..."
        className="search-input"
      />
      <ul className="search-results">
        {list.map((p) => (
          <li key={p.id}>
            <button onClick={() => onSelect({id: p.id, name: p.fullName || p.shortName, team: p.team || null,})} className="search-result-button">{p.fullName || p.shortName}
            </button>
          </li>))}
      </ul>
    </div>
  );
}