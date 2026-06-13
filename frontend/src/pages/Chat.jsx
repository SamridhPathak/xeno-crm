import React, { useState, useRef, useEffect } from "react";
import client from "../api/client";
import ChatMessage from "../components/ChatMessage";

const SUGGESTIONS = [
  "Reach customers who spent over ₹2000 but haven't bought in 45 days",
  "Send a loyalty reward to our top 10% spenders in Mumbai",
  "Re-engage customers who haven't visited in 60 days with a discount",
  "Target first-time buyers from Delhi with an upsell offer",
];

export default function Chat() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hi! I'm your AI campaign assistant for BrewBox ☕\n\nTell me who you want to reach and what you want to say — I'll handle the segmentation, craft the message, and launch the campaign for you.\n\nTry: *'Reach customers who spent over ₹2000 but haven't bought in 45 days'*",
      type: "text",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionState, setSessionState] = useState({});
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = async (text) => {
    const userText = text || input.trim();
    if (!userText) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userText, type: "text" }]);
    setLoading(true);

    try {
      const res = await client.post("/api/chat", {
        message: userText,
        session_state: sessionState,
      });

      const data = res.data;
      setSessionState(data.session_state || {});

      if (data.type === "preview") {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            type: "preview",
            content: data.reply,
            preview: {
              segment_name: data.segment_name,
              customer_count: data.customer_count,
              sample_customers: data.sample_customers,
              message_template: data.message_template,
              channel: data.channel,
              goal: data.goal,
            },
          },
        ]);
      } else if (data.type === "launched") {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            type: "launched",
            content: data.reply,
            campaign_id: data.campaign_id,
            campaign_name: data.campaign_name,
          },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", type: "text", content: data.reply },
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          type: "text",
          content: "Something went wrong. Please try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="chat-page">
      <div className="chat-header">
        <div className="chat-header-left">
          <div className="ai-avatar">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z" fill="currentColor"/>
            </svg>
          </div>
          <div>
            <h2>Campaign Copilot</h2>
            <span className="status-dot-label">
              <span className="status-dot"></span> AI-powered · BrewBox
            </span>
          </div>
        </div>
        <button className="btn-ghost" onClick={() => { setMessages([{ role: "assistant", content: "Hi! I'm your AI campaign assistant for BrewBox ☕\n\nTell me who you want to reach and what you want to say — I'll handle the segmentation, craft the message, and launch the campaign for you.", type: "text" }]); setSessionState({}); }}>
          New Chat
        </button>
      </div>

      <div className="chat-messages">
        {messages.map((msg, i) => (
          <ChatMessage key={i} message={msg} onAction={sendMessage} />
        ))}
        {loading && (
          <div className="message assistant">
            <div className="msg-bubble typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {messages.length === 1 && (
        <div className="suggestions-row">
          {SUGGESTIONS.map((s, i) => (
            <button key={i} className="suggestion-chip" onClick={() => sendMessage(s)}>
              {s}
            </button>
          ))}
        </div>
      )}

      <div className="chat-input-area">
        <textarea
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe your campaign goal in plain English..."
          rows={1}
        />
        <button
          className="btn-send"
          onClick={() => sendMessage()}
          disabled={loading || !input.trim()}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" fill="currentColor"/>
          </svg>
        </button>
      </div>
    </div>
  );
}