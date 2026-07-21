"""
Admin handler for the Rideshare Bot.
Provides admin panel for managing drivers and viewing system statistics.
"""
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, CallbackQueryHandler, filters

from config import ADMIN_IDS
from database.db import (
    get_all_drivers, get_active_ride_for_user, get_session,
    get_platform_stats, get_completed_rides, get_cancelled_rides, get_rider,
    get_pending_drivers, update_driver_status, get_driver
)
from database.models import Ride, Driver
from enums import RideStatus, DriverStatus
from keyboards.reply import get_admin_menu_keyboard
from keyboards.inline import get_driver_moderation_keyboard
from utils.logger import logger, log_with_context
from utils.i18n import t
from sqlalchemy import select, func


async def is_admin(user_id: int) -> bool:
    """Check if user is an admin."""
    return user_id in ADMIN_IDS


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin panel (restricted to admins only)."""
    user = update.effective_user
    
    if not await is_admin(user.id):
        await update.message.reply_text("❌ You don't have permission to access the admin panel.")
        return
    
    stats = await get_platform_stats()
    
    panel_text = t(
        "admin_panel", "en",
        drivers=stats["total_drivers"],
        available=stats["available_drivers"],
        riders=stats["total_riders"],
        active=stats["active_rides"]
    )
    
    await update.message.reply_text(
        panel_text,
        reply_markup=get_admin_menu_keyboard(),
        parse_mode="HTML"
    )
    
    log_with_context(logger, "INFO", "Admin panel accessed", user_id=user.id)


async def view_all_drivers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View all registered drivers."""
    user = update.effective_user
    
    if not await is_admin(user.id):
        await update.message.reply_text("❌ Unauthorized.")
        return
    
    drivers = await get_all_drivers()
    
    if not drivers:
        await update.message.reply_text("📋 No drivers registered yet.")
        return
    
    message = "👥 <b>All Drivers</b>\n\n"
    
    for driver in drivers:
        status = "✅ Available" if driver.available else "❌ Offline"
        message += (
            f"👤 {driver.name}\n"
            f"🚗 {driver.vehicle_type.value}\n"
            f"⭐ {driver.rating:.1f} ({driver.total_rides} rides)\n"
            f"📍 {status}\n"
            f"🆔 ID: {driver.id}\n\n"
        )
    
    await update.message.reply_text(message, parse_mode="HTML")


