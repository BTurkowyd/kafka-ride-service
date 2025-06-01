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


# Pydantic request schema
class RideRequestPayload(BaseModel):
    ride_id: UUID
    pickup: List[float] = Field(..., min_items=2, max_items=2)
    dropoff: List[float] = Field(..., min_items=2, max_items=2)
    passenger_id: int


class RideStartedPayload(BaseModel):
    ride_id: UUID
    driver_id: int
    location: List[float] = Field(..., min_items=2, max_items=2)


class RideCompletedPayload(BaseModel):
    ride_id: UUID
    driver_id: int
    location: List[float] = Field(..., min_items=2, max_items=2)
    pickup: List[float] = Field(..., min_items=2, max_items=2)
    dropoff: List[float] = Field(..., min_items=2, max_items=2)


class LocationUpdatePayload(BaseModel):
    ride_id: UUID
    driver_id: int
    location: List[float] = Field(..., min_items=2, max_items=2)
