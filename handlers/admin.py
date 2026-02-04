"""
Admin handler for the Rideshare Bot.
Provides admin panel for managing drivers and viewing system statistics.
"""
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from config import ADMIN_IDS
from database.db import get_all_drivers, get_active_ride_for_user
from database.models import Ride
from enums import RideStatus
from keyboards.reply import get_admin_menu_keyboard
from utils.logger import logger, log_with_context
from sqlalchemy import select, func
from database.db import get_session


async def is_admin(user_id: int) -> bool:
    """Check if user is an admin."""
    return user_id in ADMIN_IDS


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin panel (restricted to admins only)."""
    user = update.effective_user
    
    if not await is_admin(user.id):
        await update.message.reply_text("❌ You don't have permission to access the admin panel.")
        return
    
    await update.message.reply_text(
        "🛠 <b>Admin Panel</b>\n\n"
        "Welcome to the admin dashboard. Use the buttons below to manage the system.",
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
    
    async with get_session() as session:
        # Count drivers
        from database.models import Driver
        driver_count_result = await session.execute(select(func.count(Driver.id)))
        total_drivers = driver_count_result.scalar()
        
        available_drivers_result = await session.execute(
            select(func.count(Driver.id)).where(Driver.available == True)
        )
        available_drivers = available_drivers_result.scalar()
        
        # Count rides
        total_rides_result = await session.execute(select(func.count(Ride.id)))
        total_rides = total_rides_result.scalar()
        
        completed_rides_result = await session.execute(
            select(func.count(Ride.id)).where(Ride.status == RideStatus.COMPLETED)
        )
        completed_rides = completed_rides_result.scalar()
        
        active_rides_result = await session.execute(
            select(func.count(Ride.id)).where(
                Ride.status.in_([RideStatus.REQUESTED, RideStatus.ASSIGNED, RideStatus.ONGOING])
            )
        )
        active_rides = active_rides_result.scalar()
    
    stats_message = (
        "📊 <b>System Statistics</b>\n\n"
        f"👥 Total Drivers: {total_drivers}\n"
        f"✅ Available Drivers: {available_drivers}\n\n"
        f"🚕 Total Rides: {total_rides}\n"
        f"✅ Completed: {completed_rides}\n"
        f"🔄 Active: {active_rides}\n"
    )
    
    await update.message.reply_text(stats_message, parse_mode="HTML")


# ==================== Handler Setup ====================

def setup_admin_handlers(application):
    """Register admin-related handlers."""
    
    # Admin panel access
    application.add_handler(MessageHandler(filters.Regex("^🛠 Admin$"), admin_panel))
    
    # Admin actions
    application.add_handler(MessageHandler(filters.Regex("^👥 All Drivers$"), view_all_drivers))
    application.add_handler(MessageHandler(filters.Regex("^🚕 Active Rides$"), view_active_rides))
    application.add_handler(MessageHandler(filters.Regex("^📊 Statistics$"), view_statistics))
