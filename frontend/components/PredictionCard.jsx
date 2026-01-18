import React from "react";

const DEFAULT_SEASON = "20242025";
const PLACEHOLDER = "https://via.placeholder.com/140x140.png?text=No+Image";
// stat labels for prediction card
const STAT_LABELS = {
  goals: "Goals",
  assists: "Assists",
  points: "Points",
  shots: "Shots",
  ppGoals: "Power Play Goals",
  shGoals: "Shorthanded Goals",
  hits: "Hits",
  blocked: "Shots Blocked",
  faceoffPct: "Faceoff Win %",
  timeOnIce: "Time On Ice",
};
// converts seconds to a mm:ss format
const formatTimeOnIce = (seconds) => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
};
// format stat value based on its type
const formatStatValue = (key, value) => {
  if (key === "timeOnIce") {
    return formatTimeOnIce(value);
  }
  if (key === "faceoffPct") {
    return `${(value * 100).toFixed(1)}%`;
  }
  return typeof value === "number" ? value.toFixed(2) : String(value);
};

export default function PredictionCard({ player, prediction }) {
  if (!prediction || !player) return null;

  const preds = prediction.predictions || prediction;
  const team = player.team || "unknown";
  const id = player.id;
  const name = player.name || player.fullName || "Player";
  // player image from NHL API
  const imageUrl = `https://assets.nhle.com/mugs/nhl/${DEFAULT_SEASON}/${team}/${id}.png`;

  return (
    <div className="prediction-card">
      <img
        src={imageUrl}
        alt={name}
        onError={(e) => {
          e.currentTarget.onerror = null;
          e.currentTarget.src = PLACEHOLDER;
        }}
        className="player-image"
      />
      <div>
        <h2 className="player-name">{name} {team ? `- ${team}` : ""}</h2>
        <div className="stats-list">
          {Object.entries(preds).map(([k, v]) => (
            <div key={k}>
              <strong className="stat-label">{STAT_LABELS[k] || k}:</strong>
              <span className="stat-value">{formatStatValue(k, v)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}