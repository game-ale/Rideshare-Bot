"""
Pricing engine for the Rideshare Bot.
Handles fare estimation, dynamic pricing, and ETA calculations.
"""

import random

# Pricing Constants
BASE_FARE = 50.0        # ETB
PER_KM_RATE = 20.0      # ETB
PER_MIN_RATE = 2.0      # ETB
MIN_FARE = 100.0        # ETB
AVERAGE_SPEED_KMH = 25.0

def get_surge_multiplier() -> float:
    """
    Simulate dynamic surge pricing based on demand.
    In a real app, this would use time of day, active drivers, etc.
    """
    # 20% chance of a surge between 1.1x and 2.0x
    if random.random() < 0.2:
        return round(random.uniform(1.1, 2.0), 1)
    return 1.0


def calculate_eta(distance_km: float) -> int:
    """
    Calculate estimated time of arrival (duration) in minutes.
    """
    hours = distance_km / AVERAGE_SPEED_KMH
    minutes = hours * 60
    return max(1, int(round(minutes)))


def calculate_fare(distance_km: float, duration_min: int = None) -> float:
    """
    Calculate estimated fare based on distance, duration, and surge.
    """
    if duration_min is None:
        duration_min = calculate_eta(distance_km)
        
    distance_fare = distance_km * PER_KM_RATE
    time_fare = duration_min * PER_MIN_RATE
    
    subtotal = BASE_FARE + distance_fare + time_fare
    
    surge = get_surge_multiplier()
    total = subtotal * surge
    
    return max(MIN_FARE, round(total, 2))
