import uuid
import os
from datetime import datetime
from dotenv import load_dotenv
import psycopg2.extras

from confluent_kafka import DeserializingConsumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import StringDeserializer

from ..helpers import get_db_connection

# Load env
load_dotenv()
psycopg2.extras.register_uuid()

# Config
KAFKA_TOPIC = "uber.ride_requested"
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BROKER", "localhost:9092")
SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8081")

# Schema Registry client
schema_registry_conf = {'url': SCHEMA_REGISTRY_URL}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)

# Avro deserializer with from_dict passthrough
avro_deserializer = AvroDeserializer(
    schema_registry_client=schema_registry_client,
    schema_str=None,
    from_dict=lambda d, _: d
)

# Kafka consumer config with key + value deserializers
consumer_conf = {
    'bootstrap.servers': BOOTSTRAP_SERVERS,
    'key.deserializer': StringDeserializer('utf_8'),
    'value.deserializer': avro_deserializer,
    'group.id': 'ride_requested_group',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': True
}

def insert_ride(event):
    ride_id = uuid.UUID(event["ride_id"])
    passenger_id = event["passenger_id"]
    request_time = datetime.fromisoformat(event["timestamp"])
    pickup_lat, pickup_lon = event["pickup"]
    dropoff_lat, dropoff_lon = event["dropoff"]

    conn = get_db_connection()
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

def consume_ride_requested():
    consumer = DeserializingConsumer(consumer_conf)
    consumer.subscribe([KAFKA_TOPIC])

    print(f"[Consumer] Listening to topic '{KAFKA_TOPIC}'...")

    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"[ERROR] Kafka error: {msg.error()}")
            continue

        event = msg.value()
        if event is not None:
            print(f"[Kafka] Received: {event}")
            insert_ride(event)
        else:
            print("[WARN] Received null/invalid event.")

if __name__ == "__main__":
    consume_ride_requested()