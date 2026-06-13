import React from "react";
import { useNavigate } from "react-router-dom";

const CHANNEL_ICONS = { whatsapp: "💬", sms: "📱", email: "📧", rcs: "🔵" };

export default function ChatMessage({ message, onAction }) {
  const navigate = useNavigate();
  const isUser = message.role === "user";

  if (message.type === "preview" && message.preview) {
    const p = message.preview;
    return (
      <div className="message assistant">
        <div className="msg-bubble preview-bubble">
          <p className="msg-text">{message.content}</p>
          <div className="preview-card">
            <div className="preview-card-header">
              <span className="preview-card-title">{p.segment_name}</span>
              <span className="preview-card-count">{p.customer_count} customers</span>
            </div>
            {p.sample_customers?.length > 0 && (
              <div className="sample-customers">
                {p.sample_customers.map((name, i) => (
                  <span key={i} className="customer-chip">{name}</span>
                ))}
                {p.customer_count > 3 && <span className="customer-chip muted">+{p.customer_count - 3} more</span>}
              </div>
            )}
            <div className="preview-message">
              <div className="preview-message-label">
                {CHANNEL_ICONS[p.channel] || "📨"} {p.channel?.toUpperCase()} Message
              </div>
              <div className="preview-message-text">{p.message_template}</div>
            </div>
            <div className="preview-actions">
              <button className="btn-launch" onClick={() => onAction("yes, launch it")}>
                🚀 Launch Campaign
              </button>
              <button className="btn-ghost-sm" onClick={() => onAction("change channel to email")}>
                Edit Channel
              </button>
              <button className="btn-ghost-sm" onClick={() => onAction("cancel")}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (message.type === "launched") {
    return (
      <div className="message assistant">
        <div className="msg-bubble launched-bubble">
          <p className="msg-text">{message.content}</p>
          <button className="btn-view-campaign" onClick={() => navigate(`/campaigns/${message.campaign_id}`)}>
            View Live Stats →
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`message ${isUser ? "user" : "assistant"}`}>
      <div className="msg-bubble">
        <p className="msg-text">{message.content}</p>
      </div>
    </div>
  );
}