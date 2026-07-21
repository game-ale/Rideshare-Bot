# RideShare Bot & AI Admin Dashboard 🚕✨

A production-ready ride-hailing platform that combines a **Telegram Bot** (for riders and drivers) with a **Next.js Admin Dashboard**, powered by a **FastAPI** backend and **AI Support Services**.

This project demonstrates full-stack expertise, architectural maturity, and AI integration for a top-tier software engineering portfolio.

![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-00a393.svg)
![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)

## 📋 Table of Contents
- [Overview](#overview)
- [Key Features](#key-features)
- [Tech Stack & Architecture](#tech-stack--architecture)
- [Deployment (Docker)](#deployment)
- [Testing & Quality](#testing--quality)
- [Future Enhancements](#future-enhancements)

## 🎯 Overview

RideShare demonstrates how a complex, multi-sided marketplace can be orchestrated efficiently. 
- The **Telegram Bot** uses Finite State Machines (FSM) to guide Riders and Drivers through booking flows, payment simulations, and AI customer support.
- The **FastAPI Backend** acts as the central brain, handling matching algorithms, surge pricing, and exposing data via REST endpoints.
- The **Next.js Dashboard** provides operational intelligence, visualizing live data and generating AI demand forecasts for platform administrators.

## ✨ Key Features

### 🤖 AI Support & Insights
- **Smart Assistant**: Rule-based intent classification handles customer issues automatically (e.g., lost items, safety concerns, late drivers) directly in the Telegram chat.
- **Demand Forecasting**: Generates simulated predictive demand models in the admin dashboard, highlighting deployment hotspots.
- **Driver Quality Analysis**: Automatically evaluates driver metrics and flags actionable items for admins.

### 🚕 Core Ride-Hailing Logic
- **Smart Matching Engine**: Distance-based geolocation matching for riders and drivers.
- **Dynamic Pricing Engine**: Calculates base fares, distance/time variants, and simulates surge pricing.
- **Payment Lifecycle**: Enforces wallet/cash payment selection before ride completion.
- **FSM Workflows**: Robust state management for driver onboarding and ride requesting.

## 🏗 Tech Stack & Architecture

| Layer | Technology |
|-----------|-----------|
| **Frontend Dashboard** | Next.js 14, React, TailwindCSS, Lucide Icons |
| **Backend API** | FastAPI, Uvicorn, Pydantic |
| **Telegram Bot** | python-telegram-bot (async) |
| **Database & ORM** | SQLite, SQLAlchemy 2.0, Alembic |
| **Testing** | Pytest, httpx, GitHub Actions CI |
| **Orchestration** | Docker, Docker Compose |

### Enterprise Patterns Implemented
- **Pydantic Validation**: Bulletproof API request/response serialization.
- **Alembic Migrations**: Professional, version-controlled database schema management.
- **Domain Enums**: Type-safe constants for database constraints.
- **Atomic Transactions**: Prevents race conditions during ride assignments.

## 🚀 Deployment

The entire stack is containerized and orchestratable with a single command.

1. **Clone the repository** and add your Telegram Bot Token to `.env`:
   ```bash
   BOT_TOKEN=your_telegram_bot_token_here
   ```

2. **Run Docker Compose**:
   ```bash
   docker-compose up -d --build
   ```

3. **Access the Application**:
   - Telegram Bot: Open Telegram and send `/start`
   - Admin Dashboard: `http://localhost:3000`
   - API Documentation: `http://localhost:8001/docs`

## 🧪 Testing & Quality

The project includes a robust asynchronous test suite covering core business logic and API endpoints.

```bash
# Run tests locally
pytest tests/ -v
```

A GitHub Actions CI pipeline (`.github/workflows/test.yml`) automatically executes these tests on every push, ensuring 100% reliability of core pricing and matching algorithms.

## 🔮 Future Enhancements
- **PostgreSQL Migration**: Swap the SQLite volume for a managed PostgreSQL instance.
- **Redis Queue**: Move the AI insights generation and heavy matching algorithms to background Celery tasks.
- **Webhooks**: Transition the Telegram bot from long-polling to webhooks for serverless deployment.
- **Maps API**: Integrate Google Maps or Mapbox for real route distance calculations instead of Haversine approximation.

---
**License**: MIT
