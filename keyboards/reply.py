"""
Reply keyboards for the Rideshare Bot.
Provides persistent button menus for user navigation.
"""
from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Main menu keyboard shown after /start.
    
    Layout:
    [ 🚗 I'm a Driver ] [ 👤 Request a Ride ]
    [ ℹ️ Help ]
    """
    keyboard = [
        [
            KeyboardButton("🚗 I'm a Driver"),
            KeyboardButton("👤 Request a Ride")
        ],
        [KeyboardButton("ℹ️ Help")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_driver_menu_keyboard(is_available: bool = False) -> ReplyKeyboardMarkup:
    """
    Driver menu keyboard.
    
    Layout (when offline):
    [ ✅ Go Available ]
    [ 📊 My Stats ]
    [ 🏠 Main Menu ]
    
    Layout (when available):
    [ ❌ Go Offline ]
    [ 📊 My Stats ]
    [ 🏠 Main Menu ]
    """
    if is_available:
        keyboard = [
            [KeyboardButton("❌ Go Offline")],
            [KeyboardButton("📊 My Stats")],
            [KeyboardButton("🏠 Main Menu")]
        ]
    else:
        keyboard = [
            [KeyboardButton("✅ Go Available")],
            [KeyboardButton("📊 My Stats")],
            [KeyboardButton("🏠 Main Menu")]
        ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_rider_menu_keyboard(has_active_ride: bool = False) -> ReplyKeyboardMarkup:
    """
    Rider menu keyboard.
    
    Layout (no active ride):
    [ 🚕 Request Ride ]
    [ 🏠 Main Menu ]
    
    Layout (with active ride):
    [ 📍 Ride Status ]
    [ ❌ Cancel Ride ]
    [ 🏠 Main Menu ]
    """
    if has_active_ride:
        keyboard = [
            [KeyboardButton("📍 Ride Status")],
            [KeyboardButton("❌ Cancel Ride")],
            [KeyboardButton("🏠 Main Menu")]
        ]
    else:
        keyboard = [
            [KeyboardButton("🚕 Request Ride")],
            [KeyboardButton("🏠 Main Menu")]
        ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_vehicle_type_keyboard() -> ReplyKeyboardMarkup:
    """
    Vehicle type selection keyboard for driver registration.
    
    Layout:
    [ 🚗 Car ] [ 🏍 Motorcycle ]
    [ 🚐 Van ] [ 🛵 Bike ]
    """
    keyboard = [
        [KeyboardButton("🚗 Car"), KeyboardButton("🏍 Motorcycle")],
        [KeyboardButton("🚐 Van"), KeyboardButton("🛵 Bike")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


def get_admin_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Admin panel keyboard.
    
    Layout:
    [ 👥 All Drivers ] [ 🚕 Active Rides ]
    [ 📊 Statistics ]
    [ 🏠 Main Menu ]
    """
    keyboard = [
        [KeyboardButton("👥 All Drivers"), KeyboardButton("🚕 Active Rides")],
        [KeyboardButton("📊 Statistics")],
        [KeyboardButton("🏠 Main Menu")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def remove_keyboard() -> ReplyKeyboardRemove:
    """Remove the current keyboard."""
    return ReplyKeyboardRemove()
