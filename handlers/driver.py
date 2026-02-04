"""
Driver handler for the Rideshare Bot.
Manages driver registration, availability, and ride acceptance.
"""
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, 
    MessageHandler, CallbackQueryHandler, filters
)

from database.db import (
    create_driver, get_driver, set_driver_availability,
    get_active_ride_for_user, update_ride_status, get_ride
)
from enums import VehicleType, RideStatus
from fsm.driver_states import (
    DRIVER_REGISTERING_NAME, DRIVER_REGISTERING_VEHICLE,
    DRIVER_IDLE, DRIVER_CONFIRMING_RIDE, DRIVER_ONGOING_RIDE
)
from keyboards.reply import get_driver_menu_keyboard, get_vehicle_type_keyboard
from keyboards.inline import get_start_ride_keyboard
from services.location import generate_random_location
from services.notifications import notify_driver_assigned, notify_ride_started, notify_ride_completed
from utils.logger import logger, log_with_context
from utils.validators import validate_name


# ==================== Driver Registration Flow ====================

async def driver_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Start driver registration or show driver menu if already registered.
    """
    user = update.effective_user
    driver = await get_driver(user.id)
    
    if driver:
        # Driver already registered, show menu
        await update.message.reply_text(
            f"👋 Welcome back, {driver.name}!\n\n"
            f"🚗 Vehicle: {driver.vehicle_type.value}\n"
            f"⭐ Rating: {driver.rating:.1f} ({driver.total_rides} rides)\n"
            f"{'✅ You are AVAILABLE' if driver.available else '❌ You are OFFLINE'}",
            reply_markup=get_driver_menu_keyboard(driver.available)
        )
        return ConversationHandler.END
    
    # New driver, start registration
    await update.message.reply_text(
        "🚗 <b>Driver Registration</b>\n\n"
        "Let's get you set up! Please enter your full name:",
        parse_mode="HTML"
    )
    
    log_with_context(logger, "INFO", "Driver registration started", user_id=user.id)
    return DRIVER_REGISTERING_NAME


async def driver_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle driver name input."""
    name = update.message.text.strip()
    
    # Validate name
    is_valid, error_msg = validate_name(name)
    if not is_valid:
        await update.message.reply_text(f"❌ {error_msg}\n\nPlease try again:")
        return DRIVER_REGISTERING_NAME
    
    # Store name in context
    context.user_data['driver_name'] = name
    
    await update.message.reply_text(
        f"Great, {name}! 👍\n\n"
        "Now, please select your vehicle type:",
        reply_markup=get_vehicle_type_keyboard()
    )
    
    return DRIVER_REGISTERING_VEHICLE


async def driver_vehicle_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle vehicle type selection and complete registration."""
    vehicle_text = update.message.text.strip()
    user = update.effective_user
    
    # Map button text to enum
    vehicle_map = {
        "🚗 Car": VehicleType.CAR,
        "🏍 Motorcycle": VehicleType.MOTORCYCLE,
        "🚐 Van": VehicleType.VAN,
        "🛵 Bike": VehicleType.BIKE
    }
    
    vehicle_type = vehicle_map.get(vehicle_text)
    
    if not vehicle_type:
        await update.message.reply_text(
            "❌ Invalid vehicle type. Please select from the buttons:",
            reply_markup=get_vehicle_type_keyboard()
        )
        return DRIVER_REGISTERING_VEHICLE
    
    # Generate random location for driver
    lat, lng = generate_random_location()
    
    # Create driver in database
    name = context.user_data.get('driver_name')
    driver = await create_driver(user.id, name, vehicle_type, lat, lng)
    
    await update.message.reply_text(
        "✅ <b>Registration Complete!</b>\n\n"
        f"👤 Name: {driver.name}\n"
        f"🚗 Vehicle: {driver.vehicle_type.value}\n"
        f"📍 Location: Set\n\n"
        "You can now go available to start receiving ride requests!",
        reply_markup=get_driver_menu_keyboard(False),
        parse_mode="HTML"
    )
    
    log_with_context(logger, "INFO", 
                    f"Driver {name} completed registration with {vehicle_type.value}", 
                    user_id=user.id)
    
    # Clear context
    context.user_data.clear()
    
    return ConversationHandler.END


# ==================== Driver Availability ====================

async def go_available(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set driver as available."""
    user = update.effective_user
    driver = await get_driver(user.id)
    
    if not driver:
        await update.message.reply_text("❌ You need to register as a driver first!")
        return
    
    # Check if driver has an active ride
    active_ride = await get_active_ride_for_user(user.id)
    if active_ride:
        await update.message.reply_text(
            "❌ You cannot go available while you have an active ride!\n"
            "Please complete or cancel your current ride first."
        )
        return
    
    await set_driver_availability(user.id, True)
    
    await update.message.reply_text(
        "✅ <b>You are now AVAILABLE!</b>\n\n"
        "You will receive ride requests from nearby riders.",
        reply_markup=get_driver_menu_keyboard(True),
        parse_mode="HTML"
    )


