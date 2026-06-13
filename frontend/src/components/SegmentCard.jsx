import React from 'react';

const SegmentCard = ({ segment, onPreviewClick }) => {
  const { name, description, customer_count, filter_rules, created_at } = segment;

  // Normalise filter rules to list of rules
  const rulesList = Array.isArray(filter_rules)
    ? filter_rules
    : typeof filter_rules === 'object' && filter_rules
    ? [filter_rules]
    : [];

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    try {
      return new Date(dateStr).toLocaleDateString('en-IN', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="card segment-card interactive">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '4px' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 700, lineHeight: 1.3, flex: 1, paddingRight: '12px' }}>{name}</h3>
        {/* Reach badge — pill with gradient */}
        <div
          style={{
            background: 'linear-gradient(135deg, rgba(37,99,235,0.2), rgba(124,58,237,0.2))',
            border: '1px solid rgba(37,99,235,0.35)',
            color: '#93C5FD',
            padding: '5px 12px',
            borderRadius: '999px',
            fontWeight: 700,
            fontSize: '0.82rem',
            whiteSpace: 'nowrap',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            lineHeight: 1.1,
            flexShrink: 0,
          }}
        >
          <span style={{ fontSize: '1rem', fontWeight: 800, background: 'linear-gradient(135deg,#3B82F6,#A78BFA)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>{customer_count}</span>
          <span style={{ fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)', WebkitTextFillColor: 'var(--text-muted)' }}>Reach</span>
        </div>
      </div>

      <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '14px', lineHeight: 1.5 }}>
        {description || 'No description provided.'}
      </p>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '16px' }}>
        {rulesList.map((rule, idx) => (
          <span
            key={idx}
            style={{
              fontSize: '0.72rem',
              background: 'rgba(15,23,42,0.8)',
              border: '1px solid rgba(37,99,235,0.2)',
              color: '#94A3B8',
              padding: '3px 9px',
              borderRadius: '6px',
              fontWeight: 600,
              fontFamily: 'monospace',
              letterSpacing: '0.01em',
            }}
          >
            {rule.field} {rule.op} <span style={{ color: '#60A5FA' }}>{JSON.stringify(rule.value)}</span>
          </span>
        ))}
      </div>

      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderTop: '1px solid rgba(255,255,255,0.05)',
          paddingTop: '12px',
        }}
      >
        <span style={{ fontSize: '0.73rem', color: 'var(--text-muted)' }}>
          Created: {formatDate(created_at)}
        </span>
        {onPreviewClick && (
          <button className="btn btn-secondary btn-sm" onClick={() => onPreviewClick(segment.id)}>
            Preview Audience
          </button>
        )}
      </div>
    </div>
  );
};

export default SegmentCard;
