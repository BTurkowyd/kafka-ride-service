import os
import json
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras

from confluent_kafka import Consumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import SerializationContext, MessageField

from ..helpers import get_db_connection

# Load env vars
load_dotenv()
psycopg2.extras.register_uuid()

# Kafka & Registry config
KAFKA_TOPIC = "uber.dead_letter"
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BROKER", "localhost:9092")
SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8081")


# Schema Registry
schema_registry_conf = {'url': SCHEMA_REGISTRY_URL}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)
avro_deserializer = AvroDeserializer(
    schema_registry_client=schema_registry_client,
    from_dict=lambda d, _: d
)

# Kafka Consumer config
consumer_conf = {
    'bootstrap.servers': BOOTSTRAP_SERVERS,
    'group.id': 'dlq_consumer_group',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': True
}

consumer = Consumer(consumer_conf)
consumer.subscribe([KAFKA_TOPIC])

def insert_dead_letter(event):
    try:
        topic = event["topic"]
        partition = event["partition"]
        offset = event["offset"]
        event_time = datetime.fromisoformat(event["event_time"])
        error_message = event["error_message"]

        try:
            original_event = json.loads(event["original_event"])
        except json.JSONDecodeError:
            original_event = event["original_event"]

        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO dead_letter_events (
                        topic, partition, "offset", event_time,
                        original_event, error_message
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    topic, partition, offset, event_time,
                    json.dumps(original_event), error_message
                ))
        print(f"[DB] Inserted DLQ record from topic '{topic}' @ offset {offset}")
    except Exception as e:
        print(f"[ERROR] Failed to insert DLQ record: {e}")

def consume_dlq():
    print(f"[Consumer] Listening to DLQ topic '{KAFKA_TOPIC}'...")

    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"[Kafka ERROR] {msg.error()}")
            continue

        try:
            event = avro_deserializer(
                msg.value(),
                SerializationContext(msg.topic(), MessageField.VALUE)
            )
            if event:
                print(f"[Kafka] DLQ Event received: {event['error_message']}")
                insert_dead_letter(event)
            else:
                print(f"[WARN] DLQ event could not be deserialized: None returned")
        except Exception as e:
            print(f"[ERROR] Failed to process DLQ message: {e}")

if __name__ == "__main__":
    consume_dlq()