import React from 'react';

// City color map — purely visual
const CITY_COLORS = {
  Mumbai:    { bg: 'rgba(37,99,235,0.12)',   color: '#60A5FA', border: 'rgba(37,99,235,0.25)' },
  Delhi:     { bg: 'rgba(124,58,237,0.12)',  color: '#A78BFA', border: 'rgba(124,58,237,0.25)' },
  Bengaluru: { bg: 'rgba(16,185,129,0.12)',  color: '#34D399', border: 'rgba(16,185,129,0.25)' },
  Hyderabad: { bg: 'rgba(245,158,11,0.12)',  color: '#FBBF24', border: 'rgba(245,158,11,0.25)' },
  Chennai:   { bg: 'rgba(239,68,68,0.12)',   color: '#F87171', border: 'rgba(239,68,68,0.25)' },
  Pune:      { bg: 'rgba(6,182,212,0.12)',   color: '#22D3EE', border: 'rgba(6,182,212,0.25)' },
  Kolkata:   { bg: 'rgba(236,72,153,0.12)',  color: '#F472B6', border: 'rgba(236,72,153,0.25)' },
  Jaipur:    { bg: 'rgba(251,146,60,0.12)',  color: '#FB923C', border: 'rgba(251,146,60,0.25)' },
};

// Avatar color from name initial
const AVATAR_COLORS = [
  ['#2563EB','#7C3AED'], ['#7C3AED','#EC4899'], ['#10B981','#06B6D4'],
  ['#F59E0B','#EF4444'], ['#06B6D4','#2563EB'], ['#EC4899','#F59E0B'],
];

const getAvatarColors = (name = '') => {
  const idx = (name.charCodeAt(0) || 0) % AVATAR_COLORS.length;
  return AVATAR_COLORS[idx];
};

const getInitials = (name = '') => {
  const parts = name.trim().split(' ');
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return name.slice(0, 2).toUpperCase();
};

// Recency indicator: green <30d, amber 30-90d, red >90d
const getRecencyInfo = (dateStr) => {
  if (!dateStr) return { color: 'var(--text-muted)', dot: '#64748B', label: '-' };
  try {
    const days = Math.floor((Date.now() - new Date(dateStr)) / 86400000);
    if (days <= 30)  return { color: 'var(--success-color)',  dot: '#10B981', days };
    if (days <= 90)  return { color: 'var(--warning-color)',  dot: '#F59E0B', days };
    return           { color: 'var(--danger-color)',           dot: '#EF4444', days };
  } catch { return { color: 'var(--text-muted)', dot: '#64748B', days: null }; }
};

const formatCurrency = (val) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(val);

const formatDate = (dateStr) => {
  if (!dateStr) return '-';
  try {
    return new Date(dateStr).toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' });
  } catch { return dateStr; }
};

const CustomerTable = ({ customers = [], total = 0, page = 1, pageSize = 20, onPageChange }) => {
  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <div className="ct-container">
      <div className="ct-wrapper">
        <table className="ct-table">
          <thead>
            <tr>
              <th>Customer</th>
              <th>City</th>
              <th>Contact</th>
              <th>Total Spend</th>
              <th>Orders</th>
              <th>Last Purchase</th>
            </tr>
          </thead>
          <tbody>
            {customers.length === 0 ? (
              <tr>
                <td colSpan="6">
                  <div className="ct-empty">
                    <span className="ct-empty-icon">🔍</span>
                    <p>No customers found matching your search.</p>
                    <span>Try a different name, email, or city filter.</span>
                  </div>
                </td>
              </tr>
            ) : (
              customers.map((c, i) => {
                const [c1, c2] = getAvatarColors(c.name);
                const recency = getRecencyInfo(c.last_purchase_date);
                const cityStyle = CITY_COLORS[c.city] || { bg: 'rgba(100,116,139,0.12)', color: '#94A3B8', border: 'rgba(100,116,139,0.2)' };
                const isHighSpender = c.total_spend > 5000;
                const isFrequent = c.order_count >= 8;

                return (
                  <tr key={c.id} className="ct-row" style={{ animationDelay: `${i * 0.03}s` }}>

                    {/* Name + avatar */}
                    <td className="ct-name-cell">
                      <div className="ct-avatar" style={{ background: `linear-gradient(135deg, ${c1}, ${c2})` }}>
                        {getInitials(c.name)}
                      </div>
                      <div className="ct-name-info">
                        <span className="ct-name">
                          {c.name}
                          {isHighSpender && <span className="ct-badge-vip" title="High spender">⭐</span>}
                          {isFrequent && <span className="ct-badge-freq" title="Frequent buyer">🔥</span>}
                        </span>
                      </div>
                    </td>

                    {/* City badge */}
                    <td>
                      <span className="ct-city-badge" style={{
                        background: cityStyle.bg,
                        color: cityStyle.color,
                        border: `1px solid ${cityStyle.border}`,
                      }}>
                        {c.city}
                      </span>
                    </td>

                    {/* Email + phone stacked */}
                    <td className="ct-contact-cell">
                      <span className="ct-email">{c.email}</span>
                      <span className="ct-phone">{c.phone}</span>
                    </td>

                    {/* Spend */}
                    <td>
                      <span className={`ct-spend ${isHighSpender ? 'ct-spend--high' : ''}`}>
                        {formatCurrency(c.total_spend)}
                      </span>
                    </td>

                    {/* Orders */}
                    <td>
                      <div className="ct-orders">
                        <span className={`ct-order-count ${isFrequent ? 'ct-order-count--high' : ''}`}>
                          {c.order_count}
                        </span>
                        <div className="ct-order-bar-wrap">
                          <div
                            className="ct-order-bar-fill"
                            style={{ width: `${Math.min((c.order_count / 15) * 100, 100)}%` }}
                          />
                        </div>
                      </div>
                    </td>

                    {/* Last purchase + recency dot */}
                    <td>
                      <div className="ct-recency">
                        <span className="ct-recency-dot" style={{ background: recency.dot, boxShadow: `0 0 6px ${recency.dot}` }} />
                        <span className="ct-recency-date" style={{ color: recency.color }}>
                          {formatDate(c.last_purchase_date)}
                        </span>
                      </div>
                    </td>

                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Internal pagination (only if onPageChange passed) */}
      {onPageChange && (
        <div className="ct-pagination">
          <span className="ct-pagination-info">Page {page} of {totalPages}</span>
          <div className="ct-pagination-btns">
            <button className="cpag-btn" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>← Prev</button>
            <button className="cpag-btn" disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}>Next →</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default CustomerTable;
