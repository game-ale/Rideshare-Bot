# Railway Deployment Guide 🚂

Deploy your RideShare Bot to Railway for 24/7 availability!

## Prerequisites

- GitHub account
- Railway account (sign up at [railway.app](https://railway.app))
- Bot token from BotFather

## Step 1: Push to GitHub

1. **Initialize git** (if not already done):
   ```bash
   cd c:\bot\Rideshare-Bot
   git init
   git add .
   git commit -m "Initial commit: RideShare Bot"
   ```

2. **Create GitHub repository**:
   - Go to [github.com/new](https://github.com/new)
   - Name it `telegram-rideshare-bot`
   - Don't initialize with README (we already have one)
   - Click "Create repository"

3. **Push to GitHub**:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/telegram-rideshare-bot.git
   git branch -M main
   git push -u origin main
   ```

## Step 2: Create Railway Project

1. Go to [railway.app](https://railway.app)
2. Click "Start a New Project"
3. Select "Deploy from GitHub repo"
4. Authorize Railway to access your GitHub
5. Select your `telegram-rideshare-bot` repository

## Step 3: Add PostgreSQL Database

1. In your Railway project, click "+ New"
2. Select "Database" → "PostgreSQL"
3. Railway will automatically create a database
4. Copy the `DATABASE_URL` (you'll need it in Step 4)

## Step 4: Configure Environment Variables

1. Click on your bot service (not the database)
2. Go to "Variables" tab
3. Add the following variables:

```
BOT_TOKEN=your_bot_token_from_botfather
ENVIRONMENT=production
WEBHOOK_URL=https://your-app.railway.app
ADMIN_IDS=your_telegram_user_id
DATABASE_URL=postgresql+asyncpg://... (from Step 3)
LOG_LEVEL=INFO
WEBAPP_HOST=0.0.0.0
WEBAPP_PORT=8000
```

**Important Notes:**
- For `WEBHOOK_URL`, use the Railway-provided domain (found in "Settings" → "Domains")
- For `DATABASE_URL`, replace `postgresql://` with `postgresql+asyncpg://`
- Get your Telegram user ID from [@userinfobot](https://t.me/userinfobot)

## Step 5: Deploy!

1. Railway will automatically deploy your bot
2. Check the "Deployments" tab to see progress
3. Once deployed, check logs for:
   ```
   [INFO] Starting RideShare Bot...
   [INFO] Database initialized successfully
   [INFO] Running in PRODUCTION mode with webhooks
   ```

## Step 6: Verify Webhook

Check if webhook is set correctly:

```bash
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo
```

You should see:
```json
{
  "ok": true,
  "result": {
    "url": "https://your-app.railway.app/webhook",
    "has_custom_certificate": false,
    "pending_update_count": 0
  }
}
```

## Step 7: Test Your Bot!

1. Open Telegram
2. Find your bot
3. Send `/start`
4. Everything should work exactly like in development! 🎉

## Troubleshooting

### Bot doesn't respond

**Check logs in Railway:**
1. Go to your project
2. Click on the bot service
3. Check "Deployments" → "View Logs"

**Common issues:**
- ❌ Wrong `BOT_TOKEN` → Check .env variables
- ❌ Webhook not set → Check `WEBHOOK_URL` is correct
- ❌ Database connection error → Check `DATABASE_URL` format

### "Application failed to respond"

- Make sure `WEBAPP_PORT` is set to `8000`
- Check `WEBAPP_HOST` is `0.0.0.0`
- Verify your code is listening on the correct port

### Database errors

- Make sure you replaced `postgresql://` with `postgresql+asyncpg://`
- Install `asyncpg`: Add to `requirements.txt` if missing

## Monitoring

**View logs:**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# View logs
railway logs
```

**Check database:**
1. Go to Railway dashboard
2. Click on PostgreSQL service
3. Click "Data" tab to view tables

## Updating Your Bot

1. Make changes locally
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update: description of changes"
   git push
   ```
3. Railway will automatically redeploy! 🚀

## Cost

- Railway offers **$5 free credit per month**
- This bot should stay within free tier
- PostgreSQL database is included

## Alternative: Render Deployment

If you prefer Render:

1. Go to [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repo
4. Set environment variables (same as Railway)
5. Deploy!

---

**Congratulations!** Your bot is now running 24/7 in the cloud! 🎉

For issues, check the [README.md](README.md) or Railway documentation.
