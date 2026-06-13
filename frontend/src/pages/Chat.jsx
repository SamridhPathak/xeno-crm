import React, { useState, useRef, useEffect } from "react";
import client from "../api/client";
import ChatMessage from "../components/ChatMessage";

const SUGGESTIONS = [
  {
    icon: "💸",
    label: "Win-back lapsed buyers",
    text: "Reach customers who spent over ₹2000 but haven't bought in 45 days",
  },
  {
    icon: "🏆",
    label: "Reward top spenders",
    text: "Send a loyalty reward to our top 10% spenders in Mumbai",
  },
  {
    icon: "🔄",
    label: "Re-engage inactive users",
    text: "Re-engage customers who haven't visited in 60 days with a discount",
  },
  {
    icon: "🚀",
    label: "Upsell first-timers",
    text: "Target first-time buyers from Delhi with an upsell offer",
  },
];

const INITIAL_MESSAGE = {
  role: "assistant",
  content:
    "Hi! I'm your AI campaign assistant for BrewBox ☕\n\nTell me who you want to reach and what you want to say — I'll handle the segmentation, craft the message, and launch the campaign for you.\n\nTry: *'Reach customers who spent over ₹2000 but haven't bought in 45 days'*",
  type: "text",
};

export default function Chat() {
  const [messages, setMessages] = useState([INITIAL_MESSAGE]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionState, setSessionState] = useState({});
  const [inputFocused, setInputFocused] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  const isHeroState = messages.length === 1;

  useEffect(() => {
    if (!isHeroState) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
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

  const handleReset = () => {
    setMessages([INITIAL_MESSAGE]);
    setSessionState({});
    setInput("");
  };

  return (
    <div className="chat-page">
      {/* ── Header ── */}
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
        <button className="btn-ghost" onClick={handleReset}>
          New Chat
        </button>
      </div>

      {/* ── Hero state — centered landing ── */}
      {isHeroState ? (
        <div className="chat-hero">
          {/* Ambient glow orbs */}
          <div className="hero-glow-orb hero-glow-orb--blue" />
          <div className="hero-glow-orb hero-glow-orb--purple" />

          <div className="hero-content">
            {/* Big avatar orb */}
            <div className="hero-avatar-ring">
              <div className="hero-avatar-inner">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z" fill="currentColor"/>
                </svg>
              </div>
            </div>

            {/* Heading */}
            <div className="hero-heading">
              <h1 className="hero-title">Campaign Copilot</h1>
              <p className="hero-subtitle">
                Describe your audience in plain English — I'll segment, craft the message, and launch instantly.
              </p>
            </div>

            {/* Suggestion cards grid */}
            <div className="hero-suggestions">
              {SUGGESTIONS.map((s, i) => (
                <button
                  key={i}
                  className="hero-suggestion-card"
                  onClick={() => sendMessage(s.text)}
                  style={{ animationDelay: `${i * 0.08}s` }}
                >
                  <span className="hero-suggestion-icon">{s.icon}</span>
                  <span className="hero-suggestion-label">{s.label}</span>
                  <span className="hero-suggestion-text">{s.text}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Input pinned at bottom of hero */}
          <div className={`hero-input-wrap ${inputFocused ? "focused" : ""}`}>
            <div className="hero-input-glow" />
            <div className="hero-input-inner">
              <svg className="hero-input-icon" width="18" height="18" viewBox="0 0 24 24" fill="none">
                <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <textarea
                ref={inputRef}
                className="hero-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                onFocus={() => setInputFocused(true)}
                onBlur={() => setInputFocused(false)}
                placeholder="Describe your campaign goal in plain English..."
                rows={1}
              />
              <button
                className="hero-send-btn"
                onClick={() => sendMessage()}
                disabled={loading || !input.trim()}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                  <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" fill="currentColor"/>
                </svg>
              </button>
            </div>
            <p className="hero-input-hint">Press Enter to send · Shift+Enter for new line</p>
          </div>
        </div>
      ) : (
        /* ── Active conversation state ── */
        <>
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
        </>
      )}
    </div>
  );
}
