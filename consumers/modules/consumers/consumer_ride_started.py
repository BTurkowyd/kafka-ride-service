import json
import uuid
import time
import psycopg2.extras
from kafka import KafkaConsumer
from datetime import datetime
from dotenv import load_dotenv
from ..helpers import get_db_connection, ride_exists

load_dotenv()
psycopg2.extras.register_uuid()

# Kafka & DB config
KAFKA_TOPIC = "uber.ride_started"
BOOTSTRAP_SERVERS = "192.168.178.93:9092"
MAX_RETRIES = 10
RETRY_DELAY = 2  # seconds


def update_ride(event):
    ride_id = uuid.UUID(event["ride_id"])
    driver_id = event["driver_id"]
    timestamp = datetime.fromisoformat(event["timestamp"])
    pickup_lat, pickup_lon = event["location"]

    for attempt in range(MAX_RETRIES):
        conn = get_db_connection()
        try:
            if ride_exists(conn, ride_id):
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE rides
                            SET
                                driver_id = %s,
                                pickup_time = %s,
                                pickup_lat = %s,
                                pickup_lon = %s,
                                status = 'in_progress'
                            WHERE ride_id = %s;
                        """, (driver_id, timestamp, pickup_lat, pickup_lon, ride_id))
                print(f"[DB] Ride updated for ride_id {ride_id}")
                return
            else:
                if attempt < MAX_RETRIES - 1:
                    print(f"[Retry] ride_id {ride_id} not yet in DB, retrying ({attempt + 1})...")
                    time.sleep(RETRY_DELAY)
                else:
                    print(f"[ERROR] ride_id {ride_id} not found after {MAX_RETRIES} retries.")
        except Exception as e:
            print(f"[ERROR] Failed to update ride: {e}")
        finally:
            conn.close()

def consume_ride_started():
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id='ride_started_consumer_group',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=True
    )

    print(f"[Consumer] Listening to topic '{KAFKA_TOPIC}'...")

    for message in consumer:
        event = message.value
        print(f"[Kafka] Received: {event}")
        update_ride(event)

# Optional direct execution
if __name__ == "__main__":
    consume_ride_started()