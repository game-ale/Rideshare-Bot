"""
Rider handler for the Rideshare Bot.
Manages ride requests, status tracking, cancellations, and ratings.
"""
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)

from database.db import (
    create_rider, get_rider, create_ride, get_active_ride_for_user,
    cancel_ride, add_ride_rating, get_ride, assign_driver_to_ride
)
from enums import RideStatus
from fsm.rider_states import (
    RIDER_IDLE, RIDER_REQUESTING_RIDE, RIDER_WAITING_DRIVER,
    RIDER_RIDE_ASSIGNED, RIDER_ONGOING_RIDE, RIDER_RATING_DRIVER
)
from keyboards.reply import get_rider_menu_keyboard
from keyboards.inline import get_rating_keyboard, get_ride_confirmation_keyboard
from services.location import generate_random_location, format_distance, get_location_display
from services.matching import find_nearest_driver
from services.notifications import notify_driver_assigned, notify_rider_assigned, notify_ride_cancelled
from utils.logger import logger, log_with_context
from utils.validators import validate_name


# ==================== Rider Registration & Menu ====================

async def rider_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Start rider flow - auto-register if needed and show menu.
    """
    user = update.effective_user
    rider = await get_rider(user.id)
    
    if not rider:
        # Auto-register rider with their Telegram name
        name = user.first_name or "Rider"
        rider = await create_rider(user.id, name)
        log_with_context(logger, "INFO", f"Rider {name} auto-registered", user_id=user.id)
    
    # Check for active ride
    active_ride = await get_active_ride_for_user(user.id)
    has_active_ride = active_ride is not None
    
    welcome_msg = f"👋 Welcome, {rider.name}!\n\n"
    
    if has_active_ride:
        welcome_msg += (
            f"📍 You have an active ride (ID: {active_ride.id})\n"
            f"Status: {active_ride.status.value}\n\n"
            "Use the buttons below to check status or cancel."
        )
    else:
        welcome_msg += "Ready to request a ride? Tap the button below!"
    
    await update.message.reply_text(
        welcome_msg,
        reply_markup=get_rider_menu_keyboard(has_active_ride)
    )


# ==================== Ride Request Flow ====================

async def request_ride(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle ride request from rider.
    """
    user = update.effective_user
    
    # Check if rider already has an active ride
    active_ride = await get_active_ride_for_user(user.id)
    if active_ride:
        await update.message.reply_text(
            f"❌ You already have an active ride (ID: {active_ride.id})!\n\n"
            f"Status: {active_ride.status.value}\n\n"
            "Please complete or cancel your current ride before requesting a new one."
        )
        return
    
    # Generate random pickup location
    rider_lat, rider_lng = generate_random_location()
    
    # Create ride request
    ride = await create_ride(user.id, rider_lat, rider_lng)
    
    await update.message.reply_text(
        "🔍 <b>Searching for nearby drivers...</b>\n\n"
        f"📍 Pickup: {get_location_display(rider_lat, rider_lng)}",
        parse_mode="HTML"
    )
    
    # Find nearest driver
    result = await find_nearest_driver(rider_lat, rider_lng, ride.id)
    
    if not result:
        # No drivers available
        await update.message.reply_text(
            "😔 <b>No Drivers Available</b>\n\n"
            "Sorry, there are no drivers nearby at the moment.\n"
            "Please try again later!",
            reply_markup=get_rider_menu_keyboard(False),
            parse_mode="HTML"
        )
        
        # Cancel the ride
        await cancel_ride(ride.id)
        return
    
    driver, distance = result
    
    # Assign driver to ride atomically
    success = await assign_driver_to_ride(ride.id, driver.id, distance)
    
    if not success:
        await update.message.reply_text(
            "😔 <b>Driver No Longer Available</b>\n\n"
            "The driver was assigned to another ride. Please try again!",
            reply_markup=get_rider_menu_keyboard(False),
            parse_mode="HTML"
        )
        return
    
    # Notify rider
    await notify_driver_assigned(
        context.bot, user.id, driver.name,
        driver.vehicle_type.value, distance, ride.id
    )
    
    # Notify driver with confirmation buttons
    pickup_location = get_location_display(rider_lat, rider_lng)
    rider = await get_rider(user.id)
    
    await context.bot.send_message(
        chat_id=driver.id,
        text=(
            "🚕 <b>New Ride Request!</b>\n\n"
            f"👤 Rider: {rider.name}\n"
            f"📍 Pickup: {pickup_location}\n"
            f"🛣 Distance: {format_distance(distance)}\n\n"
            "Please confirm to accept this ride."
        ),
        reply_markup=get_ride_confirmation_keyboard(ride.id),
        parse_mode="HTML"
    )
    
    # Update rider menu
    await update.message.reply_text(
        "✅ <b>Driver Assigned!</b>\n\n"
        f"Waiting for driver confirmation...",
        reply_markup=get_rider_menu_keyboard(True),
        parse_mode="HTML"
    )
    
    log_with_context(logger, "INFO", 
                    f"Ride requested and driver {driver.name} assigned", 
                    ride_id=ride.id, user_id=user.id)


