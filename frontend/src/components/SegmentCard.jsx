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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '6px' }}>{name}</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>
            {description || 'No description provided.'}
          </p>
        </div>
        <div
          style={{
            backgroundColor: 'var(--accent-glow)',
            color: 'var(--accent-color)',
            padding: '6px 12px',
            borderRadius: 'var(--border-radius-sm)',
            fontWeight: 700,
            fontSize: '0.9rem',
          }}
        >
          {customer_count} Reach
        </div>
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '20px' }}>
        {rulesList.map((rule, idx) => (
          <span
            key={idx}
            style={{
              fontSize: '0.75rem',
              backgroundColor: 'var(--bg-secondary)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-primary)',
              padding: '4px 8px',
              borderRadius: '4px',
              fontWeight: 500,
            }}
          >
            <strong>{rule.field}</strong> {rule.op} <code>{JSON.stringify(rule.value)}</code>
          </span>
        ))}
      </div>

      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderTop: '1px solid var(--border-color)',
          paddingTop: '12px',
        }}
      >
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
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
