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

  return (
    <div className="page">
      <div className="page-header">
        <h1>Customers</h1>
        <span className="page-subtitle">{total.toLocaleString()} total customers</span>
      </div>

      <div className="filters-row">
        <input
          className="search-input"
          placeholder="Search by name or email..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
        />
        <select className="filter-select" value={city} onChange={(e) => { setCity(e.target.value); setPage(1); }}>
          <option value="">All Cities</option>
          {CITIES.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {loading ? (
        <div className="page-loading">Loading customers...</div>
      ) : (
        <>
          <CustomerTable customers={customers} />
          <div className="pagination">
            <button className="btn-ghost" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>← Prev</button>
            <span className="page-info">Page {page}</span>
            <button className="btn-ghost" disabled={customers.length < 20} onClick={() => setPage((p) => p + 1)}>Next →</button>
          </div>
        </>
      )}
    </div>
  );
}