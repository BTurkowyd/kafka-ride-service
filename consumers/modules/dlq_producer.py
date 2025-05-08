import os
from datetime import datetime
from dotenv import load_dotenv

from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import StringSerializer

load_dotenv()

# Config
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8081")
DLQ_TOPIC = "uber.dead_letter"

# Schema Registry setup
schema_registry_conf = {'url': SCHEMA_REGISTRY_URL}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)

with open("schemas/dead_letter_event.avsc", "r") as f:
    schema_str = f.read()

avro_serializer = AvroSerializer(
    schema_registry_client=schema_registry_client,
    schema_str=schema_str,
    to_dict=lambda obj, ctx: obj  # Already dict
)

producer_conf = {
    "bootstrap.servers": KAFKA_BROKER,
    "key.serializer": StringSerializer("utf_8"),
    "value.serializer": avro_serializer
}

dlq_producer = SerializingProducer(producer_conf)


def send_to_dlq(original_event, error_msg, topic, partition, offset):
    event = {
        "topic": topic,
        "partition": partition,
        "offset": offset,
        "event_time": datetime.utcnow().isoformat(),
        "original_event": original_event,
        "error_message": error_msg
    }

    try:
        dlq_producer.produce(topic=DLQ_TOPIC, value=event)
        dlq_producer.flush()
        print(f"[DLQ] Event sent to DLQ: {topic}@{partition}:{offset}")
    except Exception as e:
        print(f"[DLQ ERROR] Failed to send to DLQ: {e}")