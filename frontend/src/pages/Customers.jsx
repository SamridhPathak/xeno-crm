import React, { useState, useEffect } from "react";
import client from "../api/client";
import CustomerTable from "../components/CustomerTable";

export default function Customers() {
  const [customers, setCustomers] = useState([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [city, setCity] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [searchFocused, setSearchFocused] = useState(false);

  const CITIES = ["Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Chennai", "Pune", "Kolkata", "Jaipur"];

  const fetchCustomers = async () => {
    setLoading(true);
    try {
      const params = { page, limit: 20 };
      if (search) params.search = search;
      if (city) params.city = city;
      const res = await client.get("/api/customers", { params });
      setCustomers(res.data.customers || res.data || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchCustomers(); }, [search, city, page]);

  const totalPages = Math.ceil(total / 20) || 1;

  return (
    <div className="page">
      {/* ── Header ── */}
      <div className="page-header customers-page-header">
        <div>
          <h1>Customers</h1>
          <span className="page-subtitle">{total.toLocaleString()} total customers</span>
        </div>
        {/* Quick stat chips */}
        <div className="customers-meta-chips">
          <div className="meta-chip">
            <span className="meta-chip-icon">👥</span>
            <span className="meta-chip-value">{total.toLocaleString()}</span>
            <span className="meta-chip-label">Total</span>
          </div>
          <div className="meta-chip">
            <span className="meta-chip-icon">🏙️</span>
            <span className="meta-chip-value">{CITIES.length}</span>
            <span className="meta-chip-label">Cities</span>
          </div>
          <div className="meta-chip">
            <span className="meta-chip-icon">📄</span>
            <span className="meta-chip-value">Pg {page}/{totalPages}</span>
            <span className="meta-chip-label">Page</span>
          </div>
        </div>
      </div>

      {/* ── Filters ── */}
      <div className="customers-filters">
        {/* Search with icon */}
        <div className={`customers-search-wrap ${searchFocused ? "focused" : ""}`}>
          <svg className="customers-search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none">
            <circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="2"/>
            <path d="M21 21l-4.35-4.35" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
          <input
            className="customers-search-input"
            placeholder="Search by name or email..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            onFocus={() => setSearchFocused(true)}
            onBlur={() => setSearchFocused(false)}
          />
          {search && (
            <button className="customers-search-clear" onClick={() => { setSearch(""); setPage(1); }}>
              ✕
            </button>
          )}
        </div>

        {/* City filter */}
        <div className="customers-city-wrap">
          <svg className="customers-city-icon" width="14" height="14" viewBox="0 0 24 24" fill="none">
            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" fill="currentColor"/>
          </svg>
          <select
            className="customers-city-select"
            value={city}
            onChange={(e) => { setCity(e.target.value); setPage(1); }}
          >
            <option value="">All Cities</option>
            {CITIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <svg className="customers-city-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none">
            <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>

        {/* Active filter badge */}
        {city && (
          <div className="customers-active-filter">
            <span>📍 {city}</span>
            <button onClick={() => { setCity(""); setPage(1); }}>✕</button>
          </div>
        )}
      </div>

      {/* ── Table ── */}
      {loading ? (
        <div className="customers-skeleton">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="skeleton-row" style={{ animationDelay: `${i * 0.05}s` }}>
              <div className="skeleton-avatar" />
              <div className="skeleton-lines">
                <div className="skeleton-line skeleton-line--name" />
                <div className="skeleton-line skeleton-line--email" />
              </div>
              <div className="skeleton-pill" />
              <div className="skeleton-line skeleton-line--mid" />
              <div className="skeleton-line skeleton-line--short" />
              <div className="skeleton-line skeleton-line--short" />
            </div>
          ))}
        </div>
      ) : (
        <CustomerTable customers={customers} />
      )}

      {/* ── Pagination ── */}
      {!loading && (
        <div className="customers-pagination">
          <span className="customers-pagination-info">
            Showing <strong>{((page - 1) * 20) + 1}–{Math.min(page * 20, total)}</strong> of <strong>{total.toLocaleString()}</strong> customers
          </span>
          <div className="customers-pagination-controls">
            <button
              className="cpag-btn"
              disabled={page === 1}
              onClick={() => setPage(1)}
              title="First page"
            >«</button>
            <button
              className="cpag-btn"
              disabled={page === 1}
              onClick={() => setPage((p) => p - 1)}
            >← Prev</button>
            <span className="cpag-page-indicator">
              <span className="cpag-current">{page}</span>
              <span className="cpag-sep">/</span>
              <span className="cpag-total">{totalPages}</span>
            </span>
            <button
              className="cpag-btn"
              disabled={customers.length < 20}
              onClick={() => setPage((p) => p + 1)}
            >Next →</button>
            <button
              className="cpag-btn"
              disabled={customers.length < 20}
              onClick={() => setPage(totalPages)}
              title="Last page"
            >»</button>
          </div>
        </div>
      )}
    </div>
  );
}
