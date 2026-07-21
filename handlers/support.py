"""
AI Support handler for the Rideshare Bot.
Provides an interactive support flow where riders/drivers can ask for help
and receive AI-powered responses.
"""
import re
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, filters
)

from database.db import get_rider, get_driver, get_active_ride_for_user
from services.ai_support import get_support_response, analyze_ride_issue
from utils.logger import logger
from utils.i18n import t, get_all_translations


# States
AWAITING_ISSUE = 0


async def support_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the AI support flow."""
    user = update.effective_user
    
    await update.message.reply_text(
        "🤖 <b>AI Support Assistant</b>\n\n"
        "I'm here to help! Please describe your issue and I'll assist you right away.\n\n"
        "Common issues I can help with:\n"
        "• 🚗 Driver is late or at wrong location\n"
        "• 💳 Payment or fare issues\n"
        "• 📦 Lost item in vehicle\n"
        "• 🚨 Safety concerns\n"
        "• ❓ General questions\n\n"
        "<i>Type your issue below or press /cancel to go back.</i>",
        parse_mode="HTML"
    )
    return AWAITING_ISSUE


async def handle_support_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process a support message with AI classification."""
    user = update.effective_user
    text = update.message.text.strip()
    
    # Get AI response
    result = get_support_response(text)
    
    # Build response
    response = result["response"]
    
    # Add ride context if available
    active_ride = await get_active_ride_for_user(user.id)
    if active_ride:
        response += f"\n\n📋 <b>Your Active Ride:</b> #{active_ride.id} ({active_ride.status.value})"
    
    # Add escalation notice
    if result["escalated"]:
        response += "\n\n🔔 <b>This issue has been flagged for admin review.</b>"
        # In production, this would create a support ticket
        logger.info(f"[AI SUPPORT] Escalated issue from user {user.id}: category={result['category']}, risk={result['risk_level']}")
    
    response += "\n\n<i>Need more help? Describe your issue or press /cancel to exit.</i>"
    
    await update.message.reply_text(response, parse_mode="HTML")
    
    return AWAITING_ISSUE


async def support_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Exit the support flow."""
    await update.message.reply_text(
        "✅ Support session ended. Use /help if you need assistance again.",
    )
    return ConversationHandler.END


def get_support_regex() -> str:
    """Get regex for the support button."""
    return "^🤖 AI Support|^🆘 Support|^🤖|support$"


def setup_support_handlers(application):
    """Register AI support handlers."""
    support_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(get_support_regex()), support_start),
            CommandHandler("support", support_start),
        ],
        states={
            AWAITING_ISSUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_support_message),
            ]
        },
        fallbacks=[
            CommandHandler("cancel", support_cancel),
            MessageHandler(filters.Regex("^(🏠|Main Menu|❌ Cancel)"), support_cancel),
        ],
        allow_reentry=True,
    )
    application.add_handler(support_conv)