async def go_offline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set driver as offline."""
    user = update.effective_user
    
    await set_driver_availability(user.id, False)
    
    await update.message.reply_text(
        "❌ <b>You are now OFFLINE</b>\n\n"
        "You will not receive any ride requests.",
        reply_markup=get_driver_menu_keyboard(False),
        parse_mode="HTML"
    )


async def driver_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show driver statistics."""
    user = update.effective_user
    driver = await get_driver(user.id)
    
    if not driver:
        await update.message.reply_text("❌ You need to register as a driver first!")
        return
    
    stats_message = (
        "📊 <b>Your Driver Stats</b>\n\n"
        f"👤 Name: {driver.name}\n"
        f"🚗 Vehicle: {driver.vehicle_type.value}\n"
        f"⭐ Rating: {driver.rating:.1f}/5.0\n"
        f"🚕 Total Rides: {driver.total_rides}\n"
        f"📍 Status: {'✅ Available' if driver.available else '❌ Offline'}"
    )
    
    await update.message.reply_text(stats_message, parse_mode="HTML")


# ==================== Ride Acceptance ====================

async def accept_ride_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle driver accepting a ride."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    ride_id = int(query.data.split("_")[-1])
    
    # Get ride details
    ride = await get_ride(ride_id)
    
    if not ride or ride.status != RideStatus.ASSIGNED:
        await query.edit_message_text(
            "❌ This ride is no longer available.",
            parse_mode="HTML"
        )
        return
    
    # Update ride status to ONGOING
    await update_ride_status(ride_id, RideStatus.ONGOING)
    
    # Notify rider
    await notify_ride_started(context.bot, ride.rider_id, user.id, ride_id)
    
    # Update driver's message
    await query.edit_message_text(
        "✅ <b>Ride Accepted!</b>\n\n"
        f"👤 Rider: {ride.rider.name}\n"
        f"📍 Pickup: {ride.rider_lat:.3f}, {ride.rider_lng:.3f}\n\n"
        "Ride is now in progress. Tap the button below when you complete the ride.",
        reply_markup=get_start_ride_keyboard(ride_id),
        parse_mode="HTML"
    )
    
    log_with_context(logger, "INFO", "Driver accepted ride", 
                    ride_id=ride_id, user_id=user.id)


async def decline_ride_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle driver declining a ride."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    ride_id = int(query.data.split("_")[-1])
    
    # Free up driver
    await set_driver_availability(user.id, True)
    
    await query.edit_message_text(
        "❌ You declined the ride.\n\n"
        "You are still available for other ride requests.",
        parse_mode="HTML"
    )
    
    log_with_context(logger, "INFO", "Driver declined ride", 
                    ride_id=ride_id, user_id=user.id)
    
    # TODO: Reassign to another driver or notify rider


async def complete_ride_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle driver completing a ride."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    ride_id = int(query.data.split("_")[-1])
    
    # Get ride details
    ride = await get_ride(ride_id)
    
    if not ride or ride.driver_id != user.id:
        await query.edit_message_text("❌ Invalid ride.")
        return
    
    # Update ride status to COMPLETED
    await update_ride_status(ride_id, RideStatus.COMPLETED)
    
    # Notify both parties
    await notify_ride_completed(context.bot, ride.rider_id, user.id, ride_id)
    
    # Update driver's message
    await query.edit_message_text(
        "✅ <b>Ride Completed!</b>\n\n"
        "Great job! You are now available for new rides.",
        parse_mode="HTML"
    )
    
    # Set driver back to available
    await set_driver_availability(user.id, True)
    
    log_with_context(logger, "INFO", "Ride completed", 
                    ride_id=ride_id, user_id=user.id)


# ==================== Handler Setup ====================

def setup_driver_handlers(application):
    """Register driver-related handlers."""
    
    # Driver registration conversation
    driver_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🚗 I'm a Driver$"), driver_start)],
        states={
            DRIVER_REGISTERING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, driver_name_received)],
            DRIVER_REGISTERING_VEHICLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, driver_vehicle_received)],
        },
        fallbacks=[CommandHandler("start", driver_start)],
    )
    
    application.add_handler(driver_conv)
    
    # Driver menu actions
    application.add_handler(MessageHandler(filters.Regex("^✅ Go Available$"), go_available))
    application.add_handler(MessageHandler(filters.Regex("^❌ Go Offline$"), go_offline))
    application.add_handler(MessageHandler(filters.Regex("^📊 My Stats$"), driver_stats))
    
    # Ride callbacks
    application.add_handler(CallbackQueryHandler(accept_ride_callback, pattern="^accept_ride_"))
    application.add_handler(CallbackQueryHandler(decline_ride_callback, pattern="^decline_ride_"))
    application.add_handler(CallbackQueryHandler(complete_ride_callback, pattern="^complete_ride_"))
