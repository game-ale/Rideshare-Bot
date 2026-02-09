"""
Database connection and operations for the Rideshare Bot.
"""
from contextlib import asynccontextmanager
from typing import Optional, List
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, and_, or_, text, inspect
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
    """Initialize database tables and handle simple migrations."""
    try:
        logger.info(f"💾 Initializing database: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
        
        async with engine.begin() as conn:
            # Create tables if they don't exist
            await conn.run_sync(Base.metadata.create_all)
            
            # Simple migration check for language_code
            def migrate_schema(sync_conn):
                inspector = inspect(sync_conn)
                table_names = inspector.get_table_names()
                
                for table in ['drivers', 'riders']:
                    if table in table_names:
                        columns = [c['name'] for c in inspector.get_columns(table)]
                        if 'language_code' not in columns:
                            logger.info(f"⚙️ Migrating {table}: adding language_code column")
                            sync_conn.execute(text(f"ALTER TABLE {table} ADD COLUMN language_code VARCHAR(5) DEFAULT 'en'"))
            
            
            # We wrap this in another try/except because if it fails, we still want the bot to try and start
            try:
                await conn.run_sync(migrate_schema)
            except Exception as migrate_err:
                logger.warning(f"⚠️ Schema migration notice (usually okay): {migrate_err}")
            
        logger.info("✅ Database initialization complete")
    except Exception as e:
        logger.error(f"❌ Fatal database error: {e}", exc_info=True)
        # In production, we keep going so the bot can at least log errors
        # but if the DB is truly down, the first query will fail anyway.


@asynccontextmanager
async def get_session():
    """Context manager for database sessions."""
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
        result = await session.execute(select(Driver).where(Driver.id == user_id))
        driver = result.scalar_one_or_none()
        
        if driver:
            driver.name = name
            driver.vehicle_type = vehicle_type
            driver.latitude = latitude
            driver.longitude = longitude
        else:
            driver = Driver(
                id=user_id,
                name=name,
                vehicle_type=vehicle_type,
                latitude=latitude,
                longitude=longitude,
                available=False,
                language_code="en"
            )
            session.add(driver)
        
        await session.commit()
        await session.refresh(driver)
        return driver


async def get_driver(user_id: int) -> Optional[Driver]:
    async with get_session() as session:
        result = await session.execute(select(Driver).where(Driver.id == user_id))
        return result.scalar_one_or_none()


async def set_driver_availability(user_id: int, available: bool) -> bool:
    async with get_session() as session:
        result = await session.execute(select(Driver).where(Driver.id == user_id))
        driver = result.scalar_one_or_none()
        if not driver: return False
        driver.available = available
        await session.commit()
        return True


async def update_driver_rating(driver_id: int, new_rating: int):
    async with get_session() as session:
        result = await session.execute(select(Driver).where(Driver.id == driver_id))
        driver = result.scalar_one_or_none()
        if driver:
            total_rides = driver.total_rides
            current_rating = driver.rating
            new_avg = ((current_rating * total_rides) + new_rating) / (total_rides + 1)
            driver.rating = round(new_avg, 2)
            driver.total_rides += 1
            await session.commit()


async def get_all_drivers() -> List[Driver]:
    """Get all registered drivers."""
    async with get_session() as session:
        result = await session.execute(select(Driver))
        return list(result.scalars().all())


async def get_available_drivers() -> List[Driver]:
    """Get all drivers currently marked as available."""
    async with get_session() as session:
        result = await session.execute(select(Driver).where(Driver.available == True))
        return list(result.scalars().all())


# ==================== Rider Operations ====================

async def create_rider(user_id: int, name: str) -> Rider:
    async with get_session() as session:
        result = await session.execute(select(Rider).where(Rider.id == user_id))
        rider = result.scalar_one_or_none()
        if rider:
            rider.name = name
        else:
            rider = Rider(id=user_id, name=name, language_code="en")
            session.add(rider)
        await session.commit()
        await session.refresh(rider)
        return rider


async def get_rider(user_id: int) -> Optional[Rider]:
    async with get_session() as session:
        result = await session.execute(select(Rider).where(Rider.id == user_id))
        return result.scalar_one_or_none()


async def set_user_language(user_id: int, language_code: str) -> bool:
    async with get_session() as session:
        result = await session.execute(select(Driver).where(Driver.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            result = await session.execute(select(Rider).where(Rider.id == user_id))
            user = result.scalar_one_or_none()
        if not user: return False
        user.language_code = language_code
        await session.commit()
        return True


# ==================== Ride Operations ====================

async def create_ride(rider_id: int, rider_lat: float, rider_lng: float) -> Ride:
    async with get_session() as session:
        ride = Ride(rider_id=rider_id, status=RideStatus.REQUESTED, 
                    rider_lat=rider_lat, rider_lng=rider_lng)
        session.add(ride)
        history = RideHistory(ride=ride, status=RideStatus.REQUESTED)
        session.add(history)
        await session.commit()
        await session.refresh(ride)
        return ride


async def assign_driver_to_ride(ride_id: int, driver_id: int, distance: float) -> bool:
    async with get_session() as session:
        async with session.begin():
            result = await session.execute(
                select(Driver).where(and_(Driver.id == driver_id, Driver.available == True)).with_for_update()
            )
            driver = result.scalar_one_or_none()
            if not driver: return False
            result = await session.execute(select(Ride).where(Ride.id == ride_id))
            ride = result.scalar_one_or_none()
            if not ride or ride.status != RideStatus.REQUESTED: return False
            ride.driver_id = driver_id
            ride.distance = distance
            ride.status = RideStatus.ASSIGNED
            driver.available = False
            history = RideHistory(ride_id=ride_id, status=RideStatus.ASSIGNED)
            session.add(history)
        return True


async def get_ride(ride_id: int) -> Optional[Ride]:
    async with get_session() as session:
        result = await session.execute(
            select(Ride).options(selectinload(Ride.rider), selectinload(Ride.driver)).where(Ride.id == ride_id)
        )
        return result.scalar_one_or_none()


async def get_active_ride_for_user(user_id: int) -> Optional[Ride]:
    async with get_session() as session:
        result = await session.execute(
            select(Ride).options(selectinload(Ride.rider), selectinload(Ride.driver))
            .where(and_(or_(Ride.rider_id == user_id, Ride.driver_id == user_id),
                        Ride.status.in_([RideStatus.REQUESTED, RideStatus.ASSIGNED, RideStatus.ONGOING])))
        )
        return result.scalar_one_or_none()


async def update_ride_status(ride_id: int, new_status: RideStatus) -> bool:
    async with get_session() as session:
        result = await session.execute(select(Ride).where(Ride.id == ride_id))
        ride = result.scalar_one_or_none()
        if not ride: return False
        ride.status = new_status
        if new_status in [RideStatus.COMPLETED, RideStatus.CANCELLED]:
            ride.completed_at = datetime.utcnow()
            if ride.driver_id:
                res = await session.execute(select(Driver).where(Driver.id == ride.driver_id))
                driver = res.scalar_one_or_none()
                if driver: driver.available = True
        history = RideHistory(ride_id=ride_id, status=new_status)
        session.add(history)
        await session.commit()
        return True


async def add_ride_rating(ride_id: int, rating: int) -> bool:
    async with get_session() as session:
        result = await session.execute(select(Ride).where(Ride.id == ride_id))
        ride = result.scalar_one_or_none() # FIXED the NameError here
        if not ride or ride.status != RideStatus.COMPLETED: return False
        ride.rating = rating
        await session.commit()
        if ride.driver_id:
            await update_driver_rating(ride.driver_id, rating)
        return True


async def cancel_ride(ride_id: int) -> bool:
    return await update_ride_status(ride_id, RideStatus.CANCELLED)


async def get_ride_history(ride_id: int) -> List[RideHistory]:
    async with get_session() as session:
        result = await session.execute(
            select(RideHistory).where(RideHistory.ride_id == ride_id).order_by(RideHistory.timestamp)
        )
        return list(result.scalars().all())
