"""
Pydantic models and shared logic for Kafka producer API payloads.

Defines request schemas for ride events and imports serializers and helpers.
"""

import os
from datetime import datetime, UTC
from uuid import UUID
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from confluent_kafka import SerializingProducer
from confluent_kafka.serialization import StringSerializer

from .serializer import (
    ride_requested_serializer,
    ride_started_serializer,
    location_update_serializer,
    ride_completed_serializer,
)
from .geolocation import haversine_distance


# Pydantic request schema for ride request event
class RideRequestPayload(BaseModel):
    """
    Schema for a ride request event.
    """

    ride_id: UUID
    pickup: List[float] = Field(..., min_items=2, max_items=2)
    dropoff: List[float] = Field(..., min_items=2, max_items=2)
    passenger_id: int


# Pydantic request schema for ride started event
class RideStartedPayload(BaseModel):
    """
    Schema for a ride started event.
    """

    ride_id: UUID
    driver_id: int
    location: List[float] = Field(..., min_items=2, max_items=2)


# Pydantic request schema for ride completed event
class RideCompletedPayload(BaseModel):
    """
    Schema for a ride completed event.
    """

    ride_id: UUID
    driver_id: int
    location: List[float] = Field(..., min_items=2, max_items=2)
    pickup: List[float] = Field(..., min_items=2, max_items=2)
    dropoff: List[float] = Field(..., min_items=2, max_items=2)


# Pydantic request schema for location update event
class LocationUpdatePayload(BaseModel):
    """
    Schema for a location update event.
    """

    ride_id: UUID
    driver_id: int
    location: List[float] = Field(..., min_items=2, max_items=2)
