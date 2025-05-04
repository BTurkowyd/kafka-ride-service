import time
import uuid
import json
from kafka import KafkaProducer
from datetime import datetime, UTC
import math

def interpolate_route(start: tuple[float, float], end: tuple[float, float], steps=10) -> list[tuple]:
    lat_diff = (end[0] - start[0]) / steps
    lon_diff = (end[1] - start[1]) / steps
    return [(round(start[0] + i * lat_diff, 4), round(start[1] + i * lon_diff, 4)) for i in range(steps + 1)]

def euclidean_distance(start: tuple[float, float], end: tuple[float, float]) -> float:
    return math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)

# Kafka setup
producer = KafkaProducer(
    bootstrap_servers='192.168.178.93:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Metadata
driver_id = str(uuid.uuid4())
passenger_id = str(uuid.uuid4())
ride_id = str(uuid.uuid4())

pickup = (52.5200, 13.4050)
dropoff = (52.5000, 13.4500)
route = interpolate_route(pickup, dropoff, steps=15)

# Send ride_requested event
producer.send('uber.ride_requested', {
    "ride_id": ride_id,
    "timestamp": datetime.now(UTC).isoformat(),
    "pickup": pickup,
    "dropoff": dropoff,
    "passenger_id": passenger_id
})
print("[SENT] ride_requested")

time.sleep(1)

# Send ride_started event
producer.send('uber.ride_started', {
    "ride_id": ride_id,
    "timestamp": datetime.now(UTC).isoformat(),
    "driver_id": driver_id,
    "location": pickup
})
print("[SENT] ride_started")

# Send location_update events
for loc in route:
    producer.send('uber.location_update', {
        "ride_id": ride_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "driver_id": driver_id,
        "location": loc
    })
    print(f"[SENT] location_update: {loc}")
    time.sleep(0.8)

# Send ride_completed event
producer.send('uber.ride_completed', {
    "ride_id": ride_id,
    "timestamp": datetime.now(UTC).isoformat(),
    "driver_id": driver_id,
    "location": dropoff,
    "fare": round(euclidean_distance(pickup, dropoff) * 2.4, 2)
})
print("[SENT] ride_completed")

producer.flush()
producer.close()