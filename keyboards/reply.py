"""
Reply keyboards for the Rideshare Bot.
Provides persistent button menus for user navigation.
"""
from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from utils.i18n import t


def get_main_menu_keyboard(lang: str = "en") -> ReplyKeyboardMarkup:
    """
    Main menu keyboard shown after /start.
    """
    keyboard = [
        [
            KeyboardButton(t("main_menu_driver", lang)),
            KeyboardButton(t("main_menu_rider", lang))
        ],
        [
            KeyboardButton(t("main_menu_lang", lang)),
            KeyboardButton(t("main_menu_help", lang))
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_driver_menu_keyboard(is_available: bool = False, lang: str = "en") -> ReplyKeyboardMarkup:
    """
    Driver menu keyboard.
    """
    if is_available:
        keyboard = [
            [KeyboardButton(t("go_offline", lang))],
            [KeyboardButton(t("my_stats", lang)), KeyboardButton("💳 Wallet")],
            [KeyboardButton("🤖 AI Support"), KeyboardButton(t("main_menu", lang))]
        ]
    else:
        keyboard = [
            [KeyboardButton(t("go_available", lang))],
            [KeyboardButton(t("my_stats", lang)), KeyboardButton("💳 Wallet")],
            [KeyboardButton("🤖 AI Support"), KeyboardButton(t("main_menu", lang))]
        ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_rider_menu_keyboard(has_active_ride: bool = False, lang: str = "en") -> ReplyKeyboardMarkup:
    """
    Rider menu keyboard.
    """
    if has_active_ride:
        keyboard = [
            [KeyboardButton(t("ride_status_btn", lang))],
            [KeyboardButton(t("cancel_ride_btn", lang))],
            [KeyboardButton("🤖 AI Support"), KeyboardButton(t("main_menu", lang))]
        ]
    else:
        keyboard = [
            [KeyboardButton(t("request_ride", lang))],
            [KeyboardButton(t("favorites_menu", lang)), KeyboardButton("💳 Wallet")],
            [KeyboardButton("🤖 AI Support"), KeyboardButton(t("main_menu", lang))]
        ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_vehicle_type_keyboard() -> ReplyKeyboardMarkup:
    """
    Vehicle type selection keyboard for driver registration.
    Stay in English for now as these are often recognizable, or we can localize.
    """
    keyboard = [
        [KeyboardButton("🚗 Car"), KeyboardButton("🏍 Motorcycle")],
        [KeyboardButton("🚐 Van"), KeyboardButton("🛵 Bike")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


def get_location_keyboard(lang: str = "en") -> ReplyKeyboardMarkup:
    """
    Keyboard that requests the user's location.
    """
    keyboard = [
        [KeyboardButton(t("share_location_btn", lang), request_location=True)],
        [KeyboardButton(t("cancel_btn", lang))]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


def get_phone_keyboard(lang: str = "en") -> ReplyKeyboardMarkup:
    """
    Keyboard for phone number input with contact sharing and skip option.
    """
    keyboard = [
        [KeyboardButton("📱 Share Contact", request_contact=True)],
        [KeyboardButton(t("skip_btn", lang))],
        [KeyboardButton(t("cancel_btn", lang))]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


def remove_keyboard() -> ReplyKeyboardRemove:
    """Remove the current keyboard."""
    return ReplyKeyboardRemove()


def get_admin_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Admin panel keyboard with comprehensive management options.
    """
    keyboard = [
        [KeyboardButton("📋 Pending Drivers"), KeyboardButton("👥 All Drivers")],
        [KeyboardButton("🚕 Active Rides"), KeyboardButton("📋 Ride History")],
        [KeyboardButton("❌ Cancelled Rides"), KeyboardButton("📊 Statistics")],
        [KeyboardButton("🔍 Search User")],
        [KeyboardButton(t("main_menu", "en"))]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_favorites_keyboard(locations: list, lang: str = "en") -> ReplyKeyboardMarkup:
    """
    Keyboard showing saved locations + option to add new.
    """
    keyboard = []
    for loc in locations:
        keyboard.append([KeyboardButton(f"📍 {loc.name}")])
    keyboard.append([KeyboardButton("➕ Save Current Location")])
    keyboard.append([KeyboardButton(t("back_btn", lang))])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
