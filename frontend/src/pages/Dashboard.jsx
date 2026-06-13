import React, { useState, useEffect } from "react";
import client from "../api/client";
import StatCard from "../components/StatCard";
import InsightCard from "../components/InsightCard";
import CampaignCard from "../components/CampaignCard";

export default function Dashboard() {
  const [overview, setOverview] = useState({});
  const [insights, setInsights] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    console.log("Dashboard mounted");

    const fetchAll = async () => {
      try {
        const ovRes = await client.get("/api/analytics/overview");

        console.log("OVERVIEW RESPONSE:", ovRes.data);

        setOverview(ovRes?.data || {});

        console.log(
          "RECENT CAMPAIGNS RAW:",
          ovRes?.data?.recent_campaigns
        );

        const normalizedCampaigns = Array.isArray(
          ovRes?.data?.recent_campaigns
        )
          ? ovRes.data.recent_campaigns.map((c) => ({
              id: c.campaign_id ?? c.id,
              name: c.campaign_name ?? c.name ?? "Untitled Campaign",
              channel: c.channel ?? "email",
              status: c.status ?? "completed",
              created_at: c.created_at ?? "",
            }))
          : [];

        console.log(
          "NORMALIZED CAMPAIGNS:",
          normalizedCampaigns
        );

        setCampaigns(normalizedCampaigns);

        try {
          const insRes = await client.get("/api/insights");

          console.log("INSIGHTS RESPONSE:", insRes.data);

          setInsights(
            Array.isArray(insRes?.data)
              ? insRes.data
              : ["AI insights temporarily unavailable"]
          );
        } catch (err) {
          console.error("Insights failed:", err);

          setInsights([
            "AI insights temporarily unavailable",
          ]);
        }
      } catch (err) {
        console.error("Dashboard failed:", err);

        setOverview({});
        setCampaigns([]);
        setInsights([
          "AI insights temporarily unavailable",
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchAll();
  }, []);

  if (loading) {
    return (
      <div className="page-loading">
        Loading dashboard...
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Dashboard</h1>
        <span className="page-subtitle">
          BrewBox CRM Overview
        </span>
      </div>

      <div className="stats-grid">
        <StatCard
          title="Customers"
          value={overview?.total_customers ?? 0}
          icon="👥"
        />

        <StatCard
          title="Segments"
          value={overview?.total_segments ?? 0}
          icon="🎯"
        />

        <StatCard
          title="Campaigns"
          value={overview?.total_campaigns ?? 0}
          icon="📢"
        />

        <StatCard
          title="Messages Sent"
          value={overview?.total_messages_sent ?? 0}
          icon="✉️"
        />

        <StatCard
          title="Delivery Rate"
          value={`${overview?.overall_delivery_rate ?? 0}%`}
          icon="📬"
        />

        <StatCard
          title="Open Rate"
          value={`${overview?.overall_open_rate ?? 0}%`}
          icon="👀"
        />

        <StatCard
          title="Click Rate"
          value={`${overview?.overall_click_rate ?? 0}%`}
          icon="🖱️"
        />
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-main">
          <div className="section-header">
            <h2>Recent Campaigns</h2>
          </div>

          <div className="campaign-list">
            {campaigns.length === 0 ? (
              <div className="empty-state">
                No campaigns yet. Start one from the Chat page.
              </div>
            ) : (
              campaigns.map((campaign) => (
                <CampaignCard
                  key={campaign.id}
                  campaign={campaign}
                />
              ))
            )}
          </div>
        </div>

        <div className="dashboard-sidebar">
          <div className="section-header">
            <h2>AI Insights</h2>
            <span className="badge-ai">
              Gemini
            </span>
          </div>

          <div className="insights-list">
            {insights.length === 0 ? (
              <div className="empty-state">
                Generating insights...
              </div>
            ) : (
              insights.map((insight, i) => (
                <InsightCard
                  key={i}
                  insight={insight}
                  index={i}
                />
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}