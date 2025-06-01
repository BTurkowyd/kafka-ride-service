import os
from datetime import datetime, UTC
from uuid import UUID
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from confluent_kafka import SerializingProducer
from confluent_kafka.serialization import StringSerializer

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

load_dotenv()

app = FastAPI()

# Config
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
TOPIC_NAME = "uber.ride_requested"

# Common producer config
producer_config = {
    "bootstrap.servers": KAFKA_BROKER,
    "key.serializer": StringSerializer("utf_8"),
}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/ride-request")
def ride_request(data: RideRequestPayload):
    # Convert to dictionary and inject event_type + timestamp
    event = {
        "event_type": "ride_requested",
        "ride_id": str(data.ride_id),
        "timestamp": datetime.now(UTC).isoformat(),
        "pickup": data.pickup,
        "dropoff": data.dropoff,
        "passenger_id": data.passenger_id,
    }

    try:
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
