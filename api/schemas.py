from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enums import VehicleType, DriverStatus, RideStatus


# ==================== Enums to Str ====================
# Using standard Pydantic validation for the Enums might require exact Enum matching,
# but for the API we want to output strings. We can use ConfigDict to use enum values.

# ==================== Driver Schemas ====================

class DriverBase(BaseModel):
    id: int
    name: str
    phone_number: Optional[str] = None
    vehicle_type: VehicleType
    plate_number: Optional[str] = None
    status: DriverStatus
    available: bool
    latitude: float
    longitude: float
    rating: float
    total_rides: int
    wallet_balance: float
    language_code: str
    created_at: Optional[datetime] = None

class DriverResponse(DriverBase):
    model_config = {"from_attributes": True, "use_enum_values": True}


class DriverVerifyRequest(BaseModel):
    action: str  # "approve" or "reject"


# ==================== Rider Schemas ====================

class RiderBase(BaseModel):
    id: int
    name: str
    phone_number: Optional[str] = None
    language_code: str
    wallet_balance: float
    created_at: Optional[datetime] = None

class RiderResponse(RiderBase):
    model_config = {"from_attributes": True, "use_enum_values": True}


# ==================== Ride Schemas ====================

class RideBase(BaseModel):
    id: int
    rider_id: int
    driver_id: Optional[int] = None
    status: RideStatus
    rider_lat: float
    rider_lng: float
    dest_lat: Optional[float] = None
    dest_lng: Optional[float] = None
    distance: Optional[float] = None
    estimated_fare: Optional[float] = None
    final_fare: Optional[float] = None
    payment_method: Optional[str] = None
    rating: Optional[int] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class RideResponse(RideBase):
    rider_name: Optional[str] = None
    driver_name: Optional[str] = None
    
    model_config = {"from_attributes": True, "use_enum_values": True}


# ==================== Stats Schema ====================

class PlatformStats(BaseModel):
    total_drivers: int
    available_drivers: int
    total_riders: int
    total_rides: int
    completed_rides: int
    cancelled_rides: int
    active_rides: int
    avg_rating: float
    completion_rate: float
