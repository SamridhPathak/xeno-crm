import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import client from "../api/client";
import CampaignStats from "../components/CampaignStats";

export default function CampaignDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [campaign, setCampaign] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [campRes, analyticsRes] = await Promise.all([
        client.get(`/api/campaigns/${id}`),
        client.get(`/api/analytics/campaign/${id}`),
      ]);
      setCampaign(campRes.data);
      setAnalytics(analyticsRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let interval;

    const startPolling = async () => {
      try {
        const [campRes, analyticsRes] = await Promise.all([
          client.get(`/api/campaigns/${id}`),
          client.get(`/api/analytics/campaign/${id}`),
        ]);

        setCampaign(campRes.data);
        setAnalytics(analyticsRes.data);
        setLoading(false);

        interval = setInterval(async () => {
          try {
            const [campRes2, analyticsRes2] = await Promise.all([
              client.get(`/api/campaigns/${id}`),
              client.get(`/api/analytics/campaign/${id}`),
            ]);

            setCampaign(campRes2.data);
            setAnalytics(analyticsRes2.data);

            console.log("Analytics refreshed");
          } catch (err) {
            console.error(err);
          }
        }, 3000);
      } catch (err) {
        console.error(err);
        setLoading(false);
      }
    };

  startPolling();

  return () => {
    if (interval) clearInterval(interval);
  };
}, [id]);

  if (loading) return <div className="page-loading">Loading campaign...</div>;
  if (!campaign) return <div className="page-loading">Campaign not found.</div>;

  const CHANNEL_ICONS = { whatsapp: "💬", sms: "📱", email: "📧", rcs: "🔵" };

  return (
    <div className="page">
      <div className="page-header">
        <button className="btn-back" onClick={() => navigate("/campaigns")}>← Back</button>
        <div>
          <h1>{campaign.campaign_name}</h1>
          <span className="page-subtitle">
            {CHANNEL_ICONS[campaign.channel]} {campaign.channel?.toUpperCase()} ·
            <span className={`status-badge ${campaign.status}`}>{campaign.status}</span>
          </span>
        </div>
      </div>

      <div className="detail-grid">
        <div className="detail-main">
          <div className="card">
            <h3>Message Template</h3>
            <div className="message-preview">
              {campaign.message_template}
            </div>
          </div>

          {analytics && <CampaignStats stats={analytics} />}

          <div className="card">
            <h3>Live Updates</h3>
            <p className="hint">Stats refresh every 3 seconds as the channel service processes deliveries.</p>
            <div className="live-indicator">
              <span className="status-dot"></span> Live tracking active
            </div>
          </div>
        </div>

        <div className="detail-sidebar">
          <div className="card">
            <h3>Campaign Info</h3>
            <div className="info-list">
              <div className="info-row"><span>Status</span><span className={`status-badge ${campaign.status}`}>{campaign.status}</span></div>
              <div className="info-row"><span>Channel</span><span>{CHANNEL_ICONS[campaign.channel]} {campaign.channel}</span></div>
              <div className="info-row"><span>Created</span><span>{new Date(campaign.created_at).toLocaleDateString()}</span></div>
              {analytics && <>
                <div className="info-row"><span>Total Sent</span><span>{analytics.total_sent}</span></div>
                <div className="info-row"><span>Delivered</span><span>{analytics.delivered}</span></div>
                <div className="info-row"><span>Failed</span><span>{analytics.failed}</span></div>
              </>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}