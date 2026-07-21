# RideShare Deployment Guide 🚀

This guide explains how to deploy the RideShare Bot and Admin Dashboard.

## Primary Deployment: Docker Compose (Recommended)

We have containerized the entire application, making it incredibly easy to run the FastAPI backend, the Telegram Bot, and the Next.js Admin Dashboard with a single command.

### Prerequisites
- Docker and Docker Compose installed on your machine or server.
- A Telegram Bot Token from BotFather.

### Step 1: Configuration
Create a `.env` file in the root directory and add your bot token:
```bash
BOT_TOKEN=your_telegram_bot_token_here
ENVIRONMENT=production
```

### Step 2: Build and Run
From the root of the project, run:
```bash
docker compose up -d --build
```

This will:
1. Build the Python backend and Next.js frontend images.
2. Run database migrations using Alembic.
3. Start the FastAPI Admin server on port `8001`.
4. Start the Telegram Bot in the background.
5. Start the Next.js Dashboard on port `3000`.

### Step 3: Access the Application
- **Telegram Bot**: Open Telegram and send `/start` to your bot.
- **Admin Dashboard**: Navigate to `http://localhost:3000` in your web browser.
- **API Docs**: Navigate to `http://localhost:8001/docs`.

### Step 4: Stopping the Application
To stop the application, run:
```bash
docker compose down
```
*(Note: Your database is stored safely in `rideshare.db` via a volume mount and will persist across restarts.)*

---

## Alternative: Railway Deployment 🚂

If you want to host the bot for free in the cloud without managing your own server, you can deploy it to Railway.

### Prerequisites
- GitHub account
- Railway account (sign up at [railway.app](https://railway.app))

### Step 1: Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit: RideShare Bot"
git remote add origin https://github.com/YOUR_USERNAME/telegram-rideshare-bot.git
git branch -M main
git push -u origin main
```

### Step 2: Create Railway Project
1. Go to [railway.app](https://railway.app)
2. Click "Start a New Project" → "Deploy from GitHub repo"
3. Select your repository.

### Step 3: Configure Environment Variables
1. Go to the "Variables" tab for your service.
2. Add the following variables:
```
BOT_TOKEN=your_bot_token_from_botfather
ENVIRONMENT=production
WEBHOOK_URL=https://your-app.railway.app
ADMIN_IDS=your_telegram_user_id
```

### Step 4: Deploy
Railway will automatically build and deploy your application. Check the Logs tab to verify it started successfully!
