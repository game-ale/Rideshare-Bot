"""
Database models for the Rideshare Bot.
Defines the schema for drivers, riders, and rides with proper relationships.

Note: FSM manages interaction flow, while the database is the single source of truth for ride state.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from enums import RideStatus, VehicleType

Base = declarative_base()


class Driver(Base):
    """Driver model - stores driver information and availability."""
    __tablename__ = "drivers"
    
    id = Column(Integer, primary_key=True)  # Telegram user ID
    name = Column(String(50), nullable=False)
    vehicle_type = Column(SQLEnum(VehicleType), nullable=False)
    available = Column(Boolean, default=False)
    latitude = Column(Float, nullable=False)  # Dummy location
    longitude = Column(Float, nullable=False)  # Dummy location
    rating = Column(Float, default=5.0)
    total_rides = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    rides = relationship("Ride", back_populates="driver", foreign_keys="Ride.driver_id")
    
    def __repr__(self):
        return f"<Driver(id={self.id}, name={self.name}, vehicle={self.vehicle_type.value}, available={self.available})>"


class Rider(Base):
    """Rider model - stores rider information."""
    __tablename__ = "riders"
    
    id = Column(Integer, primary_key=True)  # Telegram user ID
    name = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    rides = relationship("Ride", back_populates="rider", foreign_keys="Ride.rider_id")
    
    def __repr__(self):
        return f"<Rider(id={self.id}, name={self.name})>"


class Ride(Base):
    """
    Ride model - stores ride requests and assignments.
    
    Status flow: REQUESTED → ASSIGNED → ONGOING → COMPLETED/CANCELLED
    """
    __tablename__ = "rides"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rider_id = Column(Integer, ForeignKey("riders.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)  # Null until assigned
    status = Column(SQLEnum(RideStatus), nullable=False, default=RideStatus.REQUESTED)
    rider_lat = Column(Float, nullable=False)  # Pickup location
    rider_lng = Column(Float, nullable=False)
    distance = Column(Float, nullable=True)  # Distance to driver in km
    rating = Column(Integer, nullable=True)  # Rider's rating of driver (1-5)
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
