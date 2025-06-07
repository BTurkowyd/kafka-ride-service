import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import random
import time
import uuid
from datetime import datetime, UTC
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from dotenv import load_dotenv
from producer.modules.geolocation import interpolate_route, random_coord_within


load_dotenv()

PRODUCER_URL = os.getenv("PRODUCER_URL", "http://localhost:8888")
NUM_RIDES = 1000
MAX_WORKERS = 30  # Adjust to control concurrency

# Load known users
drivers = requests.get(f"{PRODUCER_URL}/get-drivers").json().get("driver_ids", [])
passengers = (
    requests.get(f"{PRODUCER_URL}/get-passengers").json().get("passenger_ids", [])
)

print(f"Loaded {len(drivers)} drivers and {len(passengers)} passengers.")


def simulate_ride():
    ride_id = str(uuid.uuid4())
    driver_id = random.choice(drivers)
    passenger_id = random.choice(passengers)
    pickup = random_coord_within()
    dropoff = random_coord_within()
    route = interpolate_route(pickup, dropoff)

    # 1. ride_requested
    try:
        requests.post(
            f"{PRODUCER_URL}/ride-request",
            json={
                "ride_id": ride_id,
                "pickup": pickup,
                "dropoff": dropoff,
                "passenger_id": passenger_id,
            },
        )
    except requests.RequestException as e:
        print(f"Error during ride-request for ride_id {ride_id}: {e}")

    # 2. ride_started
    try:
        requests.post(
            f"{PRODUCER_URL}/ride-started",
            json={
                "ride_id": ride_id,
                "driver_id": driver_id,
                "location": pickup,
            },
        )
    except requests.RequestException as e:
        print(f"Error during ride-started for ride_id {ride_id}: {e}")

    # 3. location updates
    for loc in route:
        try:
            requests.post(
                f"{PRODUCER_URL}/location-update",
                json={
                    "ride_id": ride_id,
                    "driver_id": driver_id,
                    "location": loc,
                },
            )
        except requests.RequestException as e:
            print(f"Error during location-update for ride_id {ride_id}: {e}")
        time.sleep(0.3)  # Lower delay for stress testing

    # 4. ride_completed
    try:
        requests.post(
            f"{PRODUCER_URL}/ride-completed",
            json={
                "ride_id": ride_id,
                "driver_id": driver_id,
                "location": dropoff,
                "pickup": pickup,
                "dropoff": dropoff,
            },
        )
    except requests.RequestException as e:
        print(f"Error during ride-completed for ride_id {ride_id}: {e}")

    return ride_id


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(simulate_ride) for _ in range(NUM_RIDES)]

        for future in as_completed(futures):
            print(f"✅ Completed ride {future.result()}")
