import React from "react";

const ICONS = ["💡", "📈", "⚠️", "🎯"];

export default function InsightCard({ insight, index }) {
  return (
    <div className="insight-card">
      <span className="insight-icon">{ICONS[index % ICONS.length]}</span>
      <p className="insight-text">{insight}</p>
    </div>
  );
}