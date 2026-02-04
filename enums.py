"""
Domain enums for the Rideshare Bot.
Provides type-safe constants for ride and driver states.
"""
from enum import Enum


class RideStatus(str, Enum):
    """Ride lifecycle states - single source of truth for ride status."""
    REQUESTED = "REQUESTED"
    ASSIGNED = "ASSIGNED"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class VehicleType(str, Enum):
    """Available vehicle types for drivers."""
    CAR = "Car"
    BIKE = "Bike"
    VAN = "Van"
    MOTORCYCLE = "Motorcycle"


class UserRole(str, Enum):
    """User roles in the system."""
    RIDER = "rider"
    DRIVER = "driver"
    ADMIN = "admin"
