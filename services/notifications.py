"""
Notification service for the Rideshare Bot.
Centralized system for sending notifications to users.
"""
from typing import Optional
from telegram import Bot
from telegram.constants import ParseMode
from utils.logger import logger, log_with_context


async def notify_driver_assigned(bot: Bot, rider_id: int, driver_name: str, 
                                 vehicle_type: str, distance: float, ride_id: int):
    """
    Notify rider that a driver has been assigned.
    
    Args:
        bot: Telegram bot instance
        rider_id: Rider's Telegram user ID
        driver_name: Driver's name
        vehicle_type: Type of vehicle
        distance: Distance to driver in km
        ride_id: Ride ID for logging
    """
    message = (
        f"🚕 <b>Driver Found!</b>\n\n"
        f"👤 Driver: {driver_name}\n"
        f"🚗 Vehicle: {vehicle_type}\n"
        f"📍 Distance: {distance:.1f} km away\n\n"
        f"Your driver is on the way!"
    )
    
    try:
        await bot.send_message(
            chat_id=rider_id,
            text=message,
            parse_mode=ParseMode.HTML
        )
        log_with_context(logger, "INFO", 
                        "Rider notified of driver assignment", 
                        ride_id=ride_id, user_id=rider_id)
    except Exception as e:
        log_with_context(logger, "ERROR", 
                        f"Failed to notify rider: {e}", 
                        ride_id=ride_id, user_id=rider_id)


async def notify_rider_assigned(bot: Bot, driver_id: int, rider_name: str, 
                                pickup_location: str, distance: float, ride_id: int):
    """
    Notify driver that a rider has been assigned.
    
    Args:
        bot: Telegram bot instance
        driver_id: Driver's Telegram user ID
        rider_name: Rider's name
        pickup_location: Formatted pickup location
        distance: Distance to pickup in km
        ride_id: Ride ID for logging
    """
    message = (
        f"🚕 <b>New Ride Request!</b>\n\n"
        f"👤 Rider: {rider_name}\n"
        f"📍 Pickup: {pickup_location}\n"
        f"🛣 Distance: {distance:.1f} km\n\n"
        f"Please confirm to accept this ride."
    )
    
    try:
        await bot.send_message(
            chat_id=driver_id,
            text=message,
            parse_mode=ParseMode.HTML
        )
        log_with_context(logger, "INFO", 
                        "Driver notified of ride assignment", 
                        ride_id=ride_id, user_id=driver_id)
    except Exception as e:
        log_with_context(logger, "ERROR", 
                        f"Failed to notify driver: {e}", 
                        ride_id=ride_id, user_id=driver_id)


async def notify_ride_started(bot: Bot, rider_id: int, driver_id: int, ride_id: int):
    """Notify both parties that the ride has started."""
    rider_message = "🚗 <b>Ride Started!</b>\n\nYour ride is now in progress. Have a safe journey!"
    driver_message = "🚗 <b>Ride Started!</b>\n\nRide is now in progress."
    
    try:
        await bot.send_message(chat_id=rider_id, text=rider_message, parse_mode=ParseMode.HTML)
        await bot.send_message(chat_id=driver_id, text=driver_message, parse_mode=ParseMode.HTML)
        log_with_context(logger, "INFO", "Ride started notifications sent", ride_id=ride_id)
    except Exception as e:
        log_with_context(logger, "ERROR", f"Failed to send ride started notifications: {e}", ride_id=ride_id)


async def notify_ride_completed(bot: Bot, rider_id: int, driver_id: int, ride_id: int):
    """Notify both parties that the ride has been completed."""
    rider_message = "✅ <b>Ride Completed!</b>\n\nThank you for using RideShare Bot. Please rate your driver."
    driver_message = "✅ <b>Ride Completed!</b>\n\nRide has been completed successfully."
    
    try:
        await bot.send_message(chat_id=rider_id, text=rider_message, parse_mode=ParseMode.HTML)
        await bot.send_message(chat_id=driver_id, text=driver_message, parse_mode=ParseMode.HTML)
        log_with_context(logger, "INFO", "Ride completed notifications sent", ride_id=ride_id)
    except Exception as e:
        log_with_context(logger, "ERROR", f"Failed to send ride completed notifications: {e}", ride_id=ride_id)


async def notify_ride_cancelled(bot: Bot, user_id: int, ride_id: int, 
                                other_party_id: Optional[int] = None):
    """
    Notify user(s) that a ride has been cancelled.
    
    Args:
        bot: Telegram bot instance
        user_id: User who cancelled
        ride_id: Ride ID
        other_party_id: Optional ID of other party to notify
    """
    message = "❌ <b>Ride Cancelled</b>\n\nThe ride has been cancelled."
    
    try:
        await bot.send_message(chat_id=user_id, text=message, parse_mode=ParseMode.HTML)
        
        if other_party_id:
            other_message = "❌ <b>Ride Cancelled</b>\n\nThe other party has cancelled the ride."
            await bot.send_message(chat_id=other_party_id, text=other_message, parse_mode=ParseMode.HTML)
        
        log_with_context(logger, "INFO", "Ride cancellation notifications sent", 
                        ride_id=ride_id, user_id=user_id)
    except Exception as e:
        log_with_context(logger, "ERROR", f"Failed to send cancellation notifications: {e}", 
                        ride_id=ride_id, user_id=user_id)
