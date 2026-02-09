"""
Driver handler for the Rideshare Bot.
Manages driver registration, availability, and ride acceptance.
"""
import re
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
    DRIVER_REGISTERING_LOCATION, DRIVER_IDLE, 
    DRIVER_CONFIRMING_RIDE, DRIVER_ONGOING_RIDE
)
from keyboards.reply import get_driver_menu_keyboard, get_vehicle_type_keyboard, get_location_keyboard
from keyboards.inline import get_start_ride_keyboard
from services.location import generate_random_location, get_google_maps_link
from services.notifications import notify_driver_assigned, notify_ride_started, notify_ride_completed
from utils.logger import logger, log_with_context
from utils.validators import validate_name
from utils.i18n import t, get_all_translations


# ==================== Driver Registration Flow ====================

async def driver_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start driver registration or show menu."""
    user = update.effective_user
    driver = await get_driver(user.id)
    lang = driver.language_code if driver else "en"
    
    if driver:
        await update.message.reply_text(
            t("welcome_driver", lang, 
              name=driver.name, 
              vehicle=driver.vehicle_type.value, 
              rating=f"{driver.rating:.1f}", 
              status="✅ AVAILABLE" if driver.available else "❌ OFFLINE"),
            reply_markup=get_driver_menu_keyboard(driver.available, lang),
            parse_mode="HTML"
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        t("driver_registration_prompt", lang),
        parse_mode="HTML"
    )
    return DRIVER_REGISTERING_NAME


async def driver_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle name input."""
    # ... (Keep registration mostly in English for simplicity, but use localized prompts)
    name = update.message.text.strip()
    is_valid, error = validate_name(name)
    if not is_valid:
        await update.message.reply_text(f"❌ {error}\n\nTry again:")
        return DRIVER_REGISTERING_NAME
    
    context.user_data['driver_name'] = name
    user = update.effective_user
    # Fetch lang from user metadata if possible, or default to English during registration
    # For now, let's keep it simple.
    await update.message.reply_text(
        t("select_vehicle", "en", name=name),
        reply_markup=get_vehicle_type_keyboard()
    )
    return DRIVER_REGISTERING_VEHICLE


async def driver_vehicle_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle vehicle selection."""
    text = update.message.text.strip()
    v_map = {"🚗 Car": VehicleType.CAR, "🏍 Motorcycle": VehicleType.MOTORCYCLE, 
             "🚐 Van": VehicleType.VAN, "🛵 Bike": VehicleType.BIKE}
    v_type = v_map.get(text)
    
    if not v_type:
        await update.message.reply_text("❌ Select from buttons:", reply_markup=get_vehicle_type_keyboard())
        return DRIVER_REGISTERING_VEHICLE
    
    context.user_data['driver_vehicle'] = v_type
    await update.message.reply_text(
        t("share_location_prompt", "en"),
        reply_markup=get_location_keyboard(),
        parse_mode="HTML"
    )
    return DRIVER_REGISTERING_LOCATION


async def driver_location_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle location and complete registration."""
    user = update.effective_user
    loc = update.message.location
    if not loc:
        await update.message.reply_text("❌ Use the button to share location:", reply_markup=get_location_keyboard())
        return DRIVER_REGISTERING_LOCATION
    
    name = context.user_data.get('driver_name')
    v_type = context.user_data.get('driver_vehicle')
    driver = await create_driver(user.id, name, v_type, loc.latitude, loc.longitude)
    lang = driver.language_code if driver else "en"
    
    await update.message.reply_text(
        t("registration_complete", lang),
        reply_markup=get_driver_menu_keyboard(False, lang),
        parse_mode="HTML"
    )
    context.user_data.clear()
    return ConversationHandler.END


# ==================== Driver Menu Actions ====================

