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
    DRIVER_REGISTERING_LOCATION, DRIVER_IDLE, 
    DRIVER_CONFIRMING_RIDE, DRIVER_ONGOING_RIDE
)
from keyboards.reply import get_driver_menu_keyboard, get_vehicle_type_keyboard, get_location_keyboard
from keyboards.inline import get_start_ride_keyboard
from services.location import generate_random_location, get_google_maps_link
from services.notifications import notify_driver_assigned, notify_ride_started, notify_ride_completed
from utils.logger import logger, log_with_context
from utils.validators import validate_name


# ==================== Driver Registration Flow ====================

async def driver_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start driver registration or show menu."""
    user = update.effective_user
    driver = await get_driver(user.id)
    
    if driver:
        await update.message.reply_text(
            f"👋 Welcome back, {driver.name}!\n\n"
            f"🚗 Vehicle: {driver.vehicle_type.value}\n"
            f"⭐ Rating: {driver.rating:.1f}\n"
            f"Status: {'✅ AVAILABLE' if driver.available else '❌ OFFLINE'}",
            reply_markup=get_driver_menu_keyboard(driver.available)
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "🚗 <b>Driver Registration</b>\n\n"
        "Please enter your full name:",
        parse_mode="HTML"
    )
    return DRIVER_REGISTERING_NAME


async def driver_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle name input."""
    name = update.message.text.strip()
    is_valid, error = validate_name(name)
    if not is_valid:
        await update.message.reply_text(f"❌ {error}\n\nTry again:")
        return DRIVER_REGISTERING_NAME
    
    context.user_data['driver_name'] = name
    await update.message.reply_text(
        f"Great, {name}! Select your vehicle:",
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
        "📍 <b>Where are you based?</b>\n\nShare your location to receive rides nearby.",
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
    await create_driver(user.id, name, v_type, loc.latitude, loc.longitude)
    
    await update.message.reply_text(
        "✅ <b>Registration Complete!</b>",
        reply_markup=get_driver_menu_keyboard(False),
        parse_mode="HTML"
    )
    context.user_data.clear()
    return ConversationHandler.END


# ==================== Actions ====================

async def go_available(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_driver_availability(update.effective_user.id, True)
    await update.message.reply_text("✅ Available!", reply_markup=get_driver_menu_keyboard(True))

async def go_offline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_driver_availability(update.effective_user.id, False)
    await update.message.reply_text("❌ Offline", reply_markup=get_driver_menu_keyboard(False))

async def driver_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    driver = await get_driver(update.effective_user.id)
    await update.message.reply_text(f"📊 <b>Stats</b>\nRating: {driver.rating:.1f}\nRides: {driver.total_rides}", parse_mode="HTML")


# ==================== Ride Flow ====================

async def accept_ride_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    ride_id = int(query.data.split("_")[-1])
    ride = await get_ride(ride_id)
    
    if not ride or ride.status != RideStatus.ASSIGNED:
        await query.edit_message_text("❌ Ride no longer available.")
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


def setup_driver_handlers(application):
    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🚗 I'm a Driver$"), driver_start)],
        states={
            DRIVER_REGISTERING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, driver_name_received)],
            DRIVER_REGISTERING_VEHICLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, driver_vehicle_received)],
            DRIVER_REGISTERING_LOCATION: [MessageHandler(filters.LOCATION, driver_location_received)],
        },
        fallbacks=[CommandHandler("start", driver_start)],
        allow_reentry=True
    )
    application.add_handler(conv)
    application.add_handler(MessageHandler(filters.Regex("^✅ Go Available$"), go_available))
    application.add_handler(MessageHandler(filters.Regex("^❌ Go Offline$"), go_offline))
    application.add_handler(MessageHandler(filters.Regex("^📊 My Stats$"), driver_stats))
    application.add_handler(CallbackQueryHandler(accept_ride_callback, pattern="^accept_ride_"))
    application.add_handler(CallbackQueryHandler(decline_ride_callback, pattern="^decline_ride_"))
    application.add_handler(CallbackQueryHandler(complete_ride_callback, pattern="^complete_ride_"))
