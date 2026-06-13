import React from "react";
import { Link } from "react-router-dom";

const CampaignCard = ({ campaign = {} }) => {
  const {
    id,
    name,
    channel,
    status,
    created_at,
  } = campaign;

  const safeName = name || "Untitled Campaign";
  const safeChannel = (channel || "email").toLowerCase();
  const safeStatus = (status || "unknown").toLowerCase();

  const formatDate = (dateStr) => {
    if (!dateStr) return "Unknown";

    try {
      return new Date(dateStr).toLocaleString("en-IN", {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
    } catch {
      return "Unknown";
    }
  };

  const getChannelIcon = (ch) => {
    switch (ch) {
      case "sms":
        return "💬";
      case "whatsapp":
        return "🟢";
      case "email":
      default:
        return "✉️";
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "completed": return "#10b981";
      case "sending":   return "#3b82f6";
      case "draft":     return "#f59e0b";
      case "failed":    return "#ef4444";
      default:          return "#64748b";
    }
  };

  const getStatusBorderColor = (status) => {
    switch (status) {
      case "completed": return "rgba(16,185,129,0.6)";
      case "sending":   return "rgba(59,130,246,0.6)";
      case "draft":     return "rgba(245,158,11,0.6)";
      case "failed":    return "rgba(239,68,68,0.6)";
      default:          return "rgba(100,116,139,0.4)";
    }
  };

  const displayName =
    safeName.replace(/^Campaign:\s*/i, "") || "Untitled Campaign";

  const displayStatus =
    safeStatus.charAt(0).toUpperCase() + safeStatus.slice(1);

  return (
    <div
      className="card interactive"
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "18px 20px",
        borderLeft: `3px solid ${getStatusBorderColor(safeStatus)}`,
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Subtle status glow on left edge */}
      <div style={{
        position: 'absolute',
        left: 0, top: 0, bottom: 0,
        width: '60px',
        background: `linear-gradient(90deg, ${getStatusColor(safeStatus)}08, transparent)`,
        pointerEvents: 'none',
      }} />

      <div>
        <h3 style={{ marginBottom: '8px', fontSize: '1rem', fontWeight: 700 }}>
          {displayName}
        </h3>

        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          {/* Channel badge */}
          <span style={{
            fontSize: "0.75rem",
            background: 'rgba(30,41,59,0.9)',
            border: '1px solid rgba(255,255,255,0.1)',
            color: 'var(--text-secondary)',
            padding: "3px 9px",
            borderRadius: "6px",
            fontWeight: 600,
            letterSpacing: '0.03em',
          }}>
            {getChannelIcon(safeChannel)} {safeChannel.toUpperCase()}
          </span>

          {/* Status badge */}
          <span style={{
            background: `${getStatusColor(safeStatus)}18`,
            color: getStatusColor(safeStatus),
            border: `1px solid ${getStatusColor(safeStatus)}35`,
            padding: "3px 10px",
            borderRadius: "999px",
            fontSize: "0.72rem",
            fontWeight: 700,
            letterSpacing: '0.04em',
            textTransform: 'capitalize',
          }}>
            {displayStatus}
          </span>
        </div>

        <div style={{ fontSize: "0.78rem", color: 'var(--text-muted)', marginTop: '7px' }}>
          Created {formatDate(created_at)}
        </div>
      </div>

      <Link to={`/campaigns/${id}`} className="btn btn-secondary" style={{ flexShrink: 0 }}>
        View Analytics
      </Link>
    </div>
  );
};

export default CampaignCard;