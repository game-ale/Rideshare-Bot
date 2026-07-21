"""
Start handler for the Rideshare Bot.
Handles welcome screen and role selection.
"""
import re
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from keyboards.reply import get_main_menu_keyboard
from keyboards.inline import get_language_keyboard
from database.db import set_user_language, get_rider, get_driver, get_rider_ride_count, get_driver_completed_rides_count, get_active_ride_for_user, cancel_ride
from utils.i18n import t, get_all_translations
from utils.logger import logger, log_with_context
from config import ADMIN_IDS
from telegram.ext import ConversationHandler


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command - show welcome screen with role selection.
    """
    user = update.effective_user
    
    # Get user language preference
    db_user = await get_rider(user.id) or await get_driver(user.id)
    
    if not db_user:
        # First time user
        welcome_message = t("welcome_first_time", "en", name=user.first_name)
        await update.message.reply_text(
            welcome_message,
            reply_markup=get_language_keyboard(),
            parse_mode="HTML"
        )
        await update.message.reply_text(
            t("about_rideshare", "en"),
            parse_mode="HTML"
        )
        log_with_context(logger, "INFO", f"New user {user.first_name} started bot", user_id=user.id)
        return
        
    lang = db_user.language_code
    welcome_message = t("welcome_returning", lang, name=user.first_name)
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=get_main_menu_keyboard(lang),
        parse_mode="HTML"
    )
    
    log_with_context(logger, "INFO", f"User {user.first_name} started bot", user_id=user.id)


async def select_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show language selection menu."""
    user = update.effective_user
    db_user = await get_rider(user.id) or await get_driver(user.id)
    lang = db_user.language_code if db_user else "en"
    
    await update.message.reply_text(
        t("select_language", lang),
        reply_markup=get_language_keyboard(),
        parse_mode="HTML"
    )


async def set_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection callback."""
    query = update.callback_query
    await query.answer()
    
    lang_code = query.data.split("_")[-1]
    user_id = update.effective_user.id
    
    # Update in DB
    await set_user_language(user_id, lang_code)
    
    # Notify user with updated language
    await query.edit_message_text(
        t("lang_updated", lang_code),
        parse_mode="HTML"
    )
    
    # Show main menu again with new language text
    await context.bot.send_message(
        chat_id=user_id,
        text=t("welcome_returning", lang_code, name=update.effective_user.first_name),
        reply_markup=get_main_menu_keyboard(lang_code),
        parse_mode="HTML"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /help command - show help information based on user role.
    """
    user = update.effective_user
    db_user = await get_driver(user.id) or await get_rider(user.id)
    lang = db_user.language_code if db_user else "en"
    
    is_admin = user.id in ADMIN_IDS
    is_driver = await get_driver(user.id) is not None
    
    if is_admin:
        help_text = t("help_admin", lang)
    elif is_driver:
        help_text = t("help_driver", lang)
    elif db_user: # Registered rider
        help_text = t("help_rider", lang)
    else:
        help_text = t("help_general", lang)
        
    await update.message.reply_text(help_text, parse_mode="HTML")

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /profile command - show user profile.
    """
    user = update.effective_user
    driver = await get_driver(user.id)
    rider = await get_rider(user.id)
    
    if driver:
        lang = driver.language_code
        completed_rides = await get_driver_completed_rides_count(user.id)
        status_str = "✅ Available" if driver.available else "❌ Offline"
        
        profile_text = t(
            "profile_driver", lang,
            name=driver.name,
            phone=driver.phone_number or "Not set",
            language=driver.language_code,
            vehicle=driver.vehicle_type.value,
            rating=f"{driver.rating:.1f}",
            total_rides=completed_rides,
            status=status_str,
            joined=driver.created_at.strftime('%Y-%m-%d')
        )
    elif rider:
        lang = rider.language_code
        ride_count = await get_rider_ride_count(user.id)
        
        profile_text = t(
            "profile_rider", lang,
            name=rider.name,
            phone=rider.phone_number or "Not set",
            language=rider.language_code,
            total_rides=ride_count,
            joined=rider.created_at.strftime('%Y-%m-%d')
        )
    else:
        profile_text = t("profile_not_found", "en")
        
    await update.message.reply_text(profile_text, parse_mode="HTML")

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Global /cancel command - cancels any active operation and ride.
    """
    user = update.effective_user
    db_user = await get_driver(user.id) or await get_rider(user.id)
    lang = db_user.language_code if db_user else "en"
    
    active_ride = await get_active_ride_for_user(user.id)
    
    if active_ride:
        # Instead of direct cancel, prompt for confirmation (similar to cancel ride flow)
        # But for global cancel we can just cancel it to be safe and exit
        await cancel_ride(active_ride.id)
        await update.message.reply_text(
            t("cancel_confirmed", lang),
            reply_markup=get_main_menu_keyboard(lang),
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            t("cancel_no_active", lang),
            reply_markup=get_main_menu_keyboard(lang),
            parse_mode="HTML"
        )
    return ConversationHandler.END


async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle 'Main Menu' button - return to start screen.
    """
    await start_command(update, context)


def get_lang_regex() -> str:
    """Get regex for Language button in all languages."""
    options = get_all_translations("main_menu_lang")
    return f"^({'|'.join(map(re.escape, options))})$"

def get_help_regex() -> str:
    """Get regex for Help button in all languages."""
    options = get_all_translations("main_menu_help")
    return f"^({'|'.join(map(re.escape, options))})$"

def get_home_regex() -> str:
    """Get regex for Main Menu button in all languages."""
    options = get_all_translations("main_menu")
    return f"^({'|'.join(map(re.escape, options))})$"


# Handler setup function
def setup_start_handlers(application):
    """Register start-related handlers."""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    application.add_handler(MessageHandler(filters.Regex(get_home_regex()), main_menu_handler))
    application.add_handler(MessageHandler(filters.Regex(get_help_regex()), help_command))
    application.add_handler(MessageHandler(filters.Regex(get_lang_regex()), select_language))
    application.add_handler(CallbackQueryHandler(set_language_callback, pattern="^set_lang_"))
