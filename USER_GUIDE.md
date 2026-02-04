# RideShare Bot - Complete User Guide 📚

## Table of Contents
1. [Getting Started](#getting-started)
2. [For Riders](#for-riders)
3. [For Drivers](#for-drivers)
4. [For Admins](#for-admins)
5. [Features Reference](#features-reference)
6. [Troubleshooting](#troubleshooting)

---

## Getting Started

### First Time Setup

1. **Find the bot** on Telegram (search for your bot's username)
2. **Send** `/start` to begin
3. **Choose your role**:
   - 🚗 I'm a Driver - Register as a driver
   - 👤 Request a Ride - Use as a rider

---

## For Riders 👤

### Feature 1: Request a Ride

**Step-by-step:**

1. Send `/start` to the bot
2. Tap **"👤 Request a Ride"**
3. Tap **"🚕 Request Ride"**
4. Wait while the bot searches for nearby drivers
5. You'll receive a notification when a driver is assigned:
   ```
   🚕 Driver Found!
   👤 Driver: John Doe
   🚗 Vehicle: Car
   📍 Distance: 2.3 km away
   ```

**What happens next:**
- Driver receives your request
- Driver can accept or decline
- If accepted, ride starts automatically
- You'll get "Ride Started!" notification

---

### Feature 2: Check Ride Status

**Step-by-step:**

1. During an active ride, tap **"📍 Ride Status"**
2. You'll see:
   ```
   📍 Ride Status
   
   🆔 Ride ID: 42
   📊 Status: ONGOING
   
   👤 Driver: John Doe
   🚗 Vehicle: Car
   ⭐ Rating: 4.8
   📏 Distance: 2.3 km
   ```

**When to use:**
- Check driver details
- See ride progress
- Get ride ID for reference

---

### Feature 3: Cancel a Ride

**Step-by-step:**

1. Tap **"❌ Cancel Ride"** button
2. Confirm cancellation
3. You'll see: "✅ Ride Cancelled"

**Important:**
- ✅ Can cancel: Before ride starts (REQUESTED/ASSIGNED status)
- ❌ Cannot cancel: After ride starts (ONGOING status)
- Driver will be notified if assigned

---

### Feature 4: Rate Your Driver

**Step-by-step:**

1. After ride completes, you'll automatically receive:
   ```
   ✅ Ride Completed!
   Thank you for using RideShare Bot. Please rate your driver.
   
   How was your ride?
   [ ⭐ ] [ ⭐⭐ ] [ ⭐⭐⭐ ] [ ⭐⭐⭐⭐ ] [ ⭐⭐⭐⭐⭐ ]
   ```

2. Tap the stars to rate (1-5)
3. Rating is saved and updates driver's average

**Rating Guide:**
- ⭐ - Poor service
- ⭐⭐ - Below average
- ⭐⭐⭐ - Average
- ⭐⭐⭐⭐ - Good
- ⭐⭐⭐⭐⭐ - Excellent

---

### Feature 5: Return to Main Menu

**Step-by-step:**

1. Tap **"🏠 Main Menu"** at any time
2. Returns to welcome screen
3. Choose driver or rider mode again

---

## For Drivers 🚗

### Feature 1: Driver Registration

**Step-by-step:**

1. Send `/start` to the bot
2. Tap **"🚗 I'm a Driver"**
3. **Enter your name** when prompted
   - Example: "John Doe"
   - Must be 2-50 characters
4. **Select vehicle type**:
   - 🚗 Car
   - 🏍 Motorcycle
   - 🚐 Van
   - 🛵 Bike
5. You'll see confirmation:
   ```
   ✅ Registration Complete!
   
   👤 Name: John Doe
   🚗 Vehicle: Car
   📍 Location: Set
   
   You can now go available to start receiving ride requests!
   ```

**What happens:**
- Your profile is created
- Random location assigned (dummy data)
- You start as OFFLINE
- Can now toggle availability

---

### Feature 2: Go Available

**Step-by-step:**

1. From driver menu, tap **"✅ Go Available"**
2. You'll see:
   ```
   ✅ You are now AVAILABLE!
   
   You will receive ride requests from nearby riders.
   ```
3. Your status changes to AVAILABLE
4. You can now receive ride requests

**Requirements:**
- ✅ Must be registered as driver
- ✅ Cannot have active ride
- ✅ Must be offline first

---

### Feature 3: Receive & Accept Ride Requests

**Step-by-step:**

1. When a rider requests a ride, you'll receive:
   ```
   🚕 New Ride Request!
   
   👤 Rider: Jane Smith
   📍 Pickup: 9.023°N, 38.746°E
   🛣 Distance: 2.3 km
   
   Please confirm to accept this ride.
   
   [ ✅ Accept Ride ] [ ❌ Decline ]
   ```

2. **To Accept:**
   - Tap **"✅ Accept Ride"**
   - Ride status changes to ONGOING
   - Rider is notified
   - You'll see:
     ```
     ✅ Ride Accepted!
     
     👤 Rider: Jane Smith
     📍 Pickup: 9.023, 38.746
     
     Ride is now in progress.
     ```

3. **To Decline:**
   - Tap **"❌ Decline"**
   - You remain available
   - Rider is notified (may get another driver)

---

### Feature 4: Complete a Ride

**Step-by-step:**

1. After picking up rider and completing journey
2. Tap **"✅ Complete Ride"** button
3. You'll see:
   ```
   ✅ Ride Completed!
   
   Great job! You are now available for new rides.
   ```
4. Your status returns to AVAILABLE
5. Rider receives rating prompt
6. Your total rides count increases

---

### Feature 5: Go Offline

**Step-by-step:**

1. From driver menu, tap **"❌ Go Offline"**
2. You'll see:
   ```
   ❌ You are now OFFLINE
   
   You will not receive any ride requests.
   ```
3. You stop receiving ride requests
4. Can go available again anytime

**When to use:**
- Taking a break
- End of shift
- Need to stop receiving requests

---

### Feature 6: View Driver Stats

**Step-by-step:**

1. From driver menu, tap **"📊 My Stats"**
2. You'll see:
   ```
   📊 Your Driver Stats
   
   👤 Name: John Doe
   🚗 Vehicle: Car
   ⭐ Rating: 4.8/5.0
   🚕 Total Rides: 15
   📍 Status: ✅ Available
   ```

**Stats explained:**
- **Rating**: Average of all rider ratings
- **Total Rides**: Number of completed rides
- **Status**: Current availability

---

## For Admins 🛠

### Feature 1: Access Admin Panel

**Step-by-step:**

1. Make sure your Telegram user ID is in `ADMIN_IDS` (in `.env` file)
2. Send `/start` to the bot
3. Type `/admin` or send "🛠 Admin"
4. You'll see:
   ```
   🛠 Admin Panel
   
   Welcome to the admin dashboard.
   
   [ 👥 All Drivers ] [ 🚕 Active Rides ]
   [ 📊 Statistics ]
   [ 🏠 Main Menu ]
   ```

**Note:** Only users in ADMIN_IDS can access this

---

### Feature 2: View All Drivers

**Step-by-step:**

1. From admin panel, tap **"👥 All Drivers"**
2. You'll see list of all registered drivers:
   ```
   👥 All Drivers
   
   👤 John Doe
   🚗 Car
   ⭐ 4.8 (15 rides)
   📍 ✅ Available
   🆔 ID: 123456789
   
   👤 Jane Smith
   🏍 Motorcycle
   ⭐ 5.0 (8 rides)
   📍 ❌ Offline
   🆔 ID: 987654321
   ```

**Information shown:**
- Driver name
- Vehicle type
- Rating and total rides
- Current status (Available/Offline)
- Telegram user ID

---

### Feature 3: View Active Rides

**Step-by-step:**

1. From admin panel, tap **"🚕 Active Rides"**
2. You'll see all ongoing rides:
   ```
   🚕 Active Rides
   
   🆔 Ride #42
   📊 Status: ONGOING
   👤 Rider ID: 123456789
   🚗 Driver ID: 987654321
   
   🆔 Ride #43
   📊 Status: ASSIGNED
   👤 Rider ID: 111222333
   🚗 Driver ID: 444555666
   ```

**Statuses:**
- **REQUESTED**: Waiting for driver
- **ASSIGNED**: Driver assigned, waiting confirmation
- **ONGOING**: Ride in progress

---

### Feature 4: View System Statistics

**Step-by-step:**

1. From admin panel, tap **"📊 Statistics"**
2. You'll see system overview:
   ```
   📊 System Statistics
   
   👥 Total Drivers: 25
   ✅ Available Drivers: 12
   
   🚕 Total Rides: 150
   ✅ Completed: 142
   🔄 Active: 3
   ```

**Metrics explained:**
- **Total Drivers**: All registered drivers
- **Available Drivers**: Currently available
- **Total Rides**: All ride requests ever
- **Completed**: Successfully finished rides
- **Active**: Currently ongoing rides

---

## Features Reference

### Quick Command List

| Command | Description |
|---------|-------------|
| `/start` | Show main menu |
| `/help` | Show help information |
| `/admin` | Access admin panel (admins only) |

### Button Navigation

**Main Menu:**
- 🚗 I'm a Driver - Enter driver mode
- 👤 Request a Ride - Enter rider mode
- ℹ️ Help - Show help

**Driver Menu:**
- ✅ Go Available - Start receiving requests
- ❌ Go Offline - Stop receiving requests
- 📊 My Stats - View your statistics
- 🏠 Main Menu - Return to start

**Rider Menu:**
- 🚕 Request Ride - Find a driver
- 📍 Ride Status - Check current ride
- ❌ Cancel Ride - Cancel active ride
- 🏠 Main Menu - Return to start

**Admin Menu:**
- 👥 All Drivers - View all drivers
- 🚕 Active Rides - View ongoing rides
- 📊 Statistics - System overview
- 🏠 Main Menu - Return to start

---

## Troubleshooting

### "No drivers available"

**Problem:** Can't find a driver for your ride

**Solutions:**
1. Make sure at least one driver is registered
2. Check that driver is AVAILABLE (not offline)
3. Wait a moment and try again
4. Check if drivers are within 10 km radius

---

### "You already have an active ride"

**Problem:** Can't request a new ride

**Solutions:**
1. Complete your current ride first
2. Or cancel current ride (if not started)
3. Check ride status to see current state

---

### "Cannot cancel a ride that's already in progress"

**Problem:** Trying to cancel ongoing ride

**Explanation:**
- Rides can only be cancelled before they start
- Once driver accepts and starts ride, cancellation is disabled
- This protects drivers who are already en route

**Solution:**
- Wait for ride to complete
- Contact driver directly if needed

---

### "You cannot go available while you have an active ride"

**Problem:** Driver trying to go available during ride

**Solution:**
1. Complete your current ride first
2. Tap "✅ Complete Ride"
3. Then you can go available again

---

### Bot doesn't respond

**Solutions:**
1. Check bot is running (`python app.py` should be active)
2. Send `/start` to reset
3. Check you're messaging the correct bot
4. Restart the bot if needed

---

### Driver doesn't receive ride requests

**Checklist:**
1. ✅ Driver is registered
2. ✅ Driver is AVAILABLE (not offline)
3. ✅ No active ride
4. ✅ Bot is running
5. ✅ Rider is requesting rides

---

## Tips & Best Practices

### For Riders
- ⭐ Always rate your drivers honestly
- 📍 Check ride status if unsure
- ❌ Cancel early if you change plans
- 🏠 Use main menu to switch modes

### For Drivers
- ✅ Go available when ready for rides
- ❌ Go offline during breaks
- 📊 Check stats to track performance
- 🚗 Complete rides promptly

### For Admins
- 📊 Monitor statistics regularly
- 👥 Check driver activity
- 🚕 Track active rides
- 🔍 Use for debugging issues

---

## Advanced Features

### Database Persistence
- All data is saved to database
- Survives bot restarts
- Ride history maintained
- Ratings preserved

### Smart Matching
- Distance-based algorithm
- Finds nearest available driver
- Within 10 km radius
- Instant assignment

### State Management
- FSM-driven workflows
- One ride at a time
- State validation
- Error prevention

### Logging
- All actions logged
- Correlation IDs (ride_id, user_id)
- Error tracking
- Production debugging

---

## Need More Help?

- 📖 See [README.md](README.md) for technical details
- 🚀 See [QUICKSTART.md](QUICKSTART.md) for setup
- 🌐 See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment
- 📊 See [walkthrough.md](walkthrough.md) for architecture

---

**Enjoy using RideShare Bot!** 🚕✨
