import uuid
import os
import time
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
from confluent_kafka import Consumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from ..helpers import get_db_connection, ride_exists

# Load environment variables
load_dotenv()
psycopg2.extras.register_uuid()

# Config
KAFKA_TOPIC = "uber.location_update"
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BROKER", "localhost:9092")
SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8081")
BATCH_SIZE = 10
FLUSH_INTERVAL = 5  # seconds
MAX_RETRIES = 20
RETRY_DELAY = 2  # seconds

# Avro setup
schema_registry_conf = {'url': SCHEMA_REGISTRY_URL}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)
avro_deserializer = AvroDeserializer(schema_registry_client=schema_registry_client)


# Kafka Consumer config
consumer_conf = {
    'bootstrap.servers': BOOTSTRAP_SERVERS,
    'group.id': 'location_update_consumer_group',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': True
}

consumer = Consumer(consumer_conf)
consumer.subscribe([KAFKA_TOPIC])


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
    print(f"[Consumer] Listening to topic '{KAFKA_TOPIC}'...")
    buffer = []
    last_flush_time = time.time()

    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"[Kafka ERROR] {msg.error()}")
            continue

        try:
            event = avro_deserializer(msg.value(), None)
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