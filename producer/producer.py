import time
import uuid
import json
import random
from kafka import KafkaProducer
from datetime import datetime, UTC
from modules.postgres import load_ids
from modules.geolocation import interpolate_route, haversine_distance, random_coord_within

# Kafka setup
producer = KafkaProducer(
    bootstrap_servers='192.168.178.93:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Load once
drivers, passengers = load_ids()

# Main loop
for _ in range(5):  # or while True
    driver_id = random.choice(drivers)
    passenger_id = random.choice(passengers)
    ride_id = str(uuid.uuid4())

    pickup = random_coord_within()
    dropoff = random_coord_within()
    route = interpolate_route(pickup, dropoff)

    producer.send('uber.ride_requested', {
        "event_type": "ride_requested",
        "ride_id": ride_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "pickup": pickup,
        "dropoff": dropoff,
        "passenger_id": passenger_id
    })
    print("[SENT] ride_requested")

    time.sleep(1)

    producer.send('uber.ride_started', {
        "event_type": "ride_started",
        "ride_id": ride_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "driver_id": driver_id,
        "location": pickup
    })
    print("[SENT] ride_started")

    for loc in route:
        producer.send('uber.location_update', {
            "event_type": "location_update",
            "ride_id": ride_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "driver_id": driver_id,
            "location": loc
        })
        print(f"[SENT] location_update: {loc}")
        time.sleep(0.5)

    distance_km = haversine_distance(pickup, dropoff)
    fare = round(distance_km * 2.4, 2)  # simple multiplier

    producer.send('uber.ride_completed', {
        "event_type": "ride_completed",
        "ride_id": ride_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "driver_id": driver_id,
        "location": dropoff,
        "fare": fare
    })
    print("[SENT] ride_completed")

    print("-" * 40)
    time.sleep(3)

producer.flush()
producer.close()