# ==================== Ride Status ====================

async def ride_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current ride status."""
    user = update.effective_user
    
    active_ride = await get_active_ride_for_user(user.id)
    
    if not active_ride:
        await update.message.reply_text(
            "❌ You don't have any active rides.",
            reply_markup=get_rider_menu_keyboard(False)
        )
        return
    
    # Build status message
    status_msg = (
        f"📍 <b>Ride Status</b>\n\n"
        f"🆔 Ride ID: {active_ride.id}\n"
        f"📊 Status: {active_ride.status.value}\n"
    )
    
    if active_ride.driver:
        status_msg += (
            f"\n👤 Driver: {active_ride.driver.name}\n"
            f"🚗 Vehicle: {active_ride.driver.vehicle_type.value}\n"
            f"⭐ Rating: {active_ride.driver.rating:.1f}\n"
            f"📏 Distance: {format_distance(active_ride.distance)}"
        )
    
    await update.message.reply_text(status_msg, parse_mode="HTML")


# ==================== Ride Cancellation ====================

async def cancel_ride_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle ride cancellation from button."""
    user = update.effective_user
    
    active_ride = await get_active_ride_for_user(user.id)
    
    if not active_ride:
        await update.message.reply_text(
            "❌ You don't have any active rides to cancel.",
            reply_markup=get_rider_menu_keyboard(False)
        )
        return
    
    # Can only cancel before ride starts
    if active_ride.status == RideStatus.ONGOING:
        await update.message.reply_text(
            "❌ Cannot cancel a ride that's already in progress!"
        )
        return
    
    # Cancel the ride
    await cancel_ride(active_ride.id)
    
    # Notify driver if assigned
    if active_ride.driver_id:
        await notify_ride_cancelled(context.bot, user.id, active_ride.id, active_ride.driver_id)
    
    await update.message.reply_text(
        "✅ <b>Ride Cancelled</b>\n\n"
        "Your ride has been cancelled successfully.",
        reply_markup=get_rider_menu_keyboard(False),
        parse_mode="HTML"
    )
    
    log_with_context(logger, "INFO", "Rider cancelled ride", 
                    ride_id=active_ride.id, user_id=user.id)


async def cancel_ride_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle ride cancellation from inline button."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    ride_id = int(query.data.split("_")[-1])
    
    ride = await get_ride(ride_id)
    
    if not ride or ride.rider_id != user.id:
        await query.edit_message_text("❌ Invalid ride.")
        return
    
    if ride.status == RideStatus.ONGOING:
        await query.answer("❌ Cannot cancel a ride in progress!", show_alert=True)
        return
    
    # Cancel the ride
    await cancel_ride(ride_id)
    
    # Notify driver if assigned
    if ride.driver_id:
        await notify_ride_cancelled(context.bot, user.id, ride_id, ride.driver_id)
    
    await query.edit_message_text(
        "✅ <b>Ride Cancelled</b>\n\n"
        "Your ride has been cancelled successfully.",
        parse_mode="HTML"
    )
    
    log_with_context(logger, "INFO", "Rider cancelled ride via callback", 
                    ride_id=ride_id, user_id=user.id)


# ==================== Rating System ====================

async def rate_ride_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle ride rating from inline keyboard."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Parse callback data: rate_{ride_id}_{rating}
    parts = query.data.split("_")
    ride_id = int(parts[1])
    rating = int(parts[2])
    
    # Get ride
    ride = await get_ride(ride_id)
    
    if not ride or ride.rider_id != user.id:
        await query.edit_message_text("❌ Invalid ride.")
        return
    
    if ride.status != RideStatus.COMPLETED:
        await query.answer("❌ Can only rate completed rides!", show_alert=True)
        return
    
    # Add rating
    await add_ride_rating(ride_id, rating)
    
    stars = "⭐" * rating
    await query.edit_message_text(
        f"✅ <b>Thank You!</b>\n\n"
        f"You rated this ride: {stars}\n\n"
        f"Your feedback helps us improve our service!",
        parse_mode="HTML"
    )
    
    log_with_context(logger, "INFO", f"Ride rated {rating} stars", 
                    ride_id=ride_id, user_id=user.id)


# ==================== Handler Setup ====================

def setup_rider_handlers(application):
    """Register rider-related handlers."""
    
    # Rider menu entry
    application.add_handler(MessageHandler(filters.Regex("^👤 Request a Ride$"), rider_start))
    
    # Ride actions
    application.add_handler(MessageHandler(filters.Regex("^🚕 Request Ride$"), request_ride))
    application.add_handler(MessageHandler(filters.Regex("^📍 Ride Status$"), ride_status))
    application.add_handler(MessageHandler(filters.Regex("^❌ Cancel Ride$"), cancel_ride_button))
    
    # Callbacks
    application.add_handler(CallbackQueryHandler(cancel_ride_callback, pattern="^cancel_ride_"))
    application.add_handler(CallbackQueryHandler(rate_ride_callback, pattern="^rate_"))
