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
from enums import VehicleType, RideStatus, DriverStatus
from fsm.driver_states import (
    DRIVER_REGISTERING_NAME, DRIVER_REGISTERING_PHONE, DRIVER_REGISTERING_VEHICLE,
    DRIVER_REGISTERING_PLATE, DRIVER_UPLOADING_LICENSE,
    DRIVER_REGISTERING_LOCATION, DRIVER_IDLE, 
    DRIVER_CONFIRMING_RIDE, DRIVER_ONGOING_RIDE
)
from keyboards.reply import get_driver_menu_keyboard, get_vehicle_type_keyboard, get_location_keyboard, get_phone_keyboard
from keyboards.inline import get_ride_action_keyboard, get_start_ride_keyboard
from services.location import get_google_maps_link, get_google_maps_route_link
from services.notifications import notify_ride_started, notify_ride_completed
from utils.logger import logger, log_with_context
from utils.validators import validate_name, validate_phone_number, normalize_phone_number
from utils.i18n import t, get_all_translations


# ==================== Driver Registration Flow ====================

async def driver_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start driver registration or show menu."""
    user = update.effective_user
    driver = await get_driver(user.id)
    lang = driver.language_code if driver else "en"
    
    if driver:
        # Check verification status
        status_display = "✅ AVAILABLE" if driver.available else "❌ OFFLINE"
        if hasattr(driver, 'status') and driver.status:
            if driver.status == DriverStatus.PENDING:
                status_display = "⏳ PENDING REVIEW"
            elif driver.status == DriverStatus.SUSPENDED:
                status_display = "🚫 SUSPENDED"
            elif driver.status == DriverStatus.REJECTED:
                status_display = "❌ REJECTED"
        
        await update.message.reply_text(
            t("welcome_driver", lang, 
              name=driver.name, 
              vehicle=driver.vehicle_type.value, 
              rating=f"{driver.rating:.1f}", 
              status=status_display),
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
    
    # Prompt for phone number
    await update.message.reply_text(
        t("driver_phone_prompt", "en"),
        reply_markup=get_phone_keyboard("en"),
        parse_mode="HTML"
    )
    return DRIVER_REGISTERING_PHONE

async def driver_phone_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle phone number input."""
    name = context.user_data.get('driver_name', 'Driver')
    
    phone = ""
    if update.message.contact:
        phone = update.message.contact.phone_number
    elif update.message.text:
        text = update.message.text.strip()
        skip_options = get_all_translations("skip_btn")
        if text in skip_options:
            phone = None
        else:
            phone = text
            
    if phone:
        is_valid, error = validate_phone_number(phone)
        if not is_valid:
            await update.message.reply_text(f"❌ {error}\n\nTry again:", reply_markup=get_phone_keyboard("en"))
            return DRIVER_REGISTERING_PHONE
        phone = normalize_phone_number(phone)
        
    context.user_data['driver_phone'] = phone
    
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
        t("plate_prompt", "en"),
        parse_mode="HTML"
    )
    return DRIVER_REGISTERING_PLATE


async def driver_plate_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plate number input."""
    plate = update.message.text.strip().upper()
    if len(plate) < 3 or len(plate) > 20:
        await update.message.reply_text("❌ Invalid plate number. Please try again:")
        return DRIVER_REGISTERING_PLATE
    
    context.user_data['driver_plate'] = plate
    await update.message.reply_text(
        t("license_prompt", "en"),
        parse_mode="HTML"
    )
    return DRIVER_UPLOADING_LICENSE


async def driver_license_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle license photo upload."""
    if update.message.photo:
        # Get the highest-resolution photo
        file_id = update.message.photo[-1].file_id
        context.user_data['driver_license'] = file_id
    elif update.message.text:
        skip_options = get_all_translations("skip_btn")
        if update.message.text.strip() in skip_options:
            context.user_data['driver_license'] = None
        else:
            await update.message.reply_text("❌ Please send a photo of your license, or tap Skip.")
            return DRIVER_UPLOADING_LICENSE
    else:
        await update.message.reply_text("❌ Please send a photo of your license.")
        return DRIVER_UPLOADING_LICENSE
    
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
    phone = context.user_data.get('driver_phone')
    v_type = context.user_data.get('driver_vehicle')
    plate = context.user_data.get('driver_plate')
    license_id = context.user_data.get('driver_license')
    
    driver = await create_driver(
        user_id=user.id, 
        name=name, 
        vehicle_type=v_type, 
        latitude=loc.latitude, 
        longitude=loc.longitude,
        phone_number=phone,
        plate_number=plate,
        license_file_id=license_id
    )
    lang = driver.language_code if driver else "en"
    
    # New drivers are PENDING by default
    await update.message.reply_text(
        t("pending_review", lang),
        reply_markup=get_driver_menu_keyboard(False, lang),
        parse_mode="HTML"
    )
    context.user_data.clear()
    return ConversationHandler.END


