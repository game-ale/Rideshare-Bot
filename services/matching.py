"""
Driver matching service for the Rideshare Bot.
Implements smart driver selection based on distance and availability.
"""
from typing import Optional, List, Tuple
from database.models import Driver
from database.db import get_available_drivers
from services.location import calculate_distance
from config import MAX_SEARCH_DISTANCE_KM
from utils.logger import logger, log_with_context


async def find_nearest_driver(rider_lat: float, rider_lng: float, 
                              ride_id: Optional[int] = None) -> Optional[Tuple[Driver, float]]:
    """
    Find the nearest available driver to a rider's location.
    
    Algorithm:
    1. Get all available drivers (available=True)
    2. Calculate Euclidean distance for each driver
    3. Filter drivers within MAX_SEARCH_DISTANCE_KM
    4. Sort by distance (ascending)
    5. Return nearest driver or None
    
    Args:
        rider_lat: Rider's pickup latitude
        rider_lng: Rider's pickup longitude
        ride_id: Optional ride ID for logging
    
    Returns:
        Tuple of (Driver, distance_km) or None if no drivers available
    """
    # Get all available drivers
    drivers = await get_available_drivers()
    
    if not drivers:
        log_with_context(logger, "INFO", 
                        "No available drivers found", 
                        ride_id=ride_id)
        return None
    
    # Calculate distances for all drivers
    driver_distances: List[Tuple[Driver, float]] = []
    
    for driver in drivers:
        distance = calculate_distance(
            rider_lat, rider_lng,
            driver.latitude, driver.longitude
        )
        
        # Only consider drivers within search radius
        if distance <= MAX_SEARCH_DISTANCE_KM:
            driver_distances.append((driver, distance))
    
    if not driver_distances:
        log_with_context(logger, "INFO", 
                        f"No drivers within {MAX_SEARCH_DISTANCE_KM} km", 
                        ride_id=ride_id)
        return None
    
    # Sort by distance (nearest first)
    driver_distances.sort(key=lambda x: x[1])
    
    nearest_driver, distance = driver_distances[0]
    
    log_with_context(logger, "INFO", 
                    f"Found nearest driver: {nearest_driver.name} ({distance} km away)", 
                    ride_id=ride_id, user_id=nearest_driver.id)
    
    return nearest_driver, distance


async def get_driver_stats(driver_id: int) -> dict:
    """
    Get statistics for a driver.
    
    Returns:
        Dictionary with driver stats (rating, total_rides, etc.)
    """
    from database.db import get_driver
    
    driver = await get_driver(driver_id)
    
    if not driver:
        return {}
    
    return {
        "name": driver.name,
        "vehicle_type": driver.vehicle_type.value,
        "rating": driver.rating,
        "total_rides": driver.total_rides,
        "available": driver.available
    }
