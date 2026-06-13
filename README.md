# 🚀 XenoCRM AI

> An AI-Powered Customer Relationship Management (CRM) Platform that enables marketers to create audience segments, generate campaigns using natural language, launch campaigns, and track delivery analytics in real-time.

![Status](https://img.shields.io/badge/Status-Active-success)
![Frontend](https://img.shields.io/badge/Frontend-React-blue)
![Backend](https://img.shields.io/badge/Backend-FastAPI-green)
![Database](https://img.shields.io/badge/Database-PostgreSQL-blue)
![Cache](https://img.shields.io/badge/Cache-Redis-red)
![Queue](https://img.shields.io/badge/Queue-Celery-orange)
![AI](https://img.shields.io/badge/AI-LLM%20Powered-purple)

---

# 📖 Overview

XenoCRM AI is a full-stack CRM platform designed to simulate how modern marketing teams manage customer engagement at scale.

The platform allows users to:

* Build customer segments using natural language
* Generate personalized campaigns using an LLM-powered copilot
* Launch campaigns across communication channels
* Track delivery, open, and click events
* Analyze campaign performance through real-time analytics
* Handle delivery receipts asynchronously using event-driven architecture

The project demonstrates modern full-stack engineering practices including distributed services, asynchronous processing, AI integration, analytics tracking, and scalable backend design.

---

# ✨ Key Features

## 🤖 AI Campaign Copilot

Create campaigns using plain English.

Example:

> Create a WhatsApp campaign for repeat customers in Hyderabad promoting our weekend combo offer.

The AI Copilot can:

* Understand audience intent
* Generate customer segments
* Create campaign drafts
* Launch campaigns directly from chat
* Fall back gracefully when LLM quotas are exhausted

---

## 🎯 Customer Segmentation

Create dynamic audience segments using:

* Customer location
* Spend amount
* Purchase frequency
* Order history
* Customer activity

Example Segments:

* High spenders in Mumbai
* Repeat customers in Hyderabad
* Customers inactive for 30 days
* Customers with more than 3 purchases

---

## 📢 Campaign Management

Create and manage campaigns across:

* Email
* SMS
* WhatsApp

Campaign Lifecycle:

Draft → Sending → Completed / Failed

---

## 📈 Real-Time Analytics

Track campaign performance through:

* Delivery Rate
* Failure Rate
* Open Rate
* Click Rate
* Audience Reach
* Campaign Performance Metrics

---

## 🔄 Event Driven Receipt Processing

The system simulates real-world marketing workflows by processing:

* Delivered Events
* Failed Events
* Opened Events
* Clicked Events

All events are processed asynchronously and reflected in analytics dashboards.

---

## 🛡️ Fault Tolerance

When the LLM is unavailable:

* Segment creation falls back to Smart Rules Mode
* Campaign generation falls back to template generation
* Core CRM functionality remains operational

---

# 🏗️ System Architecture

## High-Level Architecture

```text
                        ┌────────────────────┐
                        │      React UI      │
                        └─────────┬──────────┘
                                  │
                                  ▼
                        ┌────────────────────┐
                        │ FastAPI Backend    │
                        │  CRM Engine        │
                        └─────────┬──────────┘
                                  │
          ┌───────────────────────┼────────────────────────┐
          │                       │                        │
          ▼                       ▼                        ▼

 ┌────────────────┐    ┌────────────────┐      ┌────────────────┐
 │ PostgreSQL     │    │ Redis          │      │ LLM Service    │
 │ Customer Data  │    │ Task Broker    │      │ Intent Parsing │
 └────────────────┘    └────────────────┘      └────────────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ Celery Workers  │
                         └────────┬────────┘
                                  │
                                  ▼
                      ┌─────────────────────────┐
                      │ Channel Service         │
                      │ Delivery Simulator      │
                      └──────────┬──────────────┘
                                 │
                                 ▼
                      ┌─────────────────────────┐
                      │ Receipts API            │
                      │ Event Processing        │
                      └──────────┬──────────────┘
                                 │
                                 ▼
                      ┌─────────────────────────┐
                      │ Analytics Dashboard     │
                      └─────────────────────────┘
```

---

# ⚙️ Tech Stack

## Frontend

* React
* React Router
* Axios
* Vite

## Backend

* FastAPI
* SQLAlchemy
* Pydantic

## Database

* PostgreSQL

## Caching & Messaging

* Redis
* Celery

## AI Layer

* LLM-Powered Campaign Copilot
* Natural Language Intent Parsing
* Campaign Generation
* Smart Rules Fallback Engine

## Infrastructure

* Docker
* Docker Compose

---

# 🔄 Campaign Flow

```text
User
  ↓
AI Copilot
  ↓
Intent Parsing
  ↓
Segment Creation
  ↓
Campaign Draft
  ↓
Campaign Launch
  ↓
Channel Service
  ↓
Delivery Receipts
  ↓
Analytics Processing
  ↓
Dashboard Updates
```

---

# 📊 Analytics Tracked

The platform tracks:

* Total Sent
* Delivered
* Failed
* Opened
* Clicked

Analytics are updated through asynchronous receipt processing.

---

# 🧠 AI Capabilities

## Natural Language Audience Builder

Example:

> Create a campaign for high spenders in Delhi who haven't purchased in 30 days.

The AI extracts:

* Audience Filters
* Campaign Goal
* Communication Channel
* Customer Intent

---

## Campaign Generation

The AI generates:

* Subject Lines
* Message Content
* Personalized Campaign Drafts

---

## Fallback Intelligence

If AI services become unavailable:

* Smart Rules Engine takes over segmentation
* Template Engine generates campaign content

This ensures uninterrupted CRM operations.

---

# 📸 Screenshots

### Dashboard

Coming Soon

### AI Copilot

Coming Soon

### Customers

Coming Soon

### Segments

Coming Soon

### Campaigns

Coming Soon

### Campaign Analytics

Coming Soon

---

# 🚀 Local Setup

## Clone Repository

```bash
git clone https://github.com/SamridhPathak/xeno-crm.git
cd xeno-crm
```

## Backend

```bash
cd backend
pip install -r requirements.txt
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

## Start PostgreSQL & Redis

```bash
docker compose up -d
```

## Start Backend

```bash
uvicorn app.main:app --reload
```

## Start Celery Worker

```bash
celery -A app.tasks worker --loglevel=info
```

## Start Channel Service

```bash
uvicorn app.main:app --reload --port 8001
```

---

# 🎯 Learning Outcomes

This project demonstrates:

* Full Stack Development
* Distributed System Design
* Event Driven Architecture
* AI Integration
* Asynchronous Processing
* Database Design
* API Development
* Analytics Engineering
* Production-Style Backend Design

---

# 🔮 Future Improvements

* Multi-Channel Campaign Scheduling
* Role Based Access Control (RBAC)
* Campaign A/B Testing
* Advanced Analytics Dashboard
* Real Email/SMS Integrations
* Customer Journey Automation
* Campaign Templates Library
* Predictive Customer Segmentation

---

# 📌 Deployment

Deployment links will be added after production deployment.

Frontend:
TBD

Backend:
TBD

Channel Service:
TBD

---

# 👨‍💻 Author

Samridh Pathak

Built as a solo full-stack engineering project to explore AI-assisted customer engagement, campaign automation, analytics tracking, and distributed backend architecture.
