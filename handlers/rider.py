"""
Rider handler for the Rideshare Bot.
Manages ride requests, status tracking, cancellations, and ratings.
"""
import re
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
from keyboards.reply import get_rider_menu_keyboard, get_location_keyboard
from keyboards.inline import get_rating_keyboard, get_ride_confirmation_keyboard
from services.location import generate_random_location, format_distance, get_location_display
from services.matching import find_nearest_driver
from services.notifications import notify_driver_assigned, notify_rider_assigned, notify_ride_cancelled
from utils.logger import logger, log_with_context
from utils.validators import validate_name
from utils.i18n import t, get_all_translations


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
    
    lang = rider.language_code
    
    # Check for active ride
    active_ride = await get_active_ride_for_user(user.id)
    has_active_ride = active_ride is not None
    
    welcome_msg = t("welcome_rider", lang, name=rider.name)
    
    await update.message.reply_text(
        welcome_msg,
        reply_markup=get_rider_menu_keyboard(has_active_ride, lang)
    )


# ==================== Ride Request Flow (Conversation) ====================

WAITING_LOCATION = 1

async def request_ride_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle ride request from rider - Ask for location.
    """
    user = update.effective_user
    rider = await get_rider(user.id)
    lang = rider.language_code if rider else "en"
    
    # Check if rider already has an active ride
    active_ride = await get_active_ride_for_user(user.id)
    if active_ride:
        await update.message.reply_text(
            f"❌ You already have an active ride (ID: {active_ride.id})!"
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        t("select_location", lang),
        reply_markup=get_location_keyboard(lang),
        parse_mode="HTML"
    )
    return WAITING_LOCATION


async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Process the shared location and find a driver.
    """
    user = update.effective_user
    rider = await get_rider(user.id)
    lang = rider.language_code if rider else "en"
    location = update.message.location
    
    if not location:
        await update.message.reply_text(
            "❌ Please use the button below to share your location.",
            reply_markup=get_location_keyboard(lang)
        )
        return WAITING_LOCATION

    # Create ride
    ride = await create_ride(user.id, location.latitude, location.longitude)
    
    await update.message.reply_text(
        t("searching_driver", lang, location=get_location_display(location.latitude, location.longitude)),
        reply_markup=get_rider_menu_keyboard(True, lang),
        parse_mode="HTML"
    )
    
    # Matching Logic
    driver, distance = await find_nearest_driver(location.latitude, location.longitude)
    
    if not driver:
        await update.message.reply_text(t("no_drivers", lang), parse_mode="HTML")
        # In a real app, we'd keep searching or queue it
        return ConversationHandler.END
        
    # Notify rider and driver
    await assign_driver_to_ride(ride.id, driver.id, distance)
    await notify_rider_assigned(context.bot, user.id, driver, distance)
    await notify_driver_assigned(context.bot, driver.id, user, location.latitude, location.longitude, ride.id)
    
    return ConversationHandler.END


async def cancel_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel ride request during conversation."""
    user_id = update.effective_user.id
    rider = await get_rider(user_id)
    lang = rider.language_code if rider else "en"
    
    await update.message.reply_text(
        "❌ Request cancelled.",
        reply_markup=get_rider_menu_keyboard(False, lang)
    )
    return ConversationHandler.END


# ==================== Ride Management Buttons ====================

async def ride_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show status of active ride."""
    user_id = update.effective_user.id
    ride = await get_active_ride_for_user(user_id)
    
    if not ride:
        await update.message.reply_text("❌ No active ride.")
        return

    status_text = (
        f"🚕 <b>Ride Status (ID: {ride.id})</b>\n\n"
        f"Status: {ride.status.value}\n"
    )
    if ride.driver:
        status_text += f"Driver: {ride.driver.name}\nVehicle: {ride.driver.vehicle_type.value}\n"
        
    await update.message.reply_text(status_text, parse_mode="HTML")


async def cancel_ride_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the 'Cancel Ride' button."""
    user_id = update.effective_user.id
    ride = await get_active_ride_for_user(user_id)
    
    if not ride:
        await update.message.reply_text("❌ No active ride to cancel.")
        return

    await update.message.reply_text(
        f"Are you sure you want to cancel ride {ride.id}?",
        reply_markup=get_ride_confirmation_keyboard(ride.id)
    )


async def cancel_ride_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cancellation confirmation from inline keyboard."""
    query = update.callback_query
    await query.answer()
    
    ride_id = int(query.data.split("_")[-1])
    ride = await get_ride(ride_id)
    
    if await cancel_ride(ride_id):
        await query.edit_message_text("❌ Ride cancelled.")
        if ride and ride.driver_id:
            await notify_ride_cancelled(context.bot, ride.driver_id, ride_id)
    else:
        await query.edit_message_text("❌ Could not cancel ride.")


async def rate_ride_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle rating callback."""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("_")
    rating = int(data[1])
    ride_id = int(data[2])
    
    await add_ride_rating(ride_id, rating)
    
    stars = "⭐" * rating
    await query.edit_message_text(
        f"✅ <b>Thank You!</b>\n\n"
        f"You rated this ride: {stars}\n\n"
        f"Your feedback helps us improve our service!",
        parse_mode="HTML"
    )


# ==================== Regex Helpers ====================

def get_rider_start_regex() -> str:
    options = get_all_translations("main_menu_rider")
    return f"^({'|'.join(map(re.escape, options))})$"

def get_request_ride_regex() -> str:
    options = get_all_translations("request_ride")
    return f"^({'|'.join(map(re.escape, options))})$"

def get_cancel_btn_regex() -> str:
    options = get_all_translations("cancel_btn")
    return f"^({'|'.join(map(re.escape, options))})$"


# ==================== Handler Setup ====================

def setup_rider_handlers(application):
    """Register rider-related handlers."""
    # Rider menu entry
    application.add_handler(MessageHandler(filters.Regex(get_rider_start_regex()), rider_start))
    
    # Ride Request Conversation
    ride_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(get_request_ride_regex()), request_ride_start)],
        states={
            WAITING_LOCATION: [
                MessageHandler(filters.LOCATION, handle_location),
                MessageHandler(filters.Regex(get_cancel_btn_regex()), cancel_request)
            ]
        },
        fallbacks=[MessageHandler(filters.Regex("^🏠 Main Menu$"), cancel_request)], # Add regex if needed
        allow_reentry=True
    )
    application.add_handler(ride_conv)
    
    # Ride actions
    application.add_handler(MessageHandler(filters.Regex("^📍 Ride Status$"), ride_status))
    application.add_handler(MessageHandler(filters.Regex("^❌ Cancel Ride$"), cancel_ride_button))
    
    # Callbacks
    application.add_handler(CallbackQueryHandler(cancel_ride_callback, pattern="^cancel_ride_"))
    application.add_handler(CallbackQueryHandler(rate_ride_callback, pattern="^rate_"))
