import uuid
import os
import time
from datetime import datetime
from dotenv import load_dotenv
import psycopg2.extras
from confluent_kafka import Consumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from ..helpers import get_db_connection, ride_exists

# Load environment variables
load_dotenv()
psycopg2.extras.register_uuid()

# Config
KAFKA_TOPIC = "uber.ride_completed"
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BROKER", "localhost:9092")
SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8081")
MAX_RETRIES = 10
RETRY_DELAY = 2  # seconds

# Schema Registry
schema_registry_conf = {'url': SCHEMA_REGISTRY_URL}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)
avro_deserializer = AvroDeserializer(schema_registry_client=schema_registry_client)

# Kafka Consumer config
consumer_conf = {
    'bootstrap.servers': BOOTSTRAP_SERVERS,
    'group.id': 'ride_completed_consumer_group',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': True
}

consumer = Consumer(consumer_conf)
consumer.subscribe([KAFKA_TOPIC])


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
    print(f"[Consumer] Listening to topic '{KAFKA_TOPIC}'...")

    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"[Kafka ERROR] {msg.error()}")
            continue

        try:
            event = avro_deserializer(msg.value(), None)
            print(f"[Kafka] Received: {event}")
            update_ride_completed(event)
        except Exception as e:
            print(f"[ERROR] Failed to deserialize or process: {e}")


if __name__ == "__main__":
    consume_ride_completed()