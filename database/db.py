"""
Database connection and operations for the Rideshare Bot.
Provides async database access with proper transaction boundaries.

Key principle: Explicit transaction boundaries prevent race conditions in concurrent requests.
"""
from contextlib import asynccontextmanager
from typing import Optional, List
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from config import DATABASE_URL
from database.models import Base, Driver, Rider, Ride, RideHistory
from enums import RideStatus, VehicleType
from utils.logger import logger, log_with_context

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=False)

# Create session factory
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Initialize database tables."""
    try:
        logger.info(f"Initializing database at {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        # Don't re-raise if you want the bot to keep running to show error messages
        # but in production, we might want it to crash to trigger restart
        raise


@asynccontextmanager
async def get_session():
    """
    Context manager for database sessions.
    Ensures proper cleanup and transaction handling.
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


# ==================== Driver Operations ====================

async def create_driver(user_id: int, name: str, vehicle_type: VehicleType, 
                       latitude: float, longitude: float) -> Driver:
    """Create a new driver or update existing one."""
    async with get_session() as session:
        # Check if driver already exists
        result = await session.execute(select(Driver).where(Driver.id == user_id))
        driver = result.scalar_one_or_none()
        
        if driver:
            # Update existing driver
            driver.name = name
            driver.vehicle_type = vehicle_type
            driver.latitude = latitude
            driver.longitude = longitude
            log_with_context(logger, "INFO", f"Driver {name} updated profile", user_id=user_id)
        else:
            # Create new driver
            driver = Driver(
                id=user_id,
                name=name,
                vehicle_type=vehicle_type,
                latitude=latitude,
                longitude=longitude,
                available=False
            )
            session.add(driver)
            log_with_context(logger, "INFO", f"Driver {name} registered", user_id=user_id)
        
        await session.commit()
        await session.refresh(driver)
        return driver


async def get_driver(user_id: int) -> Optional[Driver]:
    """Get driver by user ID."""
    async with get_session() as session:
        result = await session.execute(select(Driver).where(Driver.id == user_id))
        return result.scalar_one_or_none()


async def set_driver_availability(user_id: int, available: bool) -> bool:
    """Set driver availability status."""
    async with get_session() as session:
        result = await session.execute(select(Driver).where(Driver.id == user_id))
        driver = result.scalar_one_or_none()
        
        if not driver:
            return False
        
        driver.available = available
        await session.commit()
        
        status = "available" if available else "offline"
        log_with_context(logger, "INFO", f"Driver set {status}", user_id=user_id)
        return True


async def get_all_drivers() -> List[Driver]:
    """Get all registered drivers."""
    async with get_session() as session:
        result = await session.execute(select(Driver))
        return list(result.scalars().all())


async def get_available_drivers() -> List[Driver]:
    """Get all available drivers (for matching)."""
    async with get_session() as session:
        result = await session.execute(
            select(Driver).where(Driver.available == True)
        )
        return list(result.scalars().all())


async def update_driver_rating(driver_id: int, new_rating: int):
    """Update driver's average rating after a ride."""
    async with get_session() as session:
        result = await session.execute(select(Driver).where(Driver.id == driver_id))
        driver = result.scalar_one_or_none()
        
        if driver:
            # Calculate new average rating
            total_rides = driver.total_rides
            current_rating = driver.rating
            new_avg = ((current_rating * total_rides) + new_rating) / (total_rides + 1)
            
            driver.rating = round(new_avg, 2)
            driver.total_rides += 1
            
            await session.commit()
            log_with_context(logger, "INFO", 
                           f"Driver rating updated to {driver.rating}", 
                           user_id=driver_id)


# ==================== Rider Operations ====================

async def create_rider(user_id: int, name: str) -> Rider:
    """Create a new rider or update existing one."""
    async with get_session() as session:
        result = await session.execute(select(Rider).where(Rider.id == user_id))
        rider = result.scalar_one_or_none()
        
        if rider:
            rider.name = name
            log_with_context(logger, "INFO", f"Rider {name} updated profile", user_id=user_id)
        else:
            rider = Rider(id=user_id, name=name)
            session.add(rider)
            log_with_context(logger, "INFO", f"Rider {name} registered", user_id=user_id)
        
        await session.commit()
        await session.refresh(rider)
        return rider


async def get_rider(user_id: int) -> Optional[Rider]:
    """Get rider by user ID."""
    async with get_session() as session:
        result = await session.execute(select(Rider).where(Rider.id == user_id))
        return result.scalar_one_or_none()


# ==================== Ride Operations ====================

async def create_ride(rider_id: int, rider_lat: float, rider_lng: float) -> Ride:
    """Create a new ride request."""
    async with get_session() as session:
        ride = Ride(
            rider_id=rider_id,
            status=RideStatus.REQUESTED,
            rider_lat=rider_lat,
            rider_lng=rider_lng
        )
        session.add(ride)
        
        # Add initial history entry
        history = RideHistory(ride=ride, status=RideStatus.REQUESTED)
        session.add(history)
        
        await session.commit()
        await session.refresh(ride)
        
        log_with_context(logger, "INFO", "Ride requested", 
                        ride_id=ride.id, user_id=rider_id)
        return ride


