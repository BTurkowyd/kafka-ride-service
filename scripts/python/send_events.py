import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import random
import time
import uuid
from datetime import datetime, UTC

import requests
from dotenv import load_dotenv
from producer.modules.geolocation import (
    interpolate_route,
    random_coord_within,
)
from producer.modules.postgres import load_ids

load_dotenv()

# Base URL of the FastAPI Kafka producer
PRODUCER_URL = os.getenv("PRODUCER_URL", "http://localhost:8888")

# Load known users
drivers = requests.get(f"{PRODUCER_URL}/get-drivers").json().get("driver_ids", [])
passengers = (
    requests.get(f"{PRODUCER_URL}/get-passengers").json().get("passenger_ids", [])
)

print(f"Loaded {drivers} drivers and {passengers} passengers.")

# Main simulation loop
for _ in range(10):
    ride_id = str(uuid.uuid4())
    driver_id = random.choice(drivers)
    passenger_id = random.choice(passengers)

    pickup = random_coord_within()
    dropoff = random_coord_within()
    route = interpolate_route(pickup, dropoff)

    now = datetime.now(UTC).isoformat()

    # 1. Send ride_requested
    ride_requested_data = {
        "ride_id": ride_id,
        "pickup": pickup,
        "dropoff": dropoff,
        "passenger_id": passenger_id,
    }
    response = requests.post(f"{PRODUCER_URL}/ride-request", json=ride_requested_data)
    print(f"[SENT] ride_requested | Status: {response.status_code}")

    time.sleep(1)

    # 2. Send ride_started
    ride_started_data = {"ride_id": ride_id, "driver_id": driver_id, "location": pickup}
    response = requests.post(f"{PRODUCER_URL}/ride-started", json=ride_started_data)
    print(f"[SENT] ride_started | Status: {response.status_code}")

    # 3. Send location_update
    for loc in route:
        location_data = {"ride_id": ride_id, "driver_id": driver_id, "location": loc}
        response = requests.post(f"{PRODUCER_URL}/location-update", json=location_data)
        print(f"[SENT] location_update {loc} | Status: {response.status_code}")
        time.sleep(0.5)

    # 4. Send ride_completed
    completed_data = {
        "ride_id": ride_id,
        "driver_id": driver_id,
        "location": dropoff,
        "pickup": pickup,
        "dropoff": dropoff,
    }
    response = requests.post(f"{PRODUCER_URL}/ride-completed", json=completed_data)
    print(f"[SENT] ride_completed | Status: {response.status_code}")

    print("-" * 40)
    time.sleep(3)
