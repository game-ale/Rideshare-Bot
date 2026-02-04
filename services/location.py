"""
Location utilities for the Rideshare Bot.
Provides dummy location generation and distance calculations.
"""
import random
import math
from typing import Tuple
from config import CITY_LAT_MIN, CITY_LAT_MAX, CITY_LNG_MIN, CITY_LNG_MAX


def generate_random_location() -> Tuple[float, float]:
    """
    Generate a random location within city bounds.
    Returns (latitude, longitude).
    
    Example: For Addis Ababa area (9.0-9.1, 38.7-38.8)
    """
    lat = random.uniform(CITY_LAT_MIN, CITY_LAT_MAX)
    lng = random.uniform(CITY_LNG_MIN, CITY_LNG_MAX)
    return round(lat, 6), round(lng, 6)


def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate distance between two points using Haversine formula.
    Returns distance in kilometers.
    
    Args:
        lat1, lng1: First point coordinates
        lat2, lng2: Second point coordinates
    
    Returns:
        Distance in kilometers (rounded to 2 decimal places)
    """
    # Earth's radius in kilometers
    R = 6371.0
    
    # Convert degrees to radians
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return round(distance, 2)


def format_distance(distance_km: float) -> str:
    """
    Format distance for display.
    
    Examples:
        0.5 km → "500 m"
        1.23 km → "1.2 km"
        10.5 km → "10.5 km"
    """
    if distance_km < 1.0:
        meters = int(distance_km * 1000)
        return f"{meters} m"
    else:
        return f"{distance_km:.1f} km"


def get_location_display(lat: float, lng: float) -> str:
    """
    Format coordinates for display.
    
    Example: (9.0234, 38.7456) → "9.023°N, 38.746°E"
    """
    lat_dir = "N" if lat >= 0 else "S"
    lng_dir = "E" if lng >= 0 else "W"
    return f"{abs(lat):.3f}°{lat_dir}, {abs(lng):.3f}°{lng_dir}"
