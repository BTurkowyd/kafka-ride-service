"""
FastAPI application for producing Uber ride events to Kafka.

This service exposes endpoints for simulating ride lifecycle events
(ride request, ride started, ride completed, location update)
and publishes them to Kafka topics using Avro serialization.
"""

import os
from datetime import datetime, UTC

from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from confluent_kafka import SerializingProducer
from confluent_kafka.serialization import StringSerializer
from producer.modules.postgres import DB_CONFIG
import psycopg2

from producer.modules.serializer import (
    ride_requested_serializer,
    ride_started_serializer,
    location_update_serializer,
    ride_completed_serializer,
)
from producer.modules.geolocation import haversine_distance
from producer.modules.base_models import (
    RideRequestPayload,
    RideStartedPayload,
    RideCompletedPayload,
    LocationUpdatePayload,
)

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Kafka configuration
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
TOPIC_NAME = "uber.ride_requested"

# Common Kafka producer configuration
producer_config = {
    "bootstrap.servers": KAFKA_BROKER,
    "key.serializer": StringSerializer("utf_8"),
}


@app.get("/health")
def health_check():
    """
    Health check endpoint for readiness/liveness probes.
    """
    return {"status": "ok"}


@app.post("/ride-request")
def ride_request(data: RideRequestPayload):
    """
    Publishes a ride requested event to Kafka.

    Args:
        data (RideRequestPayload): Ride request details.

    Returns:
        dict: Status and event data.
    """
    # Prepare event payload
    event = {
        "event_type": "ride_requested",
        "ride_id": str(data.ride_id),
        "timestamp": datetime.now(UTC).isoformat(),
        "pickup": data.pickup,
        "dropoff": data.dropoff,
        "passenger_id": data.passenger_id,
    }

    try:
        # Create a Kafka producer with Avro serializer
        producer = SerializingProducer(
            {**producer_config, "value.serializer": ride_requested_serializer}
        )
        producer.produce(topic=TOPIC_NAME, value=event)
        producer.flush()
        return {"status": "published", "event": event}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ride-started")
def ride_started(data: RideStartedPayload):
    """
    Publishes a ride started event to Kafka.

    Args:
        data (RideStartedPayload): Ride started details.

    Returns:
        dict: Status and event data.
    """
    event = {
        "event_type": "ride_started",
        "ride_id": str(data.ride_id),
        "timestamp": datetime.now(UTC).isoformat(),
        "driver_id": data.driver_id,
        "location": data.location,
    }

    try:
        producer = SerializingProducer(
            {**producer_config, "value.serializer": ride_started_serializer}
        )
        producer.produce(topic="uber.ride_started", value=event)
        producer.flush()
        return {"status": "published", "event": event}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ride-completed")
def ride_completed(data: RideCompletedPayload):
    """
    Publishes a ride completed event to Kafka.

    Args:
        data (RideCompletedPayload): Ride completed details.

    Returns:
        dict: Status and event data.
    """
    # Calculate fare based on distance
    fare = round(haversine_distance(data.pickup, data.dropoff) * 2.4, 2)

    event = {
        "event_type": "ride_completed",
        "ride_id": str(data.ride_id),
        "timestamp": datetime.now(UTC).isoformat(),
        "driver_id": data.driver_id,
        "location": data.location,
        "fare": fare,
    }

    try:
        producer = SerializingProducer(
            {**producer_config, "value.serializer": ride_completed_serializer}
        )
        producer.produce(topic="uber.ride_completed", value=event)
        producer.flush()
        return {"status": "published", "event": event}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/location-update")
def location_update(data: LocationUpdatePayload):
    """
    Publishes a location update event to Kafka.

    Args:
        data (LocationUpdatePayload): Location update details.

    Returns:
        dict: Status and event data.
    """
    event = {
        "event_type": "location_update",
        "ride_id": str(data.ride_id),
        "timestamp": datetime.now(UTC).isoformat(),
        "driver_id": data.driver_id,
        "location": data.location,
    }

    try:
        producer = SerializingProducer(
            {**producer_config, "value.serializer": location_update_serializer}
        )
        producer.produce(topic="uber.location_update", value=event)
        producer.flush()
        return {"status": "published", "event": event}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get-passengers")
def get_passenger():
    """
    Fetches all passenger IDs from the database.

    Returns:
        dict: List of passenger IDs.
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM passengers ORDER BY id;")
        passenger_id = cursor.fetchall()
        if not passenger_id:
            raise HTTPException(status_code=404, detail="No passengers found")
        passenger_id = [pid[0] for pid in passenger_id]  # Flatten the list of tuples

        conn.close()
        return {"passenger_ids": passenger_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get-drivers")
def get_driver():
    """
    Fetches all driver IDs from the database.

    Returns:
        dict: List of driver IDs.
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM drivers ORDER BY id;")
        driver_id = cursor.fetchall()
        if not driver_id:
            raise HTTPException(status_code=404, detail="No drivers found")
        driver_id = [did[0] for did in driver_id]  # Flatten the list of tuples

        conn.close()
        return {"driver_ids": driver_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