async def view_active_rides(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View all active rides."""
    user = update.effective_user
    
    if not await is_admin(user.id):
        await update.message.reply_text("❌ Unauthorized.")
        return
    
    async with get_session() as session:
        result = await session.execute(
            select(Ride).where(
                Ride.status.in_([RideStatus.REQUESTED, RideStatus.ASSIGNED, RideStatus.ONGOING])
            )
        )
        active_rides = list(result.scalars().all())
    
    if not active_rides:
        await update.message.reply_text("📋 No active rides at the moment.")
        return
    
    message = "🚕 <b>Active Rides</b>\n\n"
    
    for ride in active_rides:
        message += (
            f"🆔 Ride #{ride.id}\n"
            f"📊 Status: {ride.status.value}\n"
            f"👤 Rider ID: {ride.rider_id}\n"
        )
        
        if ride.driver_id:
            message += f"🚗 Driver ID: {ride.driver_id}\n"
        
        message += "\n"
    
    await update.message.reply_text(message, parse_mode="HTML")


async def view_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View system statistics."""
    user = update.effective_user
    
    if not await is_admin(user.id):
        await update.message.reply_text("❌ Unauthorized.")
        return
    
    stats = await get_platform_stats()
    
    stats_message = (
        "📊 <b>System Statistics</b>\n\n"
        f"👥 Total Drivers: {stats['total_drivers']}\n"
        f"✅ Available Drivers: {stats['available_drivers']}\n"
        f"👤 Total Riders: {stats['total_riders']}\n\n"
        f"🚕 Total Rides: {stats['total_rides']}\n"
        f"✅ Completed: {stats['completed_rides']}\n"
        f"❌ Cancelled: {stats['cancelled_rides']}\n"
        f"🔄 Active: {stats['active_rides']}\n\n"
        f"⭐ Avg Rating: {stats['avg_rating']}\n"
        f"🏆 Completion Rate: {stats['completion_rate']}%"
    )
    
    await update.message.reply_text(stats_message, parse_mode="HTML")

async def view_ride_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View completed ride history."""
    if not await is_admin(update.effective_user.id):
        return
        
    rides = await get_completed_rides(limit=10)
    
    if not rides:
        await update.message.reply_text(t("admin_no_rides", "en"), parse_mode="HTML")
        return
        
    msg = t("admin_ride_history", "en")
    for r in rides:
        msg += f"#{r.id} | {r.completed_at.strftime('%m-%d %H:%M')} | {r.distance_km:.1f}km | ⭐{r.rating or '-'}\n"
        
    await update.message.reply_text(msg, parse_mode="HTML")

async def view_cancelled_rides(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View cancelled ride history."""
    if not await is_admin(update.effective_user.id):
        return
        
    rides = await get_cancelled_rides(limit=10)
    
    if not rides:
        await update.message.reply_text(t("admin_no_rides", "en"), parse_mode="HTML")
        return
        
    msg = t("admin_cancelled_rides", "en")
    for r in rides:
        msg += f"#{r.id} | Rider: {r.rider_id} | Driver: {r.driver_id or 'None'}\n"
        
    await update.message.reply_text(msg, parse_mode="HTML")

async def search_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search user by ID stub."""
    if not await is_admin(update.effective_user.id):
        return
    await update.message.reply_text("🔍 Please provide the Telegram User ID (e.g., /search 123456789)")


async def view_pending_drivers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View pending driver applications."""
    if not await is_admin(update.effective_user.id):
        return
    
    drivers = await get_pending_drivers()
    
    if not drivers:
        await update.message.reply_text("✅ No pending driver applications.")
        return
    
    await update.message.reply_text(
        f"📋 <b>Pending Driver Applications ({len(drivers)})</b>",
        parse_mode="HTML"
    )
    
    for driver in drivers:
        info = (
            f"👤 <b>{driver.name}</b>\n"
            f"📱 Phone: {driver.phone_number or 'N/A'}\n"
            f"🚗 Vehicle: {driver.vehicle_type.value}\n"
            f"🏠 Plate: {driver.plate_number or 'N/A'}\n"
            f"🆔 ID: {driver.id}"
        )
        await update.message.reply_text(
            info,
            reply_markup=get_driver_moderation_keyboard(driver.id),
            parse_mode="HTML"
        )
        
        # If driver uploaded a license photo, send it
        if driver.license_file_id:
            try:
                await context.bot.send_photo(
                    chat_id=update.effective_user.id,
                    photo=driver.license_file_id,
                    caption=f"📸 License photo for {driver.name}"
                )
            except Exception:
                pass


async def approve_driver_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin approve button."""
    query = update.callback_query
    await query.answer()
    
    if not await is_admin(query.from_user.id):
        await query.edit_message_text("❌ Unauthorized.")
        return
    
    driver_id = int(query.data.split("_")[-1])
    success = await update_driver_status(driver_id, DriverStatus.APPROVED)
    
    if success:
        driver = await get_driver(driver_id)
        lang = driver.language_code if driver else "en"
        await query.edit_message_text(
            f"✅ Driver <b>{driver.name}</b> (ID: {driver_id}) has been <b>APPROVED</b>.",
            parse_mode="HTML"
        )
        # Notify the driver
        try:
            await context.bot.send_message(
                chat_id=driver_id,
                text=t("approved_msg", lang),
                parse_mode="HTML"
            )
        except Exception:
            pass
    else:
        await query.edit_message_text("❌ Failed to approve driver.")


async def reject_driver_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin reject button."""
    query = update.callback_query
    await query.answer()
    
    if not await is_admin(query.from_user.id):
        await query.edit_message_text("❌ Unauthorized.")
        return
    
    driver_id = int(query.data.split("_")[-1])
    success = await update_driver_status(driver_id, DriverStatus.REJECTED)
    
    if success:
        driver = await get_driver(driver_id)
        lang = driver.language_code if driver else "en"
        await query.edit_message_text(
            f"❌ Driver <b>{driver.name}</b> (ID: {driver_id}) has been <b>REJECTED</b>.",
            parse_mode="HTML"
        )
        # Notify the driver
        try:
            await context.bot.send_message(
                chat_id=driver_id,
                text=t("rejected_msg", lang),
                parse_mode="HTML"
            )
        except Exception:
            pass
    else:
        await query.edit_message_text("❌ Failed to reject driver.")


# ==================== Handler Setup ====================

def setup_admin_handlers(application):
    """Register admin-related handlers."""
    
    # Admin panel access
    application.add_handler(MessageHandler(filters.Regex("^🛠 Admin$"), admin_panel))
    
    # Admin actions
    application.add_handler(MessageHandler(filters.Regex("^📋 Pending Drivers$"), view_pending_drivers))
    application.add_handler(MessageHandler(filters.Regex("^👥 All Drivers$"), view_all_drivers))
    application.add_handler(MessageHandler(filters.Regex("^🚕 Active Rides$"), view_active_rides))
    application.add_handler(MessageHandler(filters.Regex("^📋 Ride History$"), view_ride_history))
    application.add_handler(MessageHandler(filters.Regex("^❌ Cancelled Rides$"), view_cancelled_rides))
    application.add_handler(MessageHandler(filters.Regex("^📊 Statistics$"), view_statistics))
    application.add_handler(MessageHandler(filters.Regex("^🔍 Search User$"), search_user))
    
    # Admin inline callbacks
    application.add_handler(CallbackQueryHandler(approve_driver_callback, pattern="^approve_driver_"))
    application.add_handler(CallbackQueryHandler(reject_driver_callback, pattern="^reject_driver_"))
