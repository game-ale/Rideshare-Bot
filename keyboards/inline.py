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


def get_cancel_ride_keyboard(ride_id: int) -> InlineKeyboardMarkup:
    """
    Cancellation confirmation keyboard for riders.

    Layout:
    [ Yes, Cancel Ride ]
    """
    keyboard = [
        [InlineKeyboardButton("Yes, Cancel Ride", callback_data=f"cancel_ride_{ride_id}")]
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


def get_language_keyboard() -> InlineKeyboardMarkup:
    """
    Language selection keyboard.
    
    Layout:
    [ English ] [ የአማርኛ ] [ Afan Oromo ]
    """
    keyboard = [
        [
            InlineKeyboardButton("English 🇬🇧", callback_data="set_lang_en"),
            InlineKeyboardButton("አማርኛ 🇪🇹", callback_data="set_lang_am"),
            InlineKeyboardButton("Afan Oromo 🇪🇹", callback_data="set_lang_om")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_driver_moderation_keyboard(driver_id: int) -> InlineKeyboardMarkup:
    """
    Inline keyboard for admin to approve or reject a pending driver.
    
    Layout:
    [ ✅ Approve ] [ ❌ Reject ]
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_driver_{driver_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_driver_{driver_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_route_confirmation_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """
    Keyboard for rider to confirm or cancel the requested route.
    """
    from utils.i18n import t
    keyboard = [
        [
            InlineKeyboardButton(t("confirm_ride_btn", lang), callback_data="confirm_route"),
            InlineKeyboardButton(t("cancel_btn", lang), callback_data="cancel_route")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_payment_keyboard(ride_id: int, fare: float) -> InlineKeyboardMarkup:
    """
    Keyboard for rider to select a payment method.
    """
    keyboard = [
        [
            InlineKeyboardButton(f"💵 Cash ({fare} ETB)", callback_data=f"pay_cash_{ride_id}")
        ],
        [
            InlineKeyboardButton("💳 Demo Card", callback_data=f"pay_card_{ride_id}"),
            InlineKeyboardButton("💰 Wallet", callback_data=f"pay_wallet_{ride_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

