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

  const metrics = [
    { value: `${delivery_rate}%`, label: 'Delivery Rate', color: '#10B981', gradient: 'linear-gradient(135deg,#10B981,#059669)', glow: 'rgba(16,185,129,0.15)' },
    { value: `${open_rate}%`,     label: 'Open Rate',     color: '#06B6D4', gradient: 'linear-gradient(135deg,#06B6D4,#0284C7)', glow: 'rgba(6,182,212,0.15)' },
    { value: `${click_rate}%`,    label: 'Click-Through', color: '#3B82F6', gradient: 'linear-gradient(135deg,#3B82F6,#7C3AED)', glow: 'rgba(37,99,235,0.15)' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Metric cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '14px' }}>
        {metrics.map(({ value, label, gradient, glow }) => (
          <div key={label} style={{
            background: `linear-gradient(145deg, rgba(30,41,59,0.9), rgba(22,31,47,0.8))`,
            border: '1px solid rgba(255,255,255,0.07)',
            borderRadius: '14px',
            padding: '20px 16px',
            textAlign: 'center',
            position: 'relative',
            overflow: 'hidden',
            boxShadow: `0 4px 20px ${glow}`,
            transition: 'transform 0.2s ease, box-shadow 0.2s ease',
          }}>
            {/* top accent line */}
            <div style={{ position:'absolute', top:0, left:0, right:0, height:'2px', background: gradient }} />
            <div style={{
              fontSize: '2rem',
              fontWeight: 800,
              fontFamily: 'var(--font-heading)',
              letterSpacing: '-0.03em',
              background: gradient,
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              lineHeight: 1.1,
              marginBottom: '6px',
            }}>
              {value}
            </div>
            <div style={{
              fontSize: '0.7rem',
              color: 'var(--text-secondary)',
              textTransform: 'uppercase',
              letterSpacing: '0.07em',
              fontWeight: 600,
            }}>
              {label}
            </div>
          </div>
        ))}
      </div>

      {/* Progress Bars */}
      <div className="stats-container">
        <div className="progress-group">
          <div className="progress-label-row">
            <span className="progress-name">Delivered</span>
            <span className="progress-pct">{delivered} / {total_sent}</span>
          </div>
          <div className="progress-bar-track">
            <div className="progress-bar-fill progress-fill-delivered" style={{ width: `${delivery_rate}%` }}></div>
          </div>
        </div>

        <div className="progress-group">
          <div className="progress-label-row">
            <span className="progress-name">Opened</span>
            <span className="progress-pct">{opened} / {delivered}</span>
          </div>
          <div className="progress-bar-track">
            <div className="progress-bar-fill progress-fill-opened" style={{ width: `${open_rate}%` }}></div>
          </div>
        </div>

        <div className="progress-group">
          <div className="progress-label-row">
            <span className="progress-name">Clicked</span>
            <span className="progress-pct">{clicked} / {opened}</span>
          </div>
          <div className="progress-bar-track">
            <div className="progress-bar-fill progress-fill-clicked" style={{ width: `${click_rate}%` }}></div>
          </div>
        </div>

        <div className="progress-group">
          <div className="progress-label-row">
            <span className="progress-name">Failed</span>
            <span className="progress-pct">{failed} / {total_sent}</span>
          </div>
          <div className="progress-bar-track">
            <div className="progress-bar-fill progress-fill-failed" style={{ width: `${failed_rate}%` }}></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CampaignStats;
