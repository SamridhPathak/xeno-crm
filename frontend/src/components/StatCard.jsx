import React from 'react';

const StatCard = ({ title, value, subtext, icon }) => {
  return (
    <div className="card stat-card">
      <div className="stat-header">
        <span className="stat-title">{title}</span>
        {icon && <div className="stat-icon">{icon}</div>}
      </div>
      <div className="stat-value">{value}</div>
      {subtext && <div className="stat-subtext">{subtext}</div>}
    </div>
  );
};

export default StatCard;
