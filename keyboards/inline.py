"""
Inline keyboards for the Rideshare Bot.
Provides contextual action buttons within messages.
"""
from telegram import InlineKeyboardMarkup, InlineKeyboardButton


def get_ride_confirmation_keyboard(ride_id: int) -> InlineKeyboardMarkup:
    """
    Ride confirmation keyboard for drivers.
    
    Layout:
    [ ✅ Accept Ride ] [ ❌ Decline ]
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Accept Ride", callback_data=f"accept_ride_{ride_id}"),
            InlineKeyboardButton("❌ Decline", callback_data=f"decline_ride_{ride_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_rating_keyboard(ride_id: int) -> InlineKeyboardMarkup:
    """
    Rating keyboard for riders after ride completion.
    
    Layout:
    [ ⭐ ] [ ⭐⭐ ] [ ⭐⭐⭐ ] [ ⭐⭐⭐⭐ ] [ ⭐⭐⭐⭐⭐ ]
    """
    keyboard = [
        [
            InlineKeyboardButton("⭐", callback_data=f"rate_{ride_id}_1"),
            InlineKeyboardButton("⭐⭐", callback_data=f"rate_{ride_id}_2"),
            InlineKeyboardButton("⭐⭐⭐", callback_data=f"rate_{ride_id}_3"),
            InlineKeyboardButton("⭐⭐⭐⭐", callback_data=f"rate_{ride_id}_4"),
            InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data=f"rate_{ride_id}_5")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_ride_action_keyboard(ride_id: int, is_driver: bool = False) -> InlineKeyboardMarkup:
    """
    Ride action keyboard for ongoing rides.
    
    Driver layout:
    [ ✅ Complete Ride ]
    
    Rider layout:
    [ ❌ Cancel Ride ]
    """
    if is_driver:
        keyboard = [
            [InlineKeyboardButton("✅ Complete Ride", callback_data=f"complete_ride_{ride_id}")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("❌ Cancel Ride", callback_data=f"cancel_ride_{ride_id}")]
        ]
    return InlineKeyboardMarkup(keyboard)


def get_start_ride_keyboard(ride_id: int) -> InlineKeyboardMarkup:
    """
    Start ride keyboard for drivers after accepting.
    
    Layout:
    [ 🚗 Start Ride ]
    """
    keyboard = [
        [InlineKeyboardButton("🚗 Start Ride", callback_data=f"start_ride_{ride_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)
