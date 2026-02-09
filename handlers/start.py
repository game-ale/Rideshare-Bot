"""
Start handler for the Rideshare Bot.
Handles welcome screen and role selection.
"""
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from keyboards.reply import get_main_menu_keyboard
from keyboards.inline import get_language_keyboard
from database.db import set_user_language, get_rider, get_driver
from utils.i18n import t
from utils.logger import logger, log_with_context


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command - show welcome screen with role selection.
    """
    user = update.effective_user
    
    # Get user language preference
    lang = "en"
    db_user = await get_rider(user.id) or await get_driver(user.id)
    if db_user:
        lang = db_user.language_code
    
    welcome_message = (
        f"🚕 <b>Welcome to RideShare Bot!</b>\n\n"
        f"Hello {user.first_name}! 👋\n\n"
        f"I'm your personal ride-matching assistant. "
        f"Whether you're looking for a ride or want to drive, I've got you covered!\n\n"
        f"<b>What would you like to do?</b>"
    )
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=get_main_menu_keyboard(),
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
    await query.message.reply_text(
        "🏠",
        reply_markup=get_main_menu_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /help command - show help information.
    """
    help_text = (
        "📚 <b>RideShare Bot Help</b>\n\n"
        "<b>For Riders:</b>\n"
        "• Tap 'Request a Ride' to find a nearby driver\n"
        "• View your ride status anytime\n"
        "• Cancel rides before they start\n"
        "• Rate your driver after completion\n\n"
        "<b>For Drivers:</b>\n"
        "• Register as a driver with your vehicle info\n"
        "• Toggle availability on/off\n"
        "• Accept or decline ride requests\n"
        "• View your stats and ratings\n\n"
        "<b>Commands:</b>\n"
        "/start - Main menu\n"
        "/help - Show this help message\n\n"
        "Need assistance? Contact support."
    )
    
    await update.message.reply_text(help_text, parse_mode="HTML")


async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle 'Main Menu' button - return to start screen.
    """
    await start_command(update, context)


# Handler setup function
def setup_start_handlers(application):
    """Register start-related handlers."""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.Regex("^🏠 Main Menu$"), main_menu_handler))
    application.add_handler(MessageHandler(filters.Regex("^ℹ️ Help$"), help_command))
    application.add_handler(MessageHandler(filters.Regex("^🌐 Language$"), select_language))
    application.add_handler(CallbackQueryHandler(set_language_callback, pattern="^set_lang_"))