async def assign_driver_to_ride(ride_id: int, driver_id: int, distance: float) -> bool:
    """
    Assign a driver to a ride with atomic transaction.
    This prevents race conditions where multiple rides could be assigned to the same driver.
    
    Returns True if assignment successful, False if driver is no longer available.
    """
    async with get_session() as session:
        async with session.begin():  # Explicit transaction boundary
            # Lock the driver row for update
            result = await session.execute(
                select(Driver).where(
                    and_(Driver.id == driver_id, Driver.available == True)
                ).with_for_update()
            )
            driver = result.scalar_one_or_none()
            
            if not driver:
                log_with_context(logger, "WARNING", 
                               "Driver no longer available for assignment", 
                               ride_id=ride_id, user_id=driver_id)
                return False
            
            # Get the ride
            result = await session.execute(select(Ride).where(Ride.id == ride_id))
            ride = result.scalar_one_or_none()
            
            if not ride or ride.status != RideStatus.REQUESTED:
                log_with_context(logger, "WARNING", 
                               "Ride no longer in REQUESTED state", 
                               ride_id=ride_id)
                return False
            
            # Perform atomic assignment
            ride.driver_id = driver_id
            ride.distance = distance
            ride.status = RideStatus.ASSIGNED
            driver.available = False  # Driver now busy
            
            # Add history entry
            history = RideHistory(ride_id=ride_id, status=RideStatus.ASSIGNED)
            session.add(history)
            
            # Commit happens automatically at end of 'async with session.begin()'
        
        log_with_context(logger, "INFO", 
                        f"Driver {driver_id} assigned to ride", 
                        ride_id=ride_id, user_id=ride.rider_id)
        return True


async def get_ride(ride_id: int) -> Optional[Ride]:
    """Get ride by ID with relationships loaded."""
    async with get_session() as session:
        result = await session.execute(
            select(Ride)
            .options(selectinload(Ride.rider), selectinload(Ride.driver))
            .where(Ride.id == ride_id)
        )
        return result.scalar_one_or_none()


async def get_active_ride_for_user(user_id: int) -> Optional[Ride]:
    """
    Get active ride for a user (rider or driver).
    Active = REQUESTED, ASSIGNED, or ONGOING.
    """
    async with get_session() as session:
        result = await session.execute(
            select(Ride)
            .options(selectinload(Ride.rider), selectinload(Ride.driver))
            .where(
                and_(
                    or_(Ride.rider_id == user_id, Ride.driver_id == user_id),
                    Ride.status.in_([RideStatus.REQUESTED, RideStatus.ASSIGNED, RideStatus.ONGOING])
                )
            )
        )
        return result.scalar_one_or_none()


async def update_ride_status(ride_id: int, new_status: RideStatus) -> bool:
    """Update ride status and add history entry."""
    async with get_session() as session:
        result = await session.execute(select(Ride).where(Ride.id == ride_id))
        ride = result.scalar_one_or_none()
        
        if not ride:
            return False
        
        old_status = ride.status
        ride.status = new_status
        
        # If completing or cancelling, mark completion time and free driver
        if new_status in [RideStatus.COMPLETED, RideStatus.CANCELLED]:
            ride.completed_at = datetime.utcnow()
            
            if ride.driver_id:
                result = await session.execute(select(Driver).where(Driver.id == ride.driver_id))
                driver = result.scalar_one_or_none()
                if driver:
                    driver.available = True  # Free up driver
        
        # Add history entry
        history = RideHistory(ride_id=ride_id, status=new_status)
        session.add(history)
        
        await session.commit()
        
        log_with_context(logger, "INFO", 
                        f"Ride status changed: {old_status.value} → {new_status.value}", 
                        ride_id=ride_id)
        return True


async def add_ride_rating(ride_id: int, rating: int) -> bool:
    """Add rating to a completed ride."""
    async with get_session() as session:
        result = await session.execute(select(Ride).where(Ride.id == ride_id))
        ride = result.scalar_one_or_none()
        
        if not ride or ride.status != RideStatus.COMPLETED:
            return False
        
        ride.rating = rating
        await session.commit()
        
        # Update driver's average rating
        if ride.driver_id:
            await update_driver_rating(ride.driver_id, rating)
        
        log_with_context(logger, "INFO", 
                        f"Ride rated {rating} stars", 
                        ride_id=ride_id)
        return True


async def cancel_ride(ride_id: int) -> bool:
    """Cancel a ride and free up the driver if assigned."""
    return await update_ride_status(ride_id, RideStatus.CANCELLED)


async def get_ride_history(ride_id: int) -> List[RideHistory]:
    """Get status history for a ride."""
    async with get_session() as session:
        result = await session.execute(
            select(RideHistory)
            .where(RideHistory.ride_id == ride_id)
            .order_by(RideHistory.timestamp)
        )
        return list(result.scalars().all())
