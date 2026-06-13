import React from "react";
import { useNavigate } from "react-router-dom";

const CHANNEL_ICONS = { whatsapp: "💬", sms: "📱", email: "📧", rcs: "🔵" };

/* ─────────────────────────────────────────────
   Inline markdown → React elements
   Handles: **bold**, *italic*, `code`, newlines
───────────────────────────────────────────── */
function renderMarkdown(text) {
  if (!text) return null;
  const lines = text.split("\n");
  return lines.map((line, li) => {
    // Empty line → spacer
    if (line.trim() === "") return <div key={li} style={{ height: "6px" }} />;

    // Parse inline styles within a line
    const parts = [];
    const regex = /(\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)/g;
    let last = 0;
    let match;
    let key = 0;

    while ((match = regex.exec(line)) !== null) {
      if (match.index > last) parts.push(line.slice(last, match.index));
      if (match[2]) parts.push(<strong key={key++}>{match[2]}</strong>);
      else if (match[3]) parts.push(<em key={key++}>{match[3]}</em>);
      else if (match[4]) parts.push(
        <code key={key++} style={{
          background: "rgba(37,99,235,0.12)",
          border: "1px solid rgba(37,99,235,0.2)",
          borderRadius: "4px",
          padding: "1px 6px",
          fontSize: "0.82em",
          color: "#93C5FD",
          fontFamily: "monospace",
        }}>{match[4]}</code>
      );
      last = match.index + match[0].length;
    }
    if (last < line.length) parts.push(line.slice(last));

    return <div key={li} style={{ lineHeight: "1.65" }}>{parts}</div>;
  });
}

/* ─────────────────────────────────────────────
   Detect and parse segment info block
   Lines like: "- **Segment Name**: Foo Bar"
───────────────────────────────────────────── */
const SEGMENT_FIELDS = [
  { key: "segment_name",    labels: ["segment name"],    icon: "📋" },
  { key: "target_audience", labels: ["target audience"], icon: "🎯" },
  { key: "audience_size",   labels: ["audience size"],   icon: "👥" },
  { key: "samples",         labels: ["samples"],         icon: "👤" },
];

function parseSegmentBlock(text) {
  const lines = text.split("\n");
  const fields = {};
  lines.forEach(line => {
    const clean = line.replace(/^-\s*/, "").replace(/\*\*/g, "");
    SEGMENT_FIELDS.forEach(({ key, labels }) => {
      labels.forEach(label => {
        const rx = new RegExp(`^${label}\\s*:\\s*(.+)$`, "i");
        const m = clean.match(rx);
        if (m) fields[key] = m[1].trim();
      });
    });
  });
  return Object.keys(fields).length >= 2 ? fields : null;
}

/* ─────────────────────────────────────────────
   Detect email/SMS/WhatsApp template block
   Heuristic: contains "Subject:" or "Hello {name}"
   or starts after a line like "I've drafted..."
───────────────────────────────────────────── */
function extractTemplate(text) {
  // Split on the triple-backtick or "drafted" marker
  const markers = [
    /i'?ve drafted a campaign template[^:]*:\s*`{0,3}/i,
    /```/,
  ];
  for (const marker of markers) {
    const idx = text.search(marker);
    if (idx !== -1) {
      const before = text.slice(0, idx);
      let after = text.slice(idx).replace(marker, "").replace(/```$/, "").trim();
      // Strip trailing launch prompt from template
      const launchIdx = after.search(/would you like me to launch/i);
      let template = launchIdx !== -1 ? after.slice(0, launchIdx).trim() : after;
      const launchText = launchIdx !== -1 ? after.slice(launchIdx).trim() : null;
      return { before: before.trim(), template: template.trim(), launchText };
    }
  }
  return null;
}

/* ─────────────────────────────────────────────
   Split a full AI text response into sections:
   - segmentBlock (structured info)
   - draftedLine  (the "I've drafted..." line)
   - template     (the email/SMS body)
   - launchPrompt (the "Would you like..." CTA)
   - rest         (anything else)
───────────────────────────────────────────── */
function parseAssistantMessage(text) {
  const sections = {
    intro: [],
    segmentLines: [],
    draftedLine: null,
    template: null,
    launchPrompt: null,
    outro: [],
  };

  const lines = text.split("\n");
  let mode = "intro"; // intro → segment → template → launch → outro
  let templateLines = [];
  let inTemplate = false;
  let inBacktick = false;

  lines.forEach(line => {
    const trimmed = line.trim();

    // Backtick block toggle
    if (trimmed === "```") {
      inBacktick = !inBacktick;
      inTemplate = inBacktick;
      return;
    }

    // "I've drafted" line
    if (/i'?ve drafted a campaign template/i.test(trimmed)) {
      mode = "drafted";
      sections.draftedLine = trimmed;
      inTemplate = true;
      return;
    }

    // Segment info lines: "- **Field**: value"
    if (/^-\s*\*\*[^*]+\*\*\s*:/.test(trimmed) && mode === "intro") {
      mode = "segment";
      sections.segmentLines.push(line);
      return;
    }
    if (mode === "segment" && /^-\s*\*\*[^*]+\*\*\s*:/.test(trimmed)) {
      sections.segmentLines.push(line);
      return;
    }
    // End of segment block
    if (mode === "segment" && trimmed !== "" && !/^-/.test(trimmed)) {
      mode = "post_segment";
    }

    // "Would you like" launch prompt
    if (/would you like me to launch/i.test(trimmed)) {
      inTemplate = false;
      mode = "launch";
      sections.launchPrompt = trimmed;
      return;
    }

    if (inTemplate) {
      templateLines.push(line);
      return;
    }

    if (mode === "intro" || mode === "post_segment") {
      sections.intro.push(line);
    } else if (mode === "launch") {
      // continuation of launch prompt
      if (trimmed) sections.launchPrompt += " " + trimmed;
    } else {
      sections.outro.push(line);
    }
  });

  if (templateLines.length > 0) {
    sections.template = templateLines.join("\n").trim();
  }

  return sections;
}

