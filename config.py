"""
Configuration module for the Rideshare Bot.
Loads environment variables and provides application settings.
"""
import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

# Admin Configuration
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
ADMIN_IDS: List[int] = [int(id.strip()) for id in ADMIN_IDS_STR.split(",") if id.strip()]

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"

# Webhook Configuration
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
WEBAPP_HOST = os.getenv("WEBAPP_HOST", "0.0.0.0")
WEBAPP_PORT = int(os.getenv("WEBAPP_PORT", "8000"))

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./rideshare.db")

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Location Configuration (Dummy data bounds - Addis Ababa area)
CITY_LAT_MIN = 9.0
CITY_LAT_MAX = 9.1
CITY_LNG_MIN = 38.7
CITY_LNG_MAX = 38.8

# Business Logic Configuration
MAX_SEARCH_DISTANCE_KM = 10.0  # Maximum distance to search for drivers
RIDE_TIMEOUT_MINUTES = 30  # Time before ride request expires
