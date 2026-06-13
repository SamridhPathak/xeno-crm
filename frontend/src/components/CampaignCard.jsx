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
      case "completed":
        return "#10b981";
      case "sending":
        return "#3b82f6";
      case "draft":
        return "#f59e0b";
      case "failed":
        return "#ef4444";  
      default:
        return "#64748b";
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
        padding: "20px 24px",
      }}
    >
      <div>
        <h3
          style={{
            marginBottom: "10px",
            fontSize: "1.1rem",
          }}
        >
          {displayName}
        </h3>

        <div
          style={{
            display: "flex",
            gap: "12px",
            alignItems: "center",
            marginBottom: "8px",
          }}
        >
          <span
            style={{
              fontSize: "0.85rem",
              opacity: 0.8,
            }}
          >
            {getChannelIcon(safeChannel)} {safeChannel.toUpperCase()}
          </span>

          <span
            style={{
              background: `${getStatusColor(safeStatus)}22`,
              color: getStatusColor(safeStatus),
              padding: "4px 10px",
              borderRadius: "999px",
              fontSize: "0.75rem",
              fontWeight: 600,
            }}
          >
            {displayStatus}
          </span>
        </div>

        <div
          style={{
            fontSize: "0.85rem",
            opacity: 0.7,
          }}
        >
          Created {formatDate(created_at)}
        </div>
      </div>

      <Link
        to={`/campaigns/${id}`}
        className="btn btn-secondary"
      >
        View Analytics
      </Link>
    </div>
  );
};

export default CampaignCard;