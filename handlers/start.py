"""
Start handler for the Rideshare Bot.
Handles welcome screen and role selection.
"""
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from keyboards.reply import get_main_menu_keyboard
from utils.logger import logger, log_with_context


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command - show welcome screen with role selection.
    """
    user = update.effective_user
    
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
