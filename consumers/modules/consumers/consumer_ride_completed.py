import json
import uuid
import time
import psycopg2.extras
from kafka import KafkaConsumer
from datetime import datetime
from dotenv import load_dotenv
from ..helpers import get_db_connection, ride_exists

# Load environment variables
load_dotenv()
psycopg2.extras.register_uuid()

# Config
KAFKA_TOPIC = "uber.ride_completed"
BOOTSTRAP_SERVERS = "192.168.178.93:9092"
MAX_RETRIES = 10
RETRY_DELAY = 2  # in seconds


def update_ride_completed(event):
    ride_id = uuid.UUID(event["ride_id"])
    timestamp = datetime.fromisoformat(event["timestamp"])
    dropoff_lat, dropoff_lon = event["location"]
    fare = float(event["fare"])

    for attempt in range(MAX_RETRIES):
        conn = get_db_connection()
        try:
            if ride_exists(conn, ride_id):
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE rides
                            SET
                                dropoff_time = %s,
                                dropoff_lat = %s,
                                dropoff_lon = %s,
                                fare = %s,
                                status = 'completed'
                            WHERE ride_id = %s;
                        """, (timestamp, dropoff_lat, dropoff_lon, fare, ride_id))
                print(f"[DB] Ride completed for ride_id {ride_id}")
                return
            else:
                if attempt < MAX_RETRIES - 1:
                    print(f"[Retry] ride_id {ride_id} not found, retrying ({attempt + 1})...")
                    time.sleep(RETRY_DELAY)
                else:
                    print(f"[ERROR] ride_id {ride_id} not found after {MAX_RETRIES} retries.")
        except Exception as e:
            print(f"[ERROR] Failed to update ride_completed: {e}")
        finally:
            conn.close()

def consume_ride_completed():
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id='ride_completed_consumer_group',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=True
    )

    print(f"[Consumer] Listening to topic '{KAFKA_TOPIC}'...")

    for message in consumer:
        event = message.value
        print(f"[Kafka] Received: {event}")
        update_ride_completed(event)

if __name__ == "__main__":
    consume_ride_completed()