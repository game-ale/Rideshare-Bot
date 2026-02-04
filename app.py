"""
RideShare Bot - Main Application Entry Point

A production-ready Telegram bot that simulates a ride-matching system with 
FSM-driven interactions, database-backed persistence, and role-based user flows.

Author: Portfolio Project
License: MIT
"""
import asyncio
from telegram.ext import Application

from config import BOT_TOKEN, IS_PRODUCTION, WEBHOOK_URL, WEBHOOK_PATH, WEBAPP_HOST, WEBAPP_PORT
from database.db import init_db
from handlers.start import setup_start_handlers
from handlers.driver import setup_driver_handlers
from handlers.rider import setup_rider_handlers
from handlers.admin import setup_admin_handlers
from utils.logger import logger


async def post_init(application: Application):
    """Initialize database after application starts."""
    await init_db()
    logger.info("Bot initialized successfully")


def main():
    """Main function to run the bot."""
    logger.info("Starting RideShare Bot...")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # Register all handlers
    setup_start_handlers(application)
    setup_driver_handlers(application)
    setup_rider_handlers(application)
    setup_admin_handlers(application)
    
    logger.info("All handlers registered")
    
    # Run bot
    if IS_PRODUCTION and WEBHOOK_URL:
        # Production mode with webhooks
        logger.info(f"Running in PRODUCTION mode with webhooks: {WEBHOOK_URL}")
        
        # Start webhook server
        application.run_webhook(
            listen=WEBAPP_HOST,
            port=WEBAPP_PORT,
            url_path=WEBHOOK_PATH,
            webhook_url=f"{WEBHOOK_URL}{WEBHOOK_PATH}",
            allowed_updates=["message", "callback_query"]
        )
    else:
        # Development mode with long polling
        logger.info("Running in DEVELOPMENT mode with long polling")
        
        # Start polling (this handles the event loop internally)
        application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
