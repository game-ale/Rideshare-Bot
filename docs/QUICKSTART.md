# Quick Start Guide 🚀

Get your RideShare Bot running in 5 minutes!

## Step 1: Get Your Bot Token

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` and follow the instructions
3. Choose a name (e.g., "My RideShare Bot")
4. Choose a username (e.g., "my_rideshare_bot")
5. Copy the bot token (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

## Step 2: Configure the Bot

1. Open `.env` file in the project root
2. Add your bot token:
   ```
   BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   ```
3. Add your Telegram user ID as admin (get it from [@userinfobot](https://t.me/userinfobot)):
   ```
   ADMIN_IDS=123456789
   ```

## Step 3: Run the Bot

```bash
# Make sure you're in the project directory
cd c:\bot\Rideshare-Bot

# Run the bot
python app.py
```

You should see:
```
[2026-02-04 10:47:28] [INFO] Starting RideShare Bot...
[2026-02-04 10:47:28] [INFO] Database initialized successfully
[2026-02-04 10:47:28] [INFO] All handlers registered
[2026-02-04 10:47:28] [INFO] Running in DEVELOPMENT mode with long polling
```

## Step 4: Test the Bot

1. Open Telegram and find your bot
2. Send `/start`
3. You should see the welcome screen with buttons!

### Test as a Driver:
1. Tap "🚗 I'm a Driver"
2. Enter your name
3. Select vehicle type
4. Tap "✅ Go Available"

### Test as a Rider:
1. Open another Telegram account (or use a friend's)
2. Send `/start` to your bot
3. Tap "👤 Request a Ride"
4. Tap "🚕 Request Ride"
5. Watch the magic happen! 🎉

## Troubleshooting

### "BOT_TOKEN environment variable is required"
- Make sure you added your bot token to the `.env` file
- Check there are no extra spaces

### "No drivers available"
- Make sure at least one driver is registered and available
- Check the driver went "Available" (green button)

### Bot doesn't respond
- Check the bot is running (you should see logs in terminal)
- Make sure you're messaging the correct bot
- Try `/start` command

## Next Steps

- Add more test drivers and riders
- Test the rating system
- Check the admin panel (if you set ADMIN_IDS)
- Deploy to Railway/Render for 24/7 availability

## Need Help?

Check the main [README.md](README.md) for detailed documentation!
