import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Navbar from "./components/Navbar";
import Chat from "./pages/Chat";
import Dashboard from "./pages/Dashboard";
import Customers from "./pages/Customers";
import Segments from "./pages/Segments";
import Campaigns from "./pages/Campaigns";
import CampaignDetail from "./pages/CampaignDetail";

export default function App() {
  return (
    <Router>
      <div className="app-shell">
        <Sidebar />
        <div className="main-area">
          <Navbar />
          <div className="page-content">
            <Routes>
              <Route path="/" element={<Navigate to="/chat" replace />} />
              <Route path="/chat" element={<Chat />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/customers" element={<Customers />} />
              <Route path="/segments" element={<Segments />} />
              <Route path="/campaigns" element={<Campaigns />} />
              <Route path="/campaigns/:id" element={<CampaignDetail />} />
            </Routes>
          </div>
        </div>
      </div>
    </Router>
  );
}