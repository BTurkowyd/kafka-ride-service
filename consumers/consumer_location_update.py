import json
import uuid
import psycopg2
import psycopg2.extras
from kafka import KafkaConsumer
from datetime import datetime
from dotenv import load_dotenv
import os
import time

# Load environment variables
load_dotenv()
psycopg2.extras.register_uuid()

KAFKA_TOPIC = "uber.location_update"
BOOTSTRAP_SERVERS = "192.168.178.93:9092"

DB_CONFIG = {
    'dbname': os.getenv("POSTGRES_DB"),
    'user': os.getenv("POSTGRES_USER"),
    'password': os.getenv("POSTGRES_PASSWORD"),
    'host': "192.168.178.93",
    'port': 5432
}

BATCH_SIZE = 10
FLUSH_INTERVAL = 5  # seconds

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

buffer = []
last_flush_time = time.time()

consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=BOOTSTRAP_SERVERS,
    group_id='location_update_consumer_group',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    enable_auto_commit=True
)

print("[INFO] location_update consumer (batched) is listening...")

def flush_to_db(records):
    if not records:
        return

    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                psycopg2.extras.execute_values(
                    cur,
                    """
                    INSERT INTO ride_locations (ride_id, timestamp, lat, lon)
                    VALUES %s;
                    """,
                    records
                )
        print(f"[INFO] Flushed {len(records)} location updates to DB.")
    except Exception as e:
        print(f"[ERROR] Failed to batch insert: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

for message in consumer:
    data = message.value
    try:
        ride_id = uuid.UUID(data['ride_id'])
        timestamp = datetime.fromisoformat(data['timestamp'])
        lat, lon = data['location']
        buffer.append((ride_id, timestamp, lat, lon))
    except Exception as e:
        print(f"[WARN] Skipping invalid record: {e}")
        continue

    now = time.time()
    if len(buffer) >= BATCH_SIZE or (now - last_flush_time) >= FLUSH_INTERVAL:
        flush_to_db(buffer)
        buffer.clear()
        last_flush_time = now