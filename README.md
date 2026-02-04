# RideShare Bot 🚕

A production-ready Telegram bot that simulates a ride-matching system with FSM-driven interactions, database-backed persistence, and role-based user flows. Demonstrates system design, state management, smart matching algorithms, and production deployment with webhooks.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-20.7-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Bot Commands & UI](#bot-commands--ui)
- [Setup Instructions](#setup-instructions)
- [Deployment](#deployment)
- [Screenshots](#screenshots)
- [Future Enhancements](#future-enhancements)
- [License](#license)

## 🎯 Overview

Many ride-hailing systems require complex infrastructure. This project demonstrates how core ride-matching logic, state management, and user interaction can be implemented using Telegram Bots and dummy location data.

**Key principle**: FSM manages interaction flow, while the database is the single source of truth for ride state.

## ✨ Features

### For Riders 👤
- **One-tap ride requests** with automatic driver matching
- **Real-time ride status** tracking
- **Ride cancellation** before driver acceptance
- **Driver rating system** (1-5 stars) after ride completion
- **Smart matching** based on distance and availability

### For Drivers 🚗
- **Simple registration** with name and vehicle type
- **Availability toggle** (go available/offline)
- **Ride notifications** with accept/decline options
- **Driver statistics** (rating, total rides)
- **One-ride-at-a-time** constraint enforcement

### For Admins 🛠
- **Driver management** - view all registered drivers
- **Active ride monitoring** - track ongoing rides
- **System statistics** - total drivers, rides, completion rates

### Technical Highlights 🔧
- ✅ **Domain enums** for type-safe constants (prevents typos)
- ✅ **Atomic transactions** for ride assignment (prevents race conditions)
- ✅ **Correlation ID logging** (ride_id, user_id) for production debugging
- ✅ **FSM-driven workflows** with clear state transitions
- ✅ **Smart matching algorithm** using Haversine distance
- ✅ **Database persistence** (SQLite → PostgreSQL ready)
- ✅ **Webhook support** for production deployment

## 🛠 Tech Stack

| Component | Technology |
|-----------|-----------|
| **Bot Framework** | python-telegram-bot 20.7 |
| **Database** | SQLAlchemy 2.0 + SQLite/PostgreSQL |
| **State Management** | ConversationHandler (FSM) |
| **Async Runtime** | asyncio + aiosqlite |
| **Configuration** | python-dotenv |
| **Logging** | Python logging with correlation IDs |

## 🏗 Architecture

```
Telegram User
     ↓
Bot Handlers (start, driver, rider, admin)
     ↓
FSM Layer (State Management)
     ↓
Services (Matching, Notifications, Location)
     ↓
Database (SQLAlchemy + SQLite/PostgreSQL)
```

### Project Structure

```
bot/
├── app.py                      # Entry point
├── config.py                   # Environment configuration
├── enums.py                    # Domain enums (RideStatus, VehicleType)
├── requirements.txt            # Dependencies
├── database/
│   ├── db.py                   # Database operations with transactions
│   └── models.py               # SQLAlchemy models
├── handlers/
│   ├── start.py                # Welcome & role selection
│   ├── driver.py               # Driver registration & management
│   ├── rider.py                # Ride requests & tracking
│   └── admin.py                # Admin panel
├── fsm/
│   ├── driver_states.py        # Driver FSM states
│   └── rider_states.py         # Rider FSM states
├── keyboards/
│   ├── reply.py                # Reply keyboards
│   └── inline.py               # Inline keyboards
├── services/
│   ├── matching.py             # Driver matching algorithm
│   ├── notifications.py        # User notifications
│   └── location.py             # Dummy location utilities
└── utils/
    ├── logger.py               # Logging with correlation IDs
    └── validators.py           # Input validation
```

## 🤖 Bot Commands & UI

### Commands
- `/start` - Main menu with role selection
- `/help` - Show help information

### User Flows

**Rider Flow:**
```
/start → Request Ride → Searching... → Driver Assigned → 
Ride Started → Ride Completed → Rate Driver (1-5 ⭐)
```

**Driver Flow:**
```
/start → Register (Name + Vehicle) → Go Available → 
Receive Request → Accept/Decline → Start Ride → Complete Ride
```

### Button-Driven UX

**Main Menu:**
```
[ 🚗 I'm a Driver ] [ 👤 Request a Ride ]
[ ℹ️ Help ]
```

**Driver Menu:**
```
[ ✅ Go Available ]
[ 📊 My Stats ]
[ 🏠 Main Menu ]
```

**Rider Menu:**
```
[ 🚕 Request Ride ]
[ 🏠 Main Menu ]
```

**Ride Confirmation (Inline):**
```
🚕 New Ride Request!
Rider: @username
Distance: 2.3 km

[ ✅ Accept Ride ] [ ❌ Decline ]
```

**Rating System (Inline):**
```
How was your ride?

[ ⭐ ] [ ⭐⭐ ] [ ⭐⭐⭐ ] [ ⭐⭐⭐⭐ ] [ ⭐⭐⭐⭐⭐ ]
```

## 🚀 Setup Instructions

### Prerequisites
- Python 3.9 or higher
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd Rideshare-Bot
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   # Copy example env file
   cp .env.example .env
   
   # Edit .env and add your bot token
   # BOT_TOKEN=your_bot_token_here
   ```

5. **Run the bot**
   ```bash
   python app.py
   ```

The bot will start in development mode with long polling. Open Telegram and send `/start` to your bot!

### Database Migration (SQLite → PostgreSQL)

To use PostgreSQL instead of SQLite:

1. **Update DATABASE_URL in .env:**
   ```
   DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbname
   ```

2. **Install asyncpg:**
   ```bash
   pip install asyncpg
   ```

3. **Restart the bot** - tables will be created automatically

## 🌐 Deployment

### Railway Deployment

1. **Create Railway account** at [railway.app](https://railway.app)

2. **Create new project** and add PostgreSQL database

3. **Set environment variables:**
   ```
   BOT_TOKEN=your_bot_token
   ENVIRONMENT=production
   WEBHOOK_URL=https://your-app.railway.app
   DATABASE_URL=<provided by Railway>
   ADMIN_IDS=your_telegram_user_id
   ```

4. **Deploy:**
   ```bash
   # Connect to Railway
   railway login
   
   # Deploy
   railway up
   ```

5. **Verify webhook:**
   ```bash
   curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo
   ```

### Alternative: Render Deployment

1. Create new Web Service on [render.com](https://render.com)
2. Connect your GitHub repository
3. Set environment variables (same as Railway)
4. Deploy!

## 📸 Screenshots

> **Note**: Add screenshots here showing:
> - Welcome screen
> - Driver registration flow
> - Ride request process
> - Driver confirmation screen
> - Rating system

## 🔮 Future Enhancements

Although the project uses dummy location data, the system is designed so that real GPS or map APIs can be integrated later:

- **Real GPS Integration** - Use Telegram's location sharing
- **Map Integration** - Google Maps / OpenStreetMap for routes
- **Payment System** - Stripe/PayPal integration
- **Push Notifications** - Real-time ride updates
- **Ride History** - View past rides for riders/drivers
- **Driver Verification** - Document upload and approval
- **Multi-language Support** - i18n for global reach
- **Analytics Dashboard** - Web dashboard for admins

## 📊 Key Skills Demonstrated

This project showcases:

✅ Telegram Bot API (python-telegram-bot)  
✅ FSM-based state management  
✅ Database design (SQLAlchemy)  
✅ Backend logic & workflows  
✅ UX design with keyboards  
✅ Logging & error handling  
✅ Production deployment (Railway/Render)  
✅ Atomic transactions & race condition prevention  
✅ Domain modeling with enums  
✅ Correlation ID logging for debugging  

## 📝 License

MIT License - feel free to use this project for learning or your portfolio!

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

For questions or feedback, reach out via [your contact method].

---

**Built with ❤️ as a portfolio project to demonstrate production-ready bot development**
