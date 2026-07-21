"""
Database Seeding Script for Rideshare Bot Demo
This script populates the database with realistic test data for portfolio demonstrations.
It creates riders, drivers, active rides, and ride history to make the admin panel and stats look active.
"""
import asyncio
import random
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, delete

from config import DATABASE_URL
from database.db import init_db
from database.models import Base, Driver, Rider, Ride, RideHistory
from enums import VehicleType, RideStatus, DriverStatus

# Setup Database Engine
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Dummy Data
MOCK_DRIVERS = [
    {"id": 10001, "name": "Abebe Kebede", "phone": "+251911223344", "v_type": VehicleType.CAR, "lat": 9.0054, "lng": 38.7636, "avail": True, "rating": 4.8, "status": DriverStatus.APPROVED},
    {"id": 10002, "name": "Chala Diriba", "phone": "+251922334455", "v_type": VehicleType.MOTORCYCLE, "lat": 9.0200, "lng": 38.7500, "avail": True, "rating": 4.5, "status": DriverStatus.APPROVED},
    {"id": 10003, "name": "Dawit Tesfaye", "phone": "+251933445566", "v_type": VehicleType.VAN, "lat": 8.9900, "lng": 38.7800, "avail": False, "rating": 4.9, "status": DriverStatus.APPROVED},
    {"id": 10004, "name": "Hanna Mulugeta", "phone": "+251944556677", "v_type": VehicleType.CAR, "lat": 9.0100, "lng": 38.7500, "avail": False, "rating": 0.0, "status": DriverStatus.PENDING},
]

MOCK_RIDERS = [
    {"id": 20001, "name": "Sara Tadesse", "phone": "+251944556677"},
    {"id": 20002, "name": "Kidist Alemu", "phone": "+251955667788"},
    {"id": 20003, "name": "Biniam Worku", "phone": "+251966778899"},
]

async def clear_mock_data(session: AsyncSession):
    """Clear previously seeded mock data (IDs 1000x and 2000x)."""
    print("🧹 Clearing previous mock data...")
    driver_ids = [d["id"] for d in MOCK_DRIVERS]
    rider_ids = [r["id"] for r in MOCK_RIDERS]
    
    # Delete rides associated with mock users
    await session.execute(delete(Ride).where(Ride.driver_id.in_(driver_ids)))
    await session.execute(delete(Ride).where(Ride.rider_id.in_(rider_ids)))
    
    # Delete users
    await session.execute(delete(Driver).where(Driver.id.in_(driver_ids)))
    await session.execute(delete(Rider).where(Rider.id.in_(rider_ids)))
    await session.commit()

async def seed_data():
    """Seed the database with mock data."""
    print("🌱 Starting database seeding...")
    await init_db()
    
    async with AsyncSessionLocal() as session:
        await clear_mock_data(session)
        
        print("👥 Seeding Drivers...")
        for d in MOCK_DRIVERS:
            driver = Driver(
                id=d["id"],
                name=d["name"],
                phone_number=d["phone"],
                vehicle_type=d["v_type"],
                latitude=d["lat"],
                longitude=d["lng"],
                available=d["avail"],
                status=d["status"],
                rating=d["rating"],
                total_rides=random.randint(10, 100) if d["status"] == DriverStatus.APPROVED else 0,
                language_code="en",
                plate_number=f"A{random.randint(10000, 99999)}"
            )
            session.add(driver)
            
        print("👤 Seeding Riders...")
        for r in MOCK_RIDERS:
            rider = Rider(
                id=r["id"],
                name=r["name"],
                phone_number=r["phone"],
                language_code="am"
            )
            session.add(rider)
            
        await session.commit()
        
        print("🚕 Seeding Rides...")
        now = datetime.utcnow()
        
        # 1. Completed Ride
        ride1 = Ride(
            rider_id=20001,
            driver_id=10001,
            status=RideStatus.COMPLETED,
            rider_lat=9.0100, rider_lng=38.7600,
            distance=4.2,
            rating=5.0,
            created_at=now - timedelta(hours=2),
            completed_at=now - timedelta(hours=1, minutes=30)
        )
        session.add(ride1)
        
        # 2. Cancelled Ride
        ride2 = Ride(
            rider_id=20002,
            driver_id=10002,
            status=RideStatus.CANCELLED,
            rider_lat=8.9950, rider_lng=38.7500,
            distance=1.5,
            created_at=now - timedelta(days=1),
            completed_at=now - timedelta(days=1, minutes=5)
        )
        session.add(ride2)
        
        # 3. Active (Ongoing) Ride
        ride3 = Ride(
            rider_id=20003,
            driver_id=10003,
            status=RideStatus.ONGOING,
            rider_lat=9.0300, rider_lng=38.7700,
            distance=3.1,
            created_at=now - timedelta(minutes=15)
        )
        session.add(ride3)
        
        await session.commit()
        print("✅ Seeding completed successfully! The database is now ready for demonstration.")

if __name__ == "__main__":
    asyncio.run(seed_data())
