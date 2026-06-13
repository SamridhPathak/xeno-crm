import React, { useState, useEffect } from "react";
import client from "../api/client";
import SegmentCard from "../components/SegmentCard";

export default function Segments() {
  const [segments, setSegments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    client.get("/api/segments").then((res) => {
      setSegments(res.data.segments || res.data || []);
      setLoading(false);
    });
  }, []);

  return (
    <div className="page">
      <div className="page-header">
        <h1>Segments</h1>
        <span className="page-subtitle">AI-powered audience builder</span>
      </div>

      {loading ? (
        <div className="page-loading">Loading segments...</div>
      ) : (
        <div className="segments-grid">
          {segments.map((s) => <SegmentCard key={s.id} segment={s} />)}
        </div>
      )}
    </div>
  );
}