# ==================== Driver Menu Actions ====================

async def go_available(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set driver as available (only if APPROVED)."""
    user_id = update.effective_user.id
    driver = await get_driver(user_id)
    lang = driver.language_code if driver else "en"
    
    # Block non-approved drivers
    if hasattr(driver, 'status') and driver.status and driver.status != DriverStatus.APPROVED:
        await update.message.reply_text(
            t("driver_pending_error", lang),
            parse_mode="HTML"
        )
        return
    
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
        
    from database.db import get_driver_today_rides, get_driver_completed_rides_count
    today_rides = await get_driver_today_rides(user_id)
    total_rides = await get_driver_completed_rides_count(user_id)
    
    # Simulated earnings based on completed rides for demo purposes
    today_earnings = today_rides * 125.0  # Average 125 ETB per ride
    total_earnings = total_rides * 125.0
    
    stats_text = t(
        "driver_earnings_stats", lang,
        today_rides=today_rides,
        today_earnings=f"{today_earnings:.2f}",
        total_rides=total_rides,
        total_earnings=f"{total_earnings:.2f}",
        rating=f"{driver.rating:.1f}",
        joined=driver.created_at.strftime('%Y-%m-%d')
    )
    await update.message.reply_text(stats_text, parse_mode="HTML")


async def driver_wallet_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show driver's simulated wallet balance."""
    user_id = update.effective_user.id
    driver = await get_driver(user_id)
    if not driver: return
    
    balance = getattr(driver, 'wallet_balance', 0.0)
    text = (
        f"💳 <b>Wallet & Earnings</b>\n\n"
        f"💰 <b>Current Balance:</b> {balance:.2f} ETB\n\n"
        f"<i>(This is a simulated wallet for demo purposes. Earnings from completed rides are automatically added here.)</i>"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def driver_update_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle location updates from drivers when they are available."""
    user = update.effective_user
    driver = await get_driver(user.id)
    
    # We only care if the driver exists and is available (or at least approved)
    if not driver or driver.status != DriverStatus.APPROVED:
        return
        
    location = update.message.location
    if not location:
        return
        
    from database.db import update_driver_location
    success = await update_driver_location(user.id, location.latitude, location.longitude)
    
    if success:
        lang = driver.language_code
        # Delete their location message or send a brief toast to avoid clutter
        try:
            msg = await update.message.reply_text(
                "📍 Location updated successfully.",
                disable_notification=True
            )
            # Optionally, we could schedule this message to be deleted after 3 seconds, 
            # but for simplicity, we'll leave it as a confirmation.
        except Exception:
            pass


# ==================== Ride Callbacks ====================

async def accept_ride_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the 'Accept Ride' inline button."""
    query = update.callback_query
    await query.answer()
    
    ride_id = int(query.data.split("_")[-1])
    ride = await get_ride(ride_id)
    
    if not ride or ride.driver_id != update.effective_user.id or ride.status != RideStatus.ASSIGNED:
        await query.edit_message_text("❌ This ride is no longer available.")
        return

    # If the ride has a destination, give the driver a full routing link
    if ride.dest_lat and ride.dest_lng:
        map_link = get_google_maps_route_link(ride.rider_lat, ride.rider_lng, ride.dest_lat, ride.dest_lng)
        map_btn_text = "View Route on Map"
    else:
        map_link = get_google_maps_link(ride.rider_lat, ride.rider_lng)
        map_btn_text = "View Pickup on Map"
        
    await query.edit_message_text(
        f"✅ <b>Accepted!</b>\n\n📍 <a href='{map_link}'>{map_btn_text}</a>\n\nTap Start Ride when the rider is picked up.",
        reply_markup=get_start_ride_keyboard(ride_id),
        parse_mode="HTML",
        disable_web_page_preview=False
    )

async def decline_ride_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ride_id = int(query.data.split("_")[-1])
    ride = await get_ride(ride_id)
    if ride and ride.driver_id == update.effective_user.id and ride.status == RideStatus.ASSIGNED:
        await update_ride_status(ride_id, RideStatus.CANCELLED)
    await set_driver_availability(update.effective_user.id, True)
    await query.edit_message_text("❌ Declined.")


async def start_ride_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    ride_id = int(query.data.split("_")[-1])
    ride = await get_ride(ride_id)

    if not ride or ride.driver_id != update.effective_user.id or ride.status != RideStatus.ASSIGNED:
        await query.edit_message_text("❌ This ride cannot be started.")
        return

    await update_ride_status(ride_id, RideStatus.ONGOING)
    await notify_ride_started(context.bot, ride.rider_id, update.effective_user.id, ride_id)
    await query.edit_message_text(
        "🚗 <b>Ride Started!</b>\n\nComplete the ride when you arrive.",
        reply_markup=get_ride_action_keyboard(ride_id, is_driver=True),
        parse_mode="HTML"
    )

async def complete_ride_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ride_id = int(query.data.split("_")[-1])
    ride = await get_ride(ride_id)

    if not ride or ride.driver_id != update.effective_user.id or ride.status != RideStatus.ONGOING:
        await query.edit_message_text("❌ This ride cannot be completed.")
        return

    # Phase 4 Payment Flow
    await update_ride_status(ride_id, RideStatus.AWAITING_PAYMENT)
    
    fare = ride.estimated_fare or 150.0
    
    # Notify rider to pay
    from keyboards.inline import get_payment_keyboard
    rider_msg = (
        f"🏁 <b>You have arrived!</b>\n\n"
        f"💵 <b>Total Fare:</b> {fare} ETB\n\n"
        f"Please select your payment method to complete the ride:"
    )
    try:
        await context.bot.send_message(
            chat_id=ride.rider_id, 
            text=rider_msg, 
            reply_markup=get_payment_keyboard(ride_id, fare),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed to send payment request to rider {ride.rider_id}: {e}")

    await query.edit_message_text("⏳ <b>Waiting for Payment...</b>\n\nThe rider has been prompted to pay the fare.", parse_mode="HTML")


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
            DRIVER_REGISTERING_PHONE: [MessageHandler(filters.CONTACT | filters.TEXT & ~filters.COMMAND, driver_phone_received)],
            DRIVER_REGISTERING_VEHICLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, driver_vehicle_received)],
            DRIVER_REGISTERING_PLATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, driver_plate_received)],
            DRIVER_UPLOADING_LICENSE: [
                MessageHandler(filters.PHOTO, driver_license_received),
                MessageHandler(filters.TEXT & ~filters.COMMAND, driver_license_received)
            ],
            DRIVER_REGISTERING_LOCATION: [MessageHandler(filters.LOCATION, driver_location_received)],
        },
        fallbacks=[CommandHandler("start", driver_start)],
        allow_reentry=True
    )
    application.add_handler(conv)
    application.add_handler(MessageHandler(filters.Regex(get_go_available_regex()), go_available))
    application.add_handler(MessageHandler(filters.Regex(get_go_offline_regex()), go_offline))
    application.add_handler(MessageHandler(filters.Regex(get_my_stats_regex()), driver_stats))
    application.add_handler(MessageHandler(filters.Regex("^💳 Wallet"), driver_wallet_menu))
    
    # Handle live location updates (or static location pins) when driver is not in conversation
    application.add_handler(MessageHandler(filters.LOCATION, driver_update_location))
    
    application.add_handler(CallbackQueryHandler(accept_ride_callback, pattern="^accept_ride_"))
    application.add_handler(CallbackQueryHandler(decline_ride_callback, pattern="^decline_ride_"))
    application.add_handler(CallbackQueryHandler(start_ride_callback, pattern="^start_ride_"))
    application.add_handler(CallbackQueryHandler(complete_ride_callback, pattern="^complete_ride_"))
