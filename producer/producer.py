import os
import random
import time
import uuid
from datetime import datetime, UTC

from confluent_kafka import SerializingProducer
from confluent_kafka.serialization import StringSerializer
from dotenv import load_dotenv
from modules.geolocation import interpolate_route, haversine_distance, random_coord_within
from modules.postgres import load_ids
from modules.serializer import (
    ride_requested_serializer,
    ride_started_serializer,
    location_update_serializer,
    ride_completed_serializer
)

load_dotenv()

# Config
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")

# Producer config (common)
producer_config = {
    "bootstrap.servers": KAFKA_BROKER,
    "key.serializer": StringSerializer("utf_8"),
    "debug": "all"
}

# Load known users
drivers, passengers = load_ids()

# Main loop
for _ in range(10):  # or while True
    ride_id = str(uuid.uuid4())
    driver_id = random.choice(drivers)
    passenger_id = random.choice(passengers)

    pickup = random_coord_within()
    dropoff = random_coord_within()
    route = interpolate_route(pickup, dropoff)

    now = datetime.now(UTC).isoformat()

    # 1. ride_requested
    ride_requested_data = {
        "event_type": "ride_requested",
        "ride_id": ride_id,
        "timestamp": now,
        "pickup": pickup,
        "dropoff": dropoff,
        "passenger_id": passenger_id
    }

    producer = SerializingProducer({
        **producer_config,
        "value.serializer": ride_requested_serializer
    })
    producer.produce(topic="uber.ride_requested", value=ride_requested_data)
    producer.flush()
    print("[SENT] ride_requested")

    time.sleep(1)

    # 2. ride_started
    ride_started_data = {
        "event_type": "ride_started",
        "ride_id": ride_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "driver_id": driver_id,
        "location": pickup
    }

    producer = SerializingProducer({
        **producer_config,
        "value.serializer": ride_started_serializer
    })
    producer.produce(topic="uber.ride_started", value=ride_started_data)
    producer.flush()
    print("[SENT] ride_started")

    # 3. location_update
    for loc in route:
        location_data = {
            "event_type": "location_update",
            "ride_id": ride_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "driver_id": driver_id,
            "location": loc
        }
        producer = SerializingProducer({
            **producer_config,
            "value.serializer": location_update_serializer
        })
        producer.produce(topic="uber.location_update", value=location_data)
        producer.flush()
        print(f"[SENT] location_update: {loc}")
        time.sleep(0.5)

    # 4. ride_completed
    fare = round(haversine_distance(pickup, dropoff) * 2.4, 2)
    completed_data = {
        "event_type": "ride_completed",
        "ride_id": ride_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "driver_id": driver_id,
        "location": dropoff,
        "fare": fare
    }

    producer = SerializingProducer({
        **producer_config,
        "value.serializer": ride_completed_serializer
    })
    producer.produce(topic="uber.ride_completed", value=completed_data)
    producer.flush()
    print("[SENT] ride_completed")

    print("-" * 40)
    time.sleep(3)