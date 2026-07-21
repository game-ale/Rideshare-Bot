"""
Database models for the Rideshare Bot.
Defines the schema for drivers, riders, and rides with proper relationships.

Note: FSM manages interaction flow, while the database is the single source of truth for ride state.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum as SQLEnum, BigInteger
from sqlalchemy.orm import declarative_base, relationship
from enums import RideStatus, VehicleType, DriverStatus

Base = declarative_base()


class Driver(Base):
    """Driver model - stores driver information and availability."""
    __tablename__ = "drivers"
    
    id = Column(BigInteger, primary_key=True)  # Telegram user ID
    name = Column(String(50), nullable=False)
    phone_number = Column(String(20), nullable=True)  # Optional phone number
    vehicle_type = Column(SQLEnum(VehicleType), nullable=False)
    plate_number = Column(String(20), nullable=True)
    license_file_id = Column(String(255), nullable=True)
    status = Column(SQLEnum(DriverStatus), default=DriverStatus.PENDING)
    available = Column(Boolean, default=False)
    latitude = Column(Float, nullable=False)  # Dummy location
    longitude = Column(Float, nullable=False)  # Dummy location
    rating = Column(Float, default=5.0)
    total_rides = Column(Integer, default=0)
    wallet_balance = Column(Float, default=0.0)
    language_code = Column(String(5), default="en")  # 'en', 'am', 'om'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    rides = relationship("Ride", back_populates="driver", foreign_keys="Ride.driver_id")
    
    def __repr__(self):
        return f"<Driver(id={self.id}, name={self.name}, vehicle={self.vehicle_type.value}, available={self.available})>"


class Rider(Base):
    """Rider model - stores rider information."""
    __tablename__ = "riders"
    
    id = Column(BigInteger, primary_key=True)  # Telegram user ID
    name = Column(String(50), nullable=False)
    phone_number = Column(String(20), nullable=True)  # Optional phone number
    language_code = Column(String(5), default="en")  # 'en', 'am', 'om'
    wallet_balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    rides = relationship("Ride", back_populates="rider", foreign_keys="Ride.rider_id")
    saved_locations = relationship("SavedLocation", back_populates="rider", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Rider(id={self.id}, name={self.name})>"

class SavedLocation(Base):
    """Stores favorite locations for riders (e.g., Home, Work)."""
    __tablename__ = "saved_locations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rider_id = Column(BigInteger, ForeignKey("riders.id"), nullable=False)
    name = Column(String(50), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    rider = relationship("Rider", back_populates="saved_locations")
    
    def __repr__(self):
        return f"<SavedLocation(name={self.name}, rider_id={self.rider_id})>"


class Ride(Base):
    """
    Ride model - stores ride requests and assignments.
    
    Status flow: REQUESTED → ASSIGNED → ONGOING → COMPLETED/CANCELLED
    """
    __tablename__ = "rides"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rider_id = Column(BigInteger, ForeignKey("riders.id"), nullable=False)
    driver_id = Column(BigInteger, ForeignKey("drivers.id"), nullable=True)  # Null until assigned
    status = Column(SQLEnum(RideStatus), nullable=False, default=RideStatus.REQUESTED)
    rider_lat = Column(Float, nullable=False)  # Pickup location
    rider_lng = Column(Float, nullable=False)
    dest_lat = Column(Float, nullable=True)    # Destination location
    dest_lng = Column(Float, nullable=True)
    distance = Column(Float, nullable=True)    # Distance to driver in km
    estimated_fare = Column(Float, nullable=True) # Estimated fare
    estimated_duration = Column(Integer, nullable=True) # Estimated duration in minutes
    final_fare = Column(Float, nullable=True)  # Actual charged amount
    payment_method = Column(String(20), nullable=True) # CASH, WALLET, CARD
    rating = Column(Integer, nullable=True)    # Rider's rating of driver (1-5)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    rider = relationship("Rider", back_populates="rides", foreign_keys=[rider_id])
    driver = relationship("Driver", back_populates="rides", foreign_keys=[driver_id])
    history = relationship("RideHistory", back_populates="ride", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Ride(id={self.id}, rider_id={self.rider_id}, driver_id={self.driver_id}, status={self.status.value})>"


class RideHistory(Base):
    """
    Ride history model - tracks status changes for analytics and debugging.
    Provides audit trail for ride lifecycle.
    """
    __tablename__ = "ride_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ride_id = Column(Integer, ForeignKey("rides.id"), nullable=False)
    status = Column(SQLEnum(RideStatus), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    ride = relationship("Ride", back_populates="history")
    
    def __repr__(self):
        return f"<RideHistory(ride_id={self.ride_id}, status={self.status.value}, timestamp={self.timestamp})>"
