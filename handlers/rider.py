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
    cancel_ride, add_ride_rating, get_ride, assign_driver_to_ride,
    get_saved_locations, add_saved_location
)
from enums import RideStatus
from fsm.rider_states import (
    RIDER_IDLE, RIDER_REQUESTING_RIDE, RIDER_WAITING_DRIVER,
    RIDER_RIDE_ASSIGNED, RIDER_ONGOING_RIDE, RIDER_RATING_DRIVER,
    RIDER_REGISTERING_PHONE, RIDER_MANAGING_FAVORITES, RIDER_SAVING_LOCATION_NAME,
    RIDER_WAITING_DESTINATION, RIDER_CONFIRMING_ROUTE
)
from keyboards.reply import get_rider_menu_keyboard, get_location_keyboard, get_phone_keyboard, get_main_menu_keyboard, get_favorites_keyboard
from keyboards.inline import get_cancel_ride_keyboard
from services.location import get_location_display
from services.matching import find_nearest_driver
from services.notifications import notify_driver_assigned, notify_rider_assigned, notify_ride_cancelled
from utils.logger import logger, log_with_context
from utils.i18n import t, get_all_translations
from utils.validators import validate_phone_number, normalize_phone_number
import asyncio


# ==================== Rider Registration & Menu ====================

async def rider_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Start rider flow - check registration and show menu.
    """
    user = update.effective_user
    rider = await get_rider(user.id)
    
    if not rider or not rider.phone_number:
        # Create rider without phone number first
        if not rider:
            name = user.first_name or "Rider"
            rider = await create_rider(user.id, name)
            
        lang = rider.language_code
        await update.message.reply_text(
            t("driver_phone_prompt", lang),  # We can reuse this prompt or create a generic one
            reply_markup=get_phone_keyboard(lang),
            parse_mode="HTML"
        )
        return RIDER_REGISTERING_PHONE
    
    lang = rider.language_code
    
    # Check for active ride
    active_ride = await get_active_ride_for_user(user.id)
    has_active_ride = active_ride is not None
    
    welcome_msg = t("welcome_rider", lang, name=rider.name)
    
    await update.message.reply_text(
        welcome_msg,
        reply_markup=get_rider_menu_keyboard(has_active_ride, lang)
    )
    return ConversationHandler.END


async def rider_phone_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle phone number input."""
    user = update.effective_user
    rider = await get_rider(user.id)
    lang = rider.language_code if rider else "en"
    
    phone = ""
    if update.message.contact:
        phone = update.message.contact.phone_number
    elif update.message.text:
        text = update.message.text.strip()
        # Handle skip
        skip_options = get_all_translations("skip_btn")
        if text in skip_options:
            await update.message.reply_text(
                "ℹ️ Phone number skipped. You can still request rides.",
                reply_markup=get_rider_menu_keyboard(False, lang)
            )
            return ConversationHandler.END
            
        phone = text
        
    is_valid, error = validate_phone_number(phone)
    if not is_valid:
        await update.message.reply_text(f"❌ {error}\n\nTry again:", reply_markup=get_phone_keyboard(lang))
        return RIDER_REGISTERING_PHONE
        
    phone = normalize_phone_number(phone)
    
    # Update rider
    await create_rider(user.id, rider.name, phone)
    
    await update.message.reply_text(
        t("phone_shared", lang, phone=phone),
        parse_mode="HTML"
    )
    await update.message.reply_text(
        t("welcome_rider", lang, name=rider.name),
        reply_markup=get_rider_menu_keyboard(False, lang)
    )
    return ConversationHandler.END


# ==================== Ride Request Flow (Conversation) ====================

WAITING_LOCATION = 1

async def request_ride_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle ride request from rider - Ask for pickup location.
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
        "📍 Please share your <b>Pickup Location</b> using the button below:",
        reply_markup=get_location_keyboard(lang),
        parse_mode="HTML"
    )
    return WAITING_LOCATION


async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Process the shared pickup location and ask for destination.
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

    context.user_data['pickup_lat'] = location.latitude
    context.user_data['pickup_lng'] = location.longitude
    
    await update.message.reply_text(
        "🏁 Great! Now please share your <b>Destination Location</b>:",
        reply_markup=get_location_keyboard(lang),
        parse_mode="HTML"
    )
    return RIDER_WAITING_DESTINATION


