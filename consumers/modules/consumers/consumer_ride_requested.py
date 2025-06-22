"""
Kafka consumer for processing ride requested events.

This module listens to the 'uber.ride_requested' topic, inserts new ride records into the database,
and sends failed or invalid messages to the Dead Letter Queue (DLQ).
"""

import os
import uuid
from datetime import datetime
import base64

import psycopg2.extras
from confluent_kafka import DeserializingConsumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import StringDeserializer
from dotenv import load_dotenv
from ..dlq_producer import send_to_dlq
from ..helpers import get_db_connection, prepare_original_event

# Load environment variables
load_dotenv()
psycopg2.extras.register_uuid()

# Kafka and Schema Registry configuration
KAFKA_TOPIC = "uber.ride_requested"
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BROKER", "localhost:9092")
SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8081")

# Schema Registry client
schema_registry_conf = {"url": SCHEMA_REGISTRY_URL}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)

# Avro deserializer
avro_deserializer = AvroDeserializer(
    schema_registry_client=schema_registry_client,
    schema_str=None,
    from_dict=lambda d, _: d,
)

# Kafka consumer configuration
consumer_conf = {
    "bootstrap.servers": BOOTSTRAP_SERVERS,
    "key.deserializer": StringDeserializer("utf_8"),
    "value.deserializer": avro_deserializer,
    "group.id": "ride_requested_group",
    "auto.offset.reset": "earliest",
    "enable.auto.commit": True,
}


def insert_ride(event):
    """
    Inserts a new ride record into the database.

    Args:
        event (dict): The ride requested event data.
    """
    ride_id = uuid.UUID(event["ride_id"])
    passenger_id = event["passenger_id"]
    request_time = datetime.fromisoformat(event["timestamp"])
    pickup_lat, pickup_lon = event["pickup"]
    dropoff_lat, dropoff_lon = event["dropoff"]

    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO rides (
                        ride_id, passenger_id, request_time,
                        pickup_lat, pickup_lon,
                        dropoff_lat, dropoff_lon,
                        status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                    (
                        ride_id,
                        passenger_id,
                        request_time,
                        pickup_lat,
                        pickup_lon,
                        dropoff_lat,
                        dropoff_lon,
                        "in_progress",
                    ),
                )
                print(f"[DB] Ride inserted for passenger {passenger_id}")
    except Exception as e:
        raise e
    finally:
        conn.close()


def consume_ride_requested():
    """
    Main loop for consuming ride requested events from Kafka and inserting into the database.
    """
    consumer = DeserializingConsumer(consumer_conf)
    consumer.subscribe([KAFKA_TOPIC])

    print(f"[Consumer] Listening to topic '{KAFKA_TOPIC}'...")

    while True:
        msg = consumer.poll(1.0)
        if msg is None or msg.error():
            continue

        try:
            event = msg.value()

            if event is None:
                raise ValueError("Deserialization returned None (schema mismatch?)")

            print(f"[Kafka] Received: {event}")
            insert_ride(event)

        except Exception as e:
            print(f"[DLQ] Redirecting message due to error: {e}")

            original_event = prepare_original_event(msg, locals().get("event"))

            send_to_dlq(
                original_event=original_event,
                error_msg=str(e),
                topic=msg.topic(),
                partition=msg.partition(),
                offset=msg.offset(),
            )
            print(f"[DLQ] Sent failed event to DLQ: {e}")


if __name__ == "__main__":
    consume_ride_requested()
