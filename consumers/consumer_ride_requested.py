import json
import uuid

import psycopg2
import psycopg2.extras
from kafka import KafkaConsumer
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
psycopg2.extras.register_uuid()

# Kafka & DB config
KAFKA_TOPIC = "uber.ride_requested"
BOOTSTRAP_SERVERS = "192.168.178.93:9092"

DB_CONFIG = {
    'dbname': os.getenv("POSTGRES_DB"),
    'user': os.getenv("POSTGRES_USER"),
    'password': os.getenv("POSTGRES_PASSWORD"),
    'host': "192.168.178.93",
    'port': 5432
}

def create_connection():
    return psycopg2.connect(**DB_CONFIG)

def insert_ride(event):
    ride_id = uuid.UUID(event["ride_id"])
    passenger_id = event["passenger_id"]
    request_time = datetime.fromisoformat(event["timestamp"])
    pickup_lat, pickup_lon = event["pickup"]
    dropoff_lat, dropoff_lon = event["dropoff"]

    conn = create_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO rides (
                        ride_id, passenger_id, request_time,
                        pickup_lat, pickup_lon,
                        dropoff_lat, dropoff_lon,
                        status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    ride_id,
                    passenger_id,
                    request_time,
                    pickup_lat,
                    pickup_lon,
                    dropoff_lat,
                    dropoff_lon,
                    'in_progress'
                ))
                print(f"[DB] Ride inserted for passenger {passenger_id}")
    except Exception as e:
        print(f"[ERROR] Failed to insert ride: {e}")
    finally:
        conn.close()

def main():
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="ride_requested_group",
        value_deserializer=lambda x: json.loads(x.decode("utf-8"))
    )

    print(f"[Consumer] Listening to topic '{KAFKA_TOPIC}'...")
    for message in consumer:
        event = message.value
        print(f"[Kafka] Received: {event}")
        insert_ride(event)

if __name__ == "__main__":
    main()