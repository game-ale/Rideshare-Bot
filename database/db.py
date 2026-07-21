"""
Database connection and operations for the Rideshare Bot.
"""
from contextlib import asynccontextmanager
from typing import Optional, List
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, and_, or_, text, inspect, func
from sqlalchemy.orm import selectinload

from config import DATABASE_URL
from database.models import Base, Driver, Rider, Ride, RideHistory, SavedLocation
from enums import RideStatus, VehicleType, DriverStatus
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
                
                for table in ['drivers', 'riders', 'rides']:
                    if table in table_names:
                        columns = [c['name'] for c in inspector.get_columns(table)]
                        
                        if table in ['drivers', 'riders']:
                            if 'language_code' not in columns:
                                logger.info(f"⚙️ Migrating {table}: adding language_code column")
                                sync_conn.execute(text(f"ALTER TABLE {table} ADD COLUMN language_code VARCHAR(5) DEFAULT 'en'"))
                            if 'phone_number' not in columns:
                                logger.info(f"⚙️ Migrating {table}: adding phone_number column")
                                sync_conn.execute(text(f"ALTER TABLE {table} ADD COLUMN phone_number VARCHAR(20)"))
                            if 'wallet_balance' not in columns:
                                logger.info(f"⚙️ Migrating {table}: adding wallet_balance column")
                                sync_conn.execute(text(f"ALTER TABLE {table} ADD COLUMN wallet_balance FLOAT DEFAULT 0.0"))
                                
                        if table == 'drivers':
                            if 'status' not in columns:
                                logger.info(f"⚙️ Migrating drivers: adding status column")
                                sync_conn.execute(text(f"ALTER TABLE drivers ADD COLUMN status VARCHAR(20) DEFAULT 'APPROVED'")) # Default approved for existing
                            if 'plate_number' not in columns:
                                logger.info(f"⚙️ Migrating drivers: adding plate_number column")
                                sync_conn.execute(text(f"ALTER TABLE drivers ADD COLUMN plate_number VARCHAR(20)"))
                            if 'license_file_id' not in columns:
                                logger.info(f"⚙️ Migrating drivers: adding license_file_id column")
                                sync_conn.execute(text(f"ALTER TABLE drivers ADD COLUMN license_file_id VARCHAR(255)"))
                        
                        if table == 'rides':
                            if 'dest_lat' not in columns:
                                logger.info(f"⚙️ Migrating rides: adding routing columns")
                                sync_conn.execute(text(f"ALTER TABLE rides ADD COLUMN dest_lat FLOAT"))
                                sync_conn.execute(text(f"ALTER TABLE rides ADD COLUMN dest_lng FLOAT"))
                                sync_conn.execute(text(f"ALTER TABLE rides ADD COLUMN estimated_fare FLOAT"))
                                sync_conn.execute(text(f"ALTER TABLE rides ADD COLUMN estimated_duration INTEGER"))
                            if 'final_fare' not in columns:
                                logger.info(f"⚙️ Migrating rides: adding payment columns")
                                sync_conn.execute(text(f"ALTER TABLE rides ADD COLUMN final_fare FLOAT"))
                                sync_conn.execute(text(f"ALTER TABLE rides ADD COLUMN payment_method VARCHAR(20)"))
            
            
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
                       latitude: float, longitude: float,
                       phone_number: str = None, plate_number: str = None, 
                       license_file_id: str = None) -> Driver:
    """Create a new driver or update existing one."""
    async with get_session() as session:
        result = await session.execute(select(Driver).where(Driver.id == user_id))
        driver = result.scalar_one_or_none()
        
        if driver:
            driver.name = name
            driver.vehicle_type = vehicle_type
            driver.latitude = latitude
            driver.longitude = longitude
            if phone_number:
                driver.phone_number = phone_number
            if plate_number:
                driver.plate_number = plate_number
            if license_file_id:
                driver.license_file_id = license_file_id
        else:
            driver = Driver(
                id=user_id,
                name=name,
                phone_number=phone_number,
                vehicle_type=vehicle_type,
                plate_number=plate_number,
                license_file_id=license_file_id,
                status=DriverStatus.PENDING,
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
        if driver:
            driver.available = available
            await session.commit()
            return True
        return False


async def get_pending_drivers() -> List[Driver]:
    """Get all drivers with PENDING status."""
    async with get_session() as session:
        result = await session.execute(select(Driver).where(Driver.status == DriverStatus.PENDING))
        return list(result.scalars().all())


async def update_driver_status(user_id: int, status: DriverStatus) -> bool:
    """Update a driver's verification status."""
    async with get_session() as session:
        result = await session.execute(select(Driver).where(Driver.id == user_id))
        driver = result.scalar_one_or_none()
        if driver:
            driver.status = status
            if status != DriverStatus.APPROVED:
                driver.available = False
            await session.commit()
            return True
        return False


async def update_driver_location(driver_id: int, lat: float, lng: float) -> bool:
    """Update a driver's current GPS coordinates."""
    async with get_session() as session:
        result = await session.execute(select(Driver).where(Driver.id == driver_id))
        driver = result.scalar_one_or_none()
        if driver:
            driver.latitude = lat
            driver.longitude = lng
            await session.commit()
            return True
        return False


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

async def create_rider(user_id: int, name: str, phone_number: str = None) -> Rider:
    async with get_session() as session:
        result = await session.execute(select(Rider).where(Rider.id == user_id))
        rider = result.scalar_one_or_none()
        if rider:
            rider.name = name
            if phone_number:
                rider.phone_number = phone_number
        else:
            rider = Rider(id=user_id, name=name, phone_number=phone_number, language_code="en")
            session.add(rider)
        await session.commit()
        await session.refresh(rider)
        return rider


async def get_rider(user_id: int) -> Optional[Rider]:
    async with get_session() as session:
        result = await session.execute(select(Rider).where(Rider.id == user_id))
        return result.scalar_one_or_none()


async def get_saved_locations(rider_id: int) -> List[SavedLocation]:
    """Get all saved locations for a rider."""
    async with get_session() as session:
        result = await session.execute(select(SavedLocation).where(SavedLocation.rider_id == rider_id))
        return list(result.scalars().all())


async def add_saved_location(rider_id: int, name: str, latitude: float, longitude: float) -> SavedLocation:
    """Add a new saved location for a rider."""
    async with get_session() as session:
        loc = SavedLocation(
            rider_id=rider_id,
            name=name,
            latitude=latitude,
            longitude=longitude
        )
        session.add(loc)
        await session.commit()
        await session.refresh(loc)
        return loc


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


# ==================== Wallet Operations ====================

async def update_wallet_balance(user_id: int, amount: float, is_driver: bool = False) -> bool:
    """Add amount to user's wallet. Use negative amount to deduct."""
    async with get_session() as session:
        model = Driver if is_driver else Rider
        result = await session.execute(select(model).where(model.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.wallet_balance += amount
            await session.commit()
            return True
        return False


# ==================== Ride Operations ====================

async def create_ride(rider_id: int, rider_lat: float, rider_lng: float, 
                      dest_lat: float = None, dest_lng: float = None,
                      estimated_fare: float = None, estimated_duration: int = None) -> Ride:
    async with get_session() as session:
        ride = Ride(
            rider_id=rider_id, 
            status=RideStatus.REQUESTED, 
            rider_lat=rider_lat, 
            rider_lng=rider_lng,
            dest_lat=dest_lat,
            dest_lng=dest_lng,
            estimated_fare=estimated_fare,
            estimated_duration=estimated_duration
        )
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


# ==================== Phase 1: New Query Functions ====================

async def get_rider_ride_count(user_id: int) -> int:
    """Get total number of rides for a rider."""
    async with get_session() as session:
        result = await session.execute(
            select(func.count(Ride.id)).where(Ride.rider_id == user_id)
        )
        return result.scalar() or 0


async def get_driver_completed_rides_count(driver_id: int) -> int:
    """Get total completed rides for a driver."""
    async with get_session() as session:
        result = await session.execute(
            select(func.count(Ride.id)).where(
                and_(Ride.driver_id == driver_id, Ride.status == RideStatus.COMPLETED)
            )
        )
        return result.scalar() or 0


async def get_driver_today_rides(driver_id: int) -> int:
    """Get today's ride count for a driver."""
    from datetime import date
    today_start = datetime.combine(date.today(), datetime.min.time())
    async with get_session() as session:
        result = await session.execute(
            select(func.count(Ride.id)).where(
                and_(
                    Ride.driver_id == driver_id,
                    Ride.status == RideStatus.COMPLETED,
                    Ride.completed_at >= today_start
                )
            )
        )
        return result.scalar() or 0


async def get_completed_rides(limit: int = 20) -> List[Ride]:
    """Get recent completed rides."""
    async with get_session() as session:
        result = await session.execute(
            select(Ride)
            .options(selectinload(Ride.rider), selectinload(Ride.driver))
            .where(Ride.status == RideStatus.COMPLETED)
            .order_by(Ride.completed_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


async def get_cancelled_rides(limit: int = 20) -> List[Ride]:
    """Get recent cancelled rides."""
    async with get_session() as session:
        result = await session.execute(
            select(Ride)
            .options(selectinload(Ride.rider), selectinload(Ride.driver))
            .where(Ride.status == RideStatus.CANCELLED)
            .order_by(Ride.completed_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


async def get_all_riders() -> List[Rider]:
    """Get all registered riders."""
    async with get_session() as session:
        result = await session.execute(select(Rider))
        return list(result.scalars().all())


async def get_platform_stats() -> dict:
    """Get comprehensive platform statistics."""
    async with get_session() as session:
        # Drivers
        total_drivers = (await session.execute(select(func.count(Driver.id)))).scalar() or 0
        available_drivers = (await session.execute(
            select(func.count(Driver.id)).where(Driver.available == True)
        )).scalar() or 0
        
        # Riders
        total_riders = (await session.execute(select(func.count(Rider.id)))).scalar() or 0
        
        # Rides
        total_rides = (await session.execute(select(func.count(Ride.id)))).scalar() or 0
        completed_rides = (await session.execute(
            select(func.count(Ride.id)).where(Ride.status == RideStatus.COMPLETED)
        )).scalar() or 0
        cancelled_rides = (await session.execute(
            select(func.count(Ride.id)).where(Ride.status == RideStatus.CANCELLED)
        )).scalar() or 0
        active_rides = (await session.execute(
            select(func.count(Ride.id)).where(
                Ride.status.in_([RideStatus.REQUESTED, RideStatus.ASSIGNED, RideStatus.ONGOING])
            )
        )).scalar() or 0
        
        # Averages
        avg_rating = (await session.execute(
            select(func.avg(Ride.rating)).where(Ride.rating.isnot(None))
        )).scalar()
        
        completion_rate = (completed_rides / total_rides * 100) if total_rides > 0 else 0
        
        return {
            "total_drivers": total_drivers,
            "available_drivers": available_drivers,
            "total_riders": total_riders,
            "total_rides": total_rides,
            "completed_rides": completed_rides,
            "cancelled_rides": cancelled_rides,
            "active_rides": active_rides,
            "avg_rating": round(avg_rating, 2) if avg_rating else 0,
            "completion_rate": round(completion_rate, 1),
        }