async def handle_destination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Process the destination location, calculate route summary, and ask for confirmation.
    """
    user = update.effective_user
    rider = await get_rider(user.id)
    lang = rider.language_code if rider else "en"
    location = update.message.location
    
    if not location:
        await update.message.reply_text(
            "❌ Please use the button below to share your destination.",
            reply_markup=get_location_keyboard(lang)
        )
        return RIDER_WAITING_DESTINATION

    pickup_lat = context.user_data.get('pickup_lat')
    pickup_lng = context.user_data.get('pickup_lng')
    
    if not pickup_lat or not pickup_lng:
        await update.message.reply_text("❌ Session expired. Please request a ride again.")
        return ConversationHandler.END
        
    dest_lat = location.latitude
    dest_lng = location.longitude
    
    context.user_data['dest_lat'] = dest_lat
    context.user_data['dest_lng'] = dest_lng
    
    from services.location import calculate_distance, get_route_static_map_url
    from services.pricing import calculate_fare, calculate_eta
    
    distance = calculate_distance(pickup_lat, pickup_lng, dest_lat, dest_lng)
    fare = calculate_fare(distance)
    eta = calculate_eta(distance)
    
    context.user_data['estimated_fare'] = fare
    context.user_data['estimated_duration'] = eta
    
    map_url = get_route_static_map_url(pickup_lat, pickup_lng, dest_lat, dest_lng)
    
    from keyboards.inline import get_route_confirmation_keyboard
    
    caption = (
        f"🗺️ <b>Route Summary</b>\n\n"
        f"📏 <b>Distance:</b> {distance} km\n"
        f"⏱️ <b>Est. Duration:</b> {eta} min\n"
        f"💵 <b>Est. Fare:</b> {fare} ETB\n\n"
        f"Do you want to confirm this ride?"
    )
    
    await update.message.reply_photo(
        photo=map_url,
        caption=caption,
        reply_markup=get_route_confirmation_keyboard(lang),
        parse_mode="HTML"
    )
    return RIDER_CONFIRMING_ROUTE


async def confirm_route_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle route confirmation, create ride, and find driver.
    """
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    rider = await get_rider(user.id)
    lang = rider.language_code if rider else "en"
    
    if query.data == "cancel_route":
        await query.edit_message_caption("❌ Ride request cancelled.")
        context.user_data.clear()
        return ConversationHandler.END
        
    pickup_lat = context.user_data.get('pickup_lat')
    pickup_lng = context.user_data.get('pickup_lng')
    dest_lat = context.user_data.get('dest_lat')
    dest_lng = context.user_data.get('dest_lng')
    fare = context.user_data.get('estimated_fare')
    eta = context.user_data.get('estimated_duration')
    
    if not pickup_lat:
        await query.edit_message_caption("❌ Session expired. Please request a ride again.")
        return ConversationHandler.END
        
    # Searching animation
    await query.edit_message_caption("🔍 Searching for nearby drivers...", parse_mode="HTML")
    
    # Create ride
    ride = await create_ride(
        user.id, pickup_lat, pickup_lng, 
        dest_lat, dest_lng, fare, eta
    )
    
    # Matching Logic
    match = await find_nearest_driver(pickup_lat, pickup_lng, ride.id)
    
    if not match:
        await query.edit_message_caption(t("no_drivers", lang), parse_mode="HTML")
        await cancel_ride(ride.id)
        # In a real app, we'd keep searching or queue it
        return ConversationHandler.END

    driver, distance = match
        
    # Notify rider and driver
    assigned = await assign_driver_to_ride(ride.id, driver.id, distance)
    if not assigned:
        await query.edit_message_caption("❌ Error assigning driver. Please try again.")
        await cancel_ride(ride.id)
        return ConversationHandler.END

    await notify_driver_assigned(
        context.bot,
        user.id,
        driver.name,
        driver.vehicle_type.value,
        distance,
        ride.id
    )
    await notify_rider_assigned(
        context.bot,
        driver.id,
        user.first_name or "Rider",
        get_location_display(pickup_lat, pickup_lng),
        distance,
        ride.id
    )
    
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
        reply_markup=get_cancel_ride_keyboard(ride.id)
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
    ride_id = int(data[1])
    rating = int(data[2])
    
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

def get_favorites_regex() -> str:
    options = get_all_translations("favorites_menu")
    return f"^({'|'.join(map(re.escape, options))})$"

def get_back_regex() -> str:
    options = get_all_translations("back_btn")
    return f"^({'|'.join(map(re.escape, options))})$"


# ==================== Favorites Flow ====================

async def favorites_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show saved locations menu."""
    user = update.effective_user
    rider = await get_rider(user.id)
    if not rider:
        await update.message.reply_text("⚠️ Please register first.")
        return ConversationHandler.END
    
    lang = rider.language_code
    locations = await get_saved_locations(user.id)
    
    if not locations:
        await update.message.reply_text(
            "⭐ <b>Saved Locations</b>\n\nYou have no saved locations yet.\nTap below to save your current location, or share a location to save it.",
            reply_markup=get_favorites_keyboard([], lang),
            parse_mode="HTML"
        )
    else:
        loc_list = "\n".join([f"📍 {loc.name}" for loc in locations])
        await update.message.reply_text(
            f"⭐ <b>Saved Locations</b>\n\n{loc_list}\n\nTap a location to request a ride from there, or save a new one.",
            reply_markup=get_favorites_keyboard(locations, lang),
            parse_mode="HTML"
        )
    return RIDER_MANAGING_FAVORITES


async def save_location_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt user to share location to save."""
    rider = await get_rider(update.effective_user.id)
    lang = rider.language_code if rider else "en"
    await update.message.reply_text(
        "📍 Please share your location to save it.",
        reply_markup=get_location_keyboard(lang)
    )
    return RIDER_MANAGING_FAVORITES


