import React, { useState, useEffect } from "react";
import client from "../api/client";
import CampaignCard from "../components/CampaignCard";

export default function Campaigns() {
  const [campaigns, setCampaigns] = useState([]);
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    client.get("/api/campaigns").then((res) => {
      setCampaigns(res.data.campaigns || res.data || []);
      setLoading(false);
    });
  }, []);

  const filtered = filter === "all" ? campaigns : campaigns.filter((c) => c.status === filter);

  return (
    <div className="page">
      <div className="page-header">
        <h1>Campaigns</h1>
        <span className="page-subtitle">{campaigns.length} total campaigns</span>
      </div>

      <div className="filters-row">
        {["all", "draft", "sending", "completed", "failed"].map((f) => (
          <button
            key={f}
            className={`filter-tab ${filter === f ? "active" : ""}`}
            onClick={() => setFilter(f)}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="page-loading">Loading campaigns...</div>
      ) : filtered.length === 0 ? (
        <div className="empty-state-large">
          <p>No campaigns found.</p>
          <span>Launch one from the Chat page.</span>
        </div>
      ) : (
        <div className="campaigns-list">
          {filtered.map((c) => {
            console.log("CAMPAIGN OBJECT:", c);

            return (
              <CampaignCard
                key={c.id}
                campaign={c}
                showLink
              />
            );
          })}
        </div>
      )}
    </div>
  );
}