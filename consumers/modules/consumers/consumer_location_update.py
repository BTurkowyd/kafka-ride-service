import json
import uuid
import time
import psycopg2
import psycopg2.extras
from kafka import KafkaConsumer
from datetime import datetime
from dotenv import load_dotenv
from ..helpers import get_db_connection, ride_exists

# Load environment variables
load_dotenv()
psycopg2.extras.register_uuid()

# Config
KAFKA_TOPIC = "uber.location_update"
BOOTSTRAP_SERVERS = "192.168.178.93:9092"
BATCH_SIZE = 10
FLUSH_INTERVAL = 5  # seconds
MAX_RETRIES = 5
RETRY_DELAY = 1  # seconds


def flush_to_db(records):
    if not records:
        return

    for attempt in range(MAX_RETRIES):
        try:
            conn = get_db_connection()
            valid_records = []
            for rec in records:
                ride_id = rec[0]
                if ride_exists(conn, ride_id):
                    valid_records.append(rec)
                else:
                    print(f"[WARN] ride_id {ride_id} not found. Will retry batch insert...")

            if valid_records:
                with conn:
                    with conn.cursor() as cur:
                        psycopg2.extras.execute_values(
                            cur,
                            """
                            INSERT INTO ride_locations (ride_id, timestamp, lat, lon)
                            VALUES %s;
                            """,
                            valid_records
                        )
                print(f"[INFO] Flushed {len(valid_records)} location updates to DB.")
                return
            else:
                print("[WARN] No valid records yet. Retrying...")
        except Exception as e:
            print(f"[ERROR] Batch insert failed: {e}")
        finally:
            conn.close()

        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY)
        else:
            print("[ERROR] Max retries reached. Skipping batch.")

def consume_location_updates():
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id='location_update_consumer_group',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=True
    )

    print(f"[Consumer] Listening to topic '{KAFKA_TOPIC}'...")

    buffer = []
    last_flush_time = time.time()

    for message in consumer:
        event = message.value
        try:
            ride_id = uuid.UUID(event['ride_id'])
            timestamp = datetime.fromisoformat(event['timestamp'])
            lat, lon = event['location']
            buffer.append((ride_id, timestamp, lat, lon))
        except Exception as e:
            print(f"[WARN] Skipping invalid record: {e}")
            continue

        now = time.time()
        if len(buffer) >= BATCH_SIZE or (now - last_flush_time) >= FLUSH_INTERVAL:
            flush_to_db(buffer)
            buffer.clear()
            last_flush_time = now

if __name__ == "__main__":
    consume_location_updates()