"""
Kafka consumer for processing location update events and storing them in the database.

This module listens to the 'uber.location_update' topic, batches incoming events,
and periodically flushes valid records to the 'ride_locations' table in the database.
Failed or invalid messages are redirected to the Dead Letter Queue (DLQ).
"""

import json
import uuid
import os
import time
import base64
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras

from confluent_kafka import Consumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import SerializationContext, MessageField

from ..helpers import get_db_connection, ride_exists, prepare_original_event
from ..dlq_producer import send_to_dlq

# Load environment variables from .env file for configuration
load_dotenv()
psycopg2.extras.register_uuid()

# Kafka and Schema Registry configuration
KAFKA_TOPIC = "uber.location_update"
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BROKER", "localhost:9092")
SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8081")
BATCH_SIZE = 10
FLUSH_INTERVAL = 5  # seconds
MAX_RETRIES = 20
RETRY_DELAY = 2  # seconds

# Initialize Avro deserializer for message values
schema_registry_conf = {"url": SCHEMA_REGISTRY_URL}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)
avro_deserializer = AvroDeserializer(
    schema_registry_client=schema_registry_client, from_dict=lambda d, _: d
)

# Kafka consumer configuration
consumer_conf = {
    "bootstrap.servers": BOOTSTRAP_SERVERS,
    "group.id": "location_update_consumer_group",
    "auto.offset.reset": "earliest",
    "enable.auto.commit": True,
}

# Create and subscribe the Kafka consumer
consumer = Consumer(consumer_conf)
consumer.subscribe([KAFKA_TOPIC])


def flush_to_db(records):
    """
    Flushes a batch of location update records to the database.

    Args:
        records (list): List of tuples (ride_id, timestamp, lat, lon).
    """
    if not records:
        return

    for attempt in range(MAX_RETRIES):
        try:
            conn = get_db_connection()
            valid_records = []
            # Validate each record by checking if the ride exists
            for rec in records:
                ride_id = rec[0]
                if ride_exists(conn, ride_id):
                    valid_records.append(rec)
                else:
                    print(
                        f"[WARN] ride_id {ride_id} not found. Will retry batch insert..."
                    )

            if valid_records:
                # Insert valid records into the database in bulk
                with conn:
                    with conn.cursor() as cur:
                        psycopg2.extras.execute_values(
                            cur,
                            """
                            INSERT INTO ride_locations (ride_id, timestamp, lat, lon)
                            VALUES %s;
                            """,
                            valid_records,
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
    """
    Main loop for consuming location update events from Kafka,
    batching them, and flushing to the database.
    """
    print(f"[Consumer] Listening to topic '{KAFKA_TOPIC}'...")
    buffer = []
    last_flush_time = time.time()

    while True:
        # Poll for a message from Kafka
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"[Kafka ERROR] {msg.error()}")
            continue

        try:
            # Deserialize the Avro message
            event = avro_deserializer(
                msg.value(), SerializationContext(msg.topic(), MessageField.VALUE)
            )
            if event:
                # Parse and buffer the event data
                ride_id = uuid.UUID(event["ride_id"])
                timestamp = datetime.fromisoformat(event["timestamp"])
                lat, lon = event["location"]
                buffer.append((ride_id, timestamp, lat, lon))
            else:
                # If deserialization fails, raise an error to trigger DLQ
                raise ValueError("Deserialization returned None (schema mismatch?)")

        except Exception as e:
            # On error, send the original message to the Dead Letter Queue
            print(f"[DLQ] Redirecting message to DLQ due to: {e}")

            original_event = prepare_original_event(msg, locals().get("event"))

            send_to_dlq(
                topic=msg.topic(),
                partition=msg.partition(),
                offset=msg.offset(),
                original_event=original_event,
                error_msg=str(e),
            )
            continue

        # Flush the buffer to the database if batch size or interval is reached
        now = time.time()
        if len(buffer) >= BATCH_SIZE or (now - last_flush_time) >= FLUSH_INTERVAL:
            flush_to_db(buffer)
            buffer.clear()
            last_flush_time = now


if __name__ == "__main__":
    # Start the consumer loop if this script is run directly
    consume_location_updates()