async def save_location_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive location and ask for a name."""
    loc = update.message.location
    context.user_data['save_lat'] = loc.latitude
    context.user_data['save_lng'] = loc.longitude
    
    rider = await get_rider(update.effective_user.id)
    lang = rider.language_code if rider else "en"
    
    await update.message.reply_text(
        t("save_location_prompt", lang),
        parse_mode="HTML"
    )
    return RIDER_SAVING_LOCATION_NAME


async def save_location_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save the location with the given name."""
    name = update.message.text.strip()
    if len(name) < 1 or len(name) > 50:
        await update.message.reply_text("❌ Name must be between 1 and 50 characters. Try again:")
        return RIDER_SAVING_LOCATION_NAME
    
    lat = context.user_data.get('save_lat')
    lng = context.user_data.get('save_lng')
    
    if not lat or not lng:
        await update.message.reply_text("❌ Location data lost. Please try again.")
        return ConversationHandler.END
    
    rider = await get_rider(update.effective_user.id)
    lang = rider.language_code if rider else "en"
    
    await add_saved_location(update.effective_user.id, name, lat, lng)
    
    await update.message.reply_text(
        t("location_saved", lang, name=name),
        reply_markup=get_rider_menu_keyboard(False, lang),
        parse_mode="HTML"
    )
    context.user_data.pop('save_lat', None)
    context.user_data.pop('save_lng', None)
    return ConversationHandler.END


