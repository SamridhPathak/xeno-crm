import React from 'react';

const CampaignStats = ({ stats }) => {
  const {
    total_sent = 0,
    delivered = 0,
    failed = 0,
    opened = 0,
    clicked = 0,
    delivery_rate = 0,
    open_rate = 0,
    click_rate = 0,
  } = stats;

  const failed_rate = total_sent > 0 ? (failed / total_sent) * 100 : 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Percentage metrics display */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
          gap: '16px',
        }}
      >
        <div style={{ backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: 'var(--border-radius-sm)', padding: '16px', textAlign: 'center' }}>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--success-color)' }}>
            {delivery_rate}%
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Delivery Rate
          </div>
        </div>

        <div style={{ backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: 'var(--border-radius-sm)', padding: '16px', textAlign: 'center' }}>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--info-color)' }}>
            {open_rate}%
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Open Rate
          </div>
        </div>

        <div style={{ backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: 'var(--border-radius-sm)', padding: '16px', textAlign: 'center' }}>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--accent-color)' }}>
            {click_rate}%
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Click-Through
          </div>
        </div>
      </div>

      {/* Progress Bars */}
      <div className="stats-container">
        <div className="progress-group">
          <div className="progress-label-row">
            <span className="progress-name">Delivered</span>
            <span className="progress-pct">{delivered} / {total_sent}</span>
          </div>
          <div className="progress-bar-track">
            <div
              className="progress-bar-fill progress-fill-delivered"
              style={{ width: `${delivery_rate}%` }}
            ></div>
          </div>
        </div>

        <div className="progress-group">
          <div className="progress-label-row">
            <span className="progress-name">Opened</span>
            <span className="progress-pct">{opened} / {delivered}</span>
          </div>
          <div className="progress-bar-track">
            <div
              className="progress-bar-fill progress-fill-opened"
              style={{ width: `${open_rate}%` }}
            ></div>
          </div>
        </div>

        <div className="progress-group">
          <div className="progress-label-row">
            <span className="progress-name">Clicked</span>
            <span className="progress-pct">{clicked} / {opened}</span>
          </div>
          <div className="progress-bar-track">
            <div
              className="progress-bar-fill progress-fill-clicked"
              style={{ width: `${click_rate}%` }}
            ></div>
          </div>
        </div>

        <div className="progress-group">
          <div className="progress-label-row">
            <span className="progress-name">Failed</span>
            <span className="progress-pct">{failed} / {total_sent}</span>
          </div>
          <div className="progress-bar-track">
            <div
              className="progress-bar-fill progress-fill-failed"
              style={{ width: `${failed_rate}%` }}
            ></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CampaignStats;
