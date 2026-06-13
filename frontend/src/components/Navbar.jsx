import React from 'react';

const Navbar = ({ title }) => {
  return (
    <header className="navbar">
      <div className="navbar-left">
        <h2 style={{ fontSize: '1.2rem', fontWeight: 600 }}>{title || 'Dashboard'}</h2>
      </div>
      <div className="navbar-right">
        <div className="status-indicator">
          <span className="status-dot"></span>
          <span>CRM Engine Online</span>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