async def go_available(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set driver as available."""
    user_id = update.effective_user.id
    driver = await get_driver(user_id)
    lang = driver.language_code if driver else "en"
    
    await set_driver_availability(user_id, True)
    await update.message.reply_text(
        "✅ <b>Status: AVAILABLE</b>\n\nYou will now receive nearby ride requests.",
        reply_markup=get_driver_menu_keyboard(True, lang),
        parse_mode="HTML"
    )


async def go_offline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set driver as offline."""
    user_id = update.effective_user.id
    driver = await get_driver(user_id)
    lang = driver.language_code if driver else "en"
    
    await set_driver_availability(user_id, False)
    await update.message.reply_text(
        "❌ <b>Status: OFFLINE</b>\n\nYou will no longer receive ride requests.",
        reply_markup=get_driver_menu_keyboard(False, lang),
        parse_mode="HTML"
    )


async def driver_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show driver statistics."""
    user_id = update.effective_user.id
    driver = await get_driver(user_id)
    lang = driver.language_code if driver else "en"
    
    if not driver:
        return
    
    stats_text = (
        f"📊 <b>Your Statistics</b>\n\n"
        f"⭐ Rating: {driver.rating:.2f}\n"
        f"🚕 Total Rides: {driver.total_rides}\n"
        f"📅 Joined: {driver.created_at.strftime('%Y-%m-%d')}"
    )
    await update.message.reply_text(stats_text, parse_mode="HTML")


# ==================== Ride Callbacks ====================

async def accept_ride_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the 'Accept Ride' inline button."""
    query = update.callback_query
    await query.answer()
    
    ride_id = int(query.data.split("_")[-1])
    ride = await get_ride(ride_id)
    
    if not ride or ride.status != RideStatus.REQUESTED:
        await query.edit_message_text("❌ This ride is no longer available.")
        return

    await update_ride_status(ride_id, RideStatus.ONGOING)
    await notify_ride_started(context.bot, ride.rider_id, update.effective_user.id, ride_id)
    
    map_link = get_google_maps_link(ride.rider_lat, ride.rider_lng)
    await query.edit_message_text(
        f"✅ <b>Accepted!</b>\n\n📍 Pickup: <a href='{map_link}'>View on Map</a>",
        reply_markup=get_start_ride_keyboard(ride_id),
        parse_mode="HTML",
        disable_web_page_preview=False
    )

async def decline_ride_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_driver_availability(update.effective_user.id, True)
    await update.callback_query.edit_message_text("❌ Declined.")

async def complete_ride_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ride_id = int(update.callback_query.data.split("_")[-1])
    ride = await get_ride(ride_id)
    await update_ride_status(ride_id, RideStatus.COMPLETED)
    await notify_ride_completed(context.bot, ride.rider_id, update.effective_user.id, ride_id)
    await update.callback_query.edit_message_text("✅ Ride Completed!")
    await set_driver_availability(update.effective_user.id, True)


# ==================== Regex Helpers ====================

def get_driver_start_regex() -> str:
    options = get_all_translations("main_menu_driver")
    return f"^({'|'.join(map(re.escape, options))})$"

def get_go_available_regex() -> str:
    options = get_all_translations("go_available")
    return f"^({'|'.join(map(re.escape, options))})$"

def get_go_offline_regex() -> str:
    options = get_all_translations("go_offline")
    return f"^({'|'.join(map(re.escape, options))})$"

def get_my_stats_regex() -> str:
    options = get_all_translations("my_stats")
    return f"^({'|'.join(map(re.escape, options))})$"


# ==================== Handler Setup ====================

def setup_driver_handlers(application):
    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(get_driver_start_regex()), driver_start)],
        states={
            DRIVER_REGISTERING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, driver_name_received)],
            DRIVER_REGISTERING_VEHICLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, driver_vehicle_received)],
            DRIVER_REGISTERING_LOCATION: [MessageHandler(filters.LOCATION, driver_location_received)],
        },
        fallbacks=[CommandHandler("start", driver_start)],
        allow_reentry=True
    )
    application.add_handler(conv)
    application.add_handler(MessageHandler(filters.Regex(get_go_available_regex()), go_available))
    application.add_handler(MessageHandler(filters.Regex(get_go_offline_regex()), go_offline))
    application.add_handler(MessageHandler(filters.Regex(get_my_stats_regex()), driver_stats))
    application.add_handler(CallbackQueryHandler(accept_ride_callback, pattern="^accept_ride_"))
    application.add_handler(CallbackQueryHandler(decline_ride_callback, pattern="^decline_ride_"))
    application.add_handler(CallbackQueryHandler(complete_ride_callback, pattern="^complete_ride_"))
