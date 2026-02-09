"""
Location utilities for the Rideshare Bot.
Provides real GPS support, geopy distance calculations, and map integration.
"""
import random
import math
from typing import Tuple
from geopy.distance import geodesic
from config import CITY_LAT_MIN, CITY_LAT_MAX, CITY_LNG_MIN, CITY_LNG_MAX


def generate_random_location() -> Tuple[float, float]:
    """
    Generate a random location within city bounds for simulation.
    Returns (latitude, longitude).
    """
    lat = random.uniform(CITY_LAT_MIN, CITY_LAT_MAX)
    lng = random.uniform(CITY_LNG_MIN, CITY_LNG_MAX)
    return round(lat, 6), round(lng, 6)


def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate distance between two points using Geodesic (precise) formula.
    Returns distance in kilometers.
    """
    return round(geodesic((lat1, lng1), (lat2, lng2)).kilometers, 2)


def format_distance(distance_km: float) -> str:
    """Format distance for display."""
    if distance_km < 1.0:
        meters = int(distance_km * 1000)
        return f"{meters} m"
    else:
        return f"{distance_km:.1f} km"


def get_location_display(lat: float, lng: float) -> str:
    """Format coordinates for display."""
    lat_dir = "N" if lat >= 0 else "S"
    lng_dir = "E" if lng >= 0 else "W"
    return f"{abs(lat):.3f}°{lat_dir}, {abs(lng):.3f}°{lng_dir}"


def get_google_maps_link(lat: float, lng: float) -> str:
    """Generate a Google Maps link for a location."""
    return f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"


def get_static_map_url(lat: float, lng: float, zoom: int = 15) -> str:
    """
    Generate an OpenStreetMap static image URL.
    Note: Using OpenStreetMap static maps for privacy and cost-efficiency.
    """
    return f"https://static-maps.yandex.ru/1.x/?ll={lng},{lat}&z={zoom}&l=map&pt={lng},{lat},pm2rdl"