async def use_saved_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Use a saved location to start a ride request."""
    text = update.message.text.strip()
    # Extract location name (remove the 📍 prefix)
    loc_name = text.replace("📍 ", "").strip()
    
    rider = await get_rider(update.effective_user.id)
    if not rider:
        return ConversationHandler.END
    
    lang = rider.language_code
    locations = await get_saved_locations(update.effective_user.id)
    
    matched = None
    for loc in locations:
        if loc.name == loc_name:
            matched = loc
            break
    
    if not matched:
        await update.message.reply_text("❌ Location not found.")
        return RIDER_MANAGING_FAVORITES
    
    # Check if rider already has an active ride
    from database.db import get_active_ride_for_user
    active_ride = await get_active_ride_for_user(update.effective_user.id)
    if active_ride:
        await update.message.reply_text(
            f"❌ You already have an active ride (ID: {active_ride.id})!"
        )
        return ConversationHandler.END
    
    # Use saved location as pickup
    context.user_data['pickup_lat'] = matched.latitude
    context.user_data['pickup_lng'] = matched.longitude
    
    await update.message.reply_text(
        f"📍 Using <b>{loc_name}</b> as pickup.\n\n🏁 Now please share your <b>Destination Location</b>:",
        reply_markup=get_location_keyboard(lang),
        parse_mode="HTML"
    )
    
    # Since we are modifying fav_conv, I should update the handler setup to support the full ride flow from favorites.
    return RIDER_WAITING_DESTINATION


# ==================== Wallet Operations ====================

async def rider_wallet_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show rider's simulated wallet balance."""
    user_id = update.effective_user.id
    rider = await get_rider(user_id)
    if not rider: return
    
    balance = getattr(rider, 'wallet_balance', 0.0)
    text = (
        f"💳 <b>Wallet & Payments</b>\n\n"
        f"💰 <b>Current Balance:</b> {balance:.2f} ETB\n\n"
        f"<i>(This is a simulated wallet. You can use it to pay for rides. In a real app, you would add funds here via a payment gateway like Chapa.)</i>"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def process_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle rider payment selection."""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("_")
    payment_method = data[1] # cash, card, wallet
    ride_id = int(data[2])
    
    from database.db import get_ride, update_ride_status, update_wallet_balance
    from enums import RideStatus
    
    ride = await get_ride(ride_id)
    if not ride or ride.status != RideStatus.AWAITING_PAYMENT:
        await query.edit_message_text("❌ This payment is no longer valid or already processed.")
        return
        
    fare = ride.estimated_fare or 150.0
    rider_id = ride.rider_id
    driver_id = ride.driver_id
    
    if payment_method == "wallet":
        # Deduct from rider
        rider = await get_rider(rider_id)
        if getattr(rider, 'wallet_balance', 0.0) < fare:
            await query.answer("❌ Insufficient wallet balance!", show_alert=True)
            return
        await update_wallet_balance(rider_id, -fare, is_driver=False)
        
    if payment_method in ["wallet", "card"]:
        # Credit to driver
        await update_wallet_balance(driver_id, fare, is_driver=True)
        
    # Mark ride completed
    await update_ride_status(ride_id, RideStatus.COMPLETED)
    
    # Notify rider with receipt and rating
    from keyboards.inline import get_rating_keyboard
    receipt = (
        f"✅ <b>Payment Successful!</b>\n\n"
        f"💳 Method: {payment_method.capitalize()}\n"
        f"💵 Amount: {fare:.2f} ETB\n\n"
        f"Please rate your driver:"
    )
    await query.edit_message_text(receipt, reply_markup=get_rating_keyboard(ride_id), parse_mode="HTML")
    
    # Notify driver
    driver_msg = (
        f"✅ <b>Ride Completed!</b>\n\n"
        f"💵 Fare: {fare:.2f} ETB (Paid via {payment_method.capitalize()})\n\n"
        f"Great job!"
    )
    from services.location import get_location_display
    from database.db import set_driver_availability
    await set_driver_availability(driver_id, True)
    
    try:
        await context.bot.send_message(chat_id=driver_id, text=driver_msg, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to notify driver of payment: {e}")


# ==================== Handler Setup ====================

def setup_rider_handlers(application):
    """Register rider-related handlers."""
    # Rider menu entry & registration conversation
    rider_start_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(get_rider_start_regex()), rider_start)],
        states={
            RIDER_REGISTERING_PHONE: [
                MessageHandler(filters.CONTACT | filters.TEXT & ~filters.COMMAND, rider_phone_received)
            ]
        },
        fallbacks=[MessageHandler(filters.Regex(get_cancel_btn_regex()), cancel_request)],
        allow_reentry=True
    )
    application.add_handler(rider_start_conv)
    
    # Favorites conversation
    fav_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(get_favorites_regex()), favorites_menu)],
        states={
            RIDER_MANAGING_FAVORITES: [
                MessageHandler(filters.LOCATION, save_location_start),
                MessageHandler(filters.Regex("^\u2795 Save Current Location$"), save_location_prompt),
                MessageHandler(filters.Regex(get_back_regex()), cancel_request),
                MessageHandler(filters.Regex("^\U0001f4cd"), use_saved_location),
                MessageHandler(filters.TEXT & ~filters.COMMAND, cancel_request)
            ],
            RIDER_SAVING_LOCATION_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_location_name)
            ],
            RIDER_WAITING_DESTINATION: [
                MessageHandler(filters.LOCATION, handle_destination),
                MessageHandler(filters.Regex(get_cancel_btn_regex()), cancel_request)
            ],
            RIDER_CONFIRMING_ROUTE: [
                CallbackQueryHandler(confirm_route_callback, pattern="^confirm_route$|^cancel_route$"),
                MessageHandler(filters.Regex(get_cancel_btn_regex()), cancel_request)
            ]
        },
        fallbacks=[MessageHandler(filters.Regex(get_cancel_btn_regex()), cancel_request)],
        allow_reentry=True
    )
    application.add_handler(fav_conv)
    
    # Ride Request Conversation
    ride_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(get_request_ride_regex()), request_ride_start)],
        states={
            WAITING_LOCATION: [
                MessageHandler(filters.LOCATION, handle_location),
                MessageHandler(filters.Regex(get_cancel_btn_regex()), cancel_request)
            ],
            RIDER_WAITING_DESTINATION: [
                MessageHandler(filters.LOCATION, handle_destination),
                MessageHandler(filters.Regex(get_cancel_btn_regex()), cancel_request)
            ],
            RIDER_CONFIRMING_ROUTE: [
                CallbackQueryHandler(confirm_route_callback, pattern="^confirm_route$|^cancel_route$"),
                MessageHandler(filters.Regex(get_cancel_btn_regex()), cancel_request)
            ]
        },
        fallbacks=[MessageHandler(filters.Regex("^🏠|Main Menu"), cancel_request)], 
        allow_reentry=True
    )
    application.add_handler(ride_conv)
    
    # Ride actions
    application.add_handler(MessageHandler(filters.Regex(get_all_translations("ride_status_btn")), ride_status))
    application.add_handler(MessageHandler(filters.Regex(get_all_translations("cancel_ride_btn")), cancel_ride_button))
    application.add_handler(MessageHandler(filters.Regex("^💳 Wallet"), rider_wallet_menu))
    
    # Callbacks
    application.add_handler(CallbackQueryHandler(cancel_ride_callback, pattern="^cancel_ride_"))
    application.add_handler(CallbackQueryHandler(rate_ride_callback, pattern="^rate_"))
    application.add_handler(CallbackQueryHandler(process_payment_callback, pattern="^pay_"))