/* ─────────────────────────────────────────────
   Segment Info Card
───────────────────────────────────────────── */
function SegmentInfoCard({ lines }) {
  const parsed = parseSegmentBlock(lines.join("\n"));
  if (!parsed) {
    return (
      <div>{lines.map((l, i) => <div key={i}>{renderMarkdown(l)}</div>)}</div>
    );
  }

  const rows = SEGMENT_FIELDS.filter(f => parsed[f.key]);

  return (
    <div style={{
      background: "linear-gradient(135deg, rgba(15,23,42,0.9), rgba(11,15,25,0.8))",
      border: "1px solid rgba(37,99,235,0.25)",
      borderRadius: "12px",
      overflow: "hidden",
      margin: "10px 0",
    }}>
      {/* Header */}
      <div style={{
        background: "linear-gradient(90deg, rgba(37,99,235,0.15), rgba(124,58,237,0.1))",
        borderBottom: "1px solid rgba(37,99,235,0.2)",
        padding: "10px 16px",
        display: "flex",
        alignItems: "center",
        gap: "8px",
      }}>
        <span style={{ fontSize: "0.65rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "#60A5FA" }}>
          🔍 Segment Analysis
        </span>
      </div>
      {/* Rows */}
      <div style={{ padding: "4px 0" }}>
        {rows.map(({ key, icon }) => (
          <div key={key} style={{
            display: "flex",
            alignItems: "flex-start",
            gap: "12px",
            padding: "9px 16px",
            borderBottom: "1px solid rgba(255,255,255,0.04)",
          }}>
            <span style={{ fontSize: "1rem", flexShrink: 0, width: "20px", textAlign: "center" }}>{icon}</span>
            <div style={{ display: "flex", flexDirection: "column", gap: "1px" }}>
              <span style={{ fontSize: "0.68rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.07em", color: "var(--text-muted)" }}>
                {SEGMENT_FIELDS.find(f => f.key === key)?.labels[0]}
              </span>
              <span style={{ fontSize: "0.87rem", color: "var(--text-primary)", fontWeight: 500 }}>
                {parsed[key]}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────
   Template Preview Card
───────────────────────────────────────────── */
function TemplateCard({ template, channel }) {
  const lines = template.split("\n");
  const subjectLine = lines.find(l => /^subject:/i.test(l.trim()));
  const body = subjectLine
    ? lines.filter(l => !(/^subject:/i.test(l.trim()))).join("\n").trim()
    : template;
  const subject = subjectLine ? subjectLine.replace(/^subject:\s*/i, "").trim() : null;

  const channelKey = (channel || "email").toLowerCase();
  const channelIcon = CHANNEL_ICONS[channelKey] || "📨";

  return (
    <div style={{
      background: "rgba(11,15,25,0.7)",
      border: "1px solid rgba(255,255,255,0.07)",
      borderRadius: "12px",
      overflow: "hidden",
      margin: "10px 0",
    }}>
      {/* Channel header */}
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "10px 16px",
        background: "rgba(30,41,59,0.6)",
        borderBottom: "1px solid rgba(255,255,255,0.06)",
      }}>
        <span style={{ fontSize: "0.72rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "6px" }}>
          {channelIcon} <span>Template</span>
        </span>
        <span style={{
          fontSize: "0.65rem",
          background: "rgba(16,185,129,0.12)",
          border: "1px solid rgba(16,185,129,0.25)",
          color: "#34D399",
          padding: "2px 8px",
          borderRadius: "999px",
          fontWeight: 600,
        }}>AI drafted</span>
      </div>
      {/* Subject */}
      {subject && (
        <div style={{
          padding: "10px 16px",
          borderBottom: "1px solid rgba(255,255,255,0.05)",
          display: "flex",
          gap: "10px",
          alignItems: "flex-start",
        }}>
          <span style={{ fontSize: "0.68rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.07em", color: "var(--text-muted)", paddingTop: "2px", flexShrink: 0 }}>Subject</span>
          <span style={{ fontSize: "0.88rem", color: "var(--text-primary)", fontWeight: 600, fontStyle: "italic" }}>{subject}</span>
        </div>
      )}
      {/* Body */}
      <div style={{
        padding: "14px 16px",
        fontSize: "0.85rem",
        lineHeight: "1.75",
        color: "var(--text-secondary)",
        whiteSpace: "pre-wrap",
      }}>
        {body}
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────
   Launch CTA — text prompt only, no buttons
───────────────────────────────────────────── */
function LaunchCTA() {
  return (
    <div style={{
      background: "linear-gradient(135deg, rgba(37,99,235,0.08), rgba(124,58,237,0.06))",
      border: "1px solid rgba(37,99,235,0.2)",
      borderRadius: "12px",
      padding: "14px 18px",
      marginTop: "12px",
    }}>
      <p style={{ fontSize: "0.88rem", color: "var(--text-secondary)", fontWeight: 500, margin: 0, lineHeight: 1.6 }}>
        🚀 Reply <span style={{ color: "var(--text-primary)", fontWeight: 700 }}>"Yes"</span> to launch, or let me know if you'd like any changes.
      </p>
    </div>
  );
}

/* ─────────────────────────────────────────────
   Main ChatMessage component
───────────────────────────────────────────── */
export default function ChatMessage({ message, onAction }) {
  const navigate = useNavigate();
  const isUser = message.role === "user";

  /* ── Preview type (segment + message preview card) ── */
  if (message.type === "preview" && message.preview) {
    const p = message.preview;
    return (
      <div className="message assistant">
        <div className="msg-bubble preview-bubble">
          <p className="msg-text" style={{ marginBottom: "12px" }}>{message.content}</p>
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
                {p.customer_count > 3 && (
                  <span className="customer-chip muted">+{p.customer_count - 3} more</span>
                )}
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

  /* ── Launched type ── */
  if (message.type === "launched") {
    return (
      <div className="message assistant">
        <div className="msg-bubble launched-bubble">
          <p className="msg-text">{message.content}</p>
          <button
            className="btn-view-campaign"
            onClick={() => navigate(`/campaigns/${message.campaign_id}`)}
          >
            View Live Stats →
          </button>
        </div>
      </div>
    );
  }

  /* ── User message ── */
  if (isUser) {
    return (
      <div className="message user">
        <div className="msg-bubble">
          <p className="msg-text">{message.content}</p>
        </div>
      </div>
    );
  }

  /* ── Assistant text message — rich rendering ── */
  const sections = parseAssistantMessage(message.content);
  const hasSegment = sections.segmentLines.length > 0;
  const hasTemplate = !!sections.template;
  const hasLaunch = !!sections.launchPrompt;
  const hasIntro = sections.intro.some(l => l.trim() !== "");

  // Detect the channel from draftedLine e.g. "I've drafted a campaign template for **EMAIL**:"
  let detectedChannel = "email";
  if (sections.draftedLine) {
    const m = sections.draftedLine.match(/\*\*(\w+)\*\*/);
    if (m) detectedChannel = m[1].toLowerCase();
  }

  return (
    <div className="message assistant">
      <div className="msg-bubble" style={{ display: "flex", flexDirection: "column", gap: "4px" }}>

        {/* Intro text (e.g. "🔵 I've parsed your segment intent:") */}
        {hasIntro && (
          <div style={{ fontSize: "0.9rem", color: "var(--text-primary)" }}>
            {renderMarkdown(sections.intro.join("\n"))}
          </div>
        )}

        {/* Segment info card */}
        {hasSegment && (
          <SegmentInfoCard lines={sections.segmentLines} />
        )}

        {/* "I've drafted..." line */}
        {sections.draftedLine && (
          <div style={{
            fontSize: "0.85rem",
            color: "var(--text-secondary)",
            marginTop: hasSegment ? "6px" : "0",
            display: "flex",
            alignItems: "center",
            gap: "6px",
          }}>
            {renderMarkdown(sections.draftedLine)}
          </div>
        )}

        {/* Template card */}
        {hasTemplate && (
          <TemplateCard template={sections.template} channel={detectedChannel} />
        )}

        {/* Launch CTA */}
        {hasLaunch && (
          <LaunchCTA />
        )}

        {/* Outro */}
        {sections.outro.length > 0 && sections.outro.some(l => l.trim()) && (
          <div style={{ fontSize: "0.9rem", color: "var(--text-primary)", marginTop: "4px" }}>
            {renderMarkdown(sections.outro.join("\n"))}
          </div>
        )}

        {/* Fallback: if nothing was parsed, just show raw text with markdown */}
        {!hasIntro && !hasSegment && !hasTemplate && !hasLaunch && sections.outro.length === 0 && (
          <div style={{ fontSize: "0.9rem" }}>
            {renderMarkdown(message.content)}
          </div>
        )}

      </div>
    </div>
  );
}
