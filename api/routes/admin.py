"""
Admin API routes for the RideShare Dashboard.
Provides endpoints for platform stats, ride management, driver moderation, and rider info.
"""
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from database.db import (
    get_platform_stats, get_all_drivers, get_all_riders,
    get_completed_rides, get_cancelled_rides, get_pending_drivers,
    update_driver_status, get_driver, get_rider,
    get_active_ride_for_user, get_ride,
)
from enums import DriverStatus, RideStatus
from services.ai_support import generate_driver_insights, generate_demand_forecast
from api.schemas import (
    DriverResponse, RiderResponse, RideResponse, PlatformStats, DriverVerifyRequest
)

router = APIRouter()


# ==================== Stats Endpoints ====================

@router.get("/stats", response_model=PlatformStats)
async def api_get_stats():
    """Get platform-wide statistics."""
    stats = await get_platform_stats()
    return stats


# ==================== Driver Endpoints ====================

@router.get("/drivers", response_model=List[DriverResponse])
async def api_get_drivers(
    status: Optional[str] = Query(None, description="Filter by driver status: PENDING, APPROVED, REJECTED, SUSPENDED"),
):
    """Get all drivers, optionally filtered by status."""
    drivers = await get_all_drivers()
    
    if status:
        status_upper = status.upper()
        drivers = [d for d in drivers if (d.status.value if d.status else "UNKNOWN") == status_upper]
    
    return drivers


@router.get("/drivers/pending", response_model=List[DriverResponse])
async def api_get_pending_drivers():
    """Get all drivers awaiting verification."""
    drivers = await get_pending_drivers()
    return drivers


@router.get("/drivers/{driver_id}", response_model=DriverResponse)
async def api_get_driver(driver_id: int):
    """Get a specific driver by ID."""
    driver = await get_driver(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


@router.patch("/drivers/{driver_id}/verify", response_model=DriverResponse)
async def api_verify_driver(driver_id: int, body: DriverVerifyRequest):
    """Approve or reject a driver."""
    driver = await get_driver(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    if body.action == "approve":
        success = await update_driver_status(driver_id, DriverStatus.APPROVED)
    elif body.action == "reject":
        success = await update_driver_status(driver_id, DriverStatus.REJECTED)
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'reject'.")
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update driver status")
    
    updated_driver = await get_driver(driver_id)
    return updated_driver


# ==================== Rider Endpoints ====================

@router.get("/riders", response_model=List[RiderResponse])
async def api_get_riders():
    """Get all registered riders."""
    riders = await get_all_riders()
    return riders


@router.get("/riders/{rider_id}", response_model=RiderResponse)
async def api_get_rider(rider_id: int):
    """Get a specific rider by ID."""
    rider = await get_rider(rider_id)
    if not rider:
        raise HTTPException(status_code=404, detail="Rider not found")
    return rider


# ==================== Ride Endpoints ====================

@router.get("/rides", response_model=List[RideResponse])
async def api_get_rides(
    status: Optional[str] = Query(None, description="Filter by status: COMPLETED, CANCELLED"),
    limit: int = Query(50, ge=1, le=200),
):
    """Get rides, optionally filtered by status."""
    if status and status.upper() == "COMPLETED":
        rides = await get_completed_rides(limit=limit)
    elif status and status.upper() == "CANCELLED":
        rides = await get_cancelled_rides(limit=limit)
    else:
        # Get all rides — both completed and cancelled
        completed = await get_completed_rides(limit=limit)
        cancelled = await get_cancelled_rides(limit=limit)
        rides = completed + cancelled
        rides.sort(key=lambda r: r.created_at if r.created_at else datetime.min, reverse=True)
        rides = rides[:limit]
    
    # Add rider_name and driver_name for the schema
    for r in rides:
        r.rider_name = r.rider.name if r.rider else None
        r.driver_name = r.driver.name if r.driver else None

    return rides


@router.get("/rides/{ride_id}", response_model=RideResponse)
async def api_get_ride(ride_id: int):
    """Get a specific ride by ID."""
    ride = await get_ride(ride_id)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    ride.rider_name = ride.rider.name if ride.rider else None
    ride.driver_name = ride.driver.name if ride.driver else None
    return ride


# ==================== AI Endpoints ====================

@router.get("/ai/insights")
async def api_get_ai_insights():
    """Get AI-generated insights for all drivers."""
    drivers = await get_all_drivers()
    all_insights = []
    
    for driver in drivers:
        driver_dict = DriverResponse.model_validate(driver).model_dump()
        insights = generate_driver_insights(driver_dict)
        for insight in insights:
            insight["driver_id"] = driver.id
            insight["driver_name"] = driver.name
            all_insights.append(insight)
            
    # Sort insights to show action items and warnings first
    severity_order = {"action": 0, "warning": 1, "positive": 2, "neutral": 3}
    all_insights.sort(key=lambda x: severity_order.get(x["type"], 99))
    
    return all_insights


@router.get("/ai/demand")
async def api_get_ai_demand():
    """Get AI-generated demand forecast."""
    forecast = generate_demand_forecast()
    return forecast
