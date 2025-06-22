"""
Kafka Avro serializer setup for all ride event topics.

Loads Avro schemas and prepares serializers for each event type.
"""

import os

from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8081")

# Schema Registry Client
schema_registry_conf = {"url": SCHEMA_REGISTRY_URL}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)


def load_schema(path):
    """
    Loads an Avro schema from a file.

    Args:
        path (str): Path to the Avro schema file.

    Returns:
        str: Avro schema as a string.
    """
    with open(path) as f:
        return f.read()


# Load Avro schemas for each event type
ride_requested_schema = load_schema("producer/avro_schemas/ride_requested.avsc")
ride_started_schema = load_schema("producer/avro_schemas/ride_started.avsc")
location_update_schema = load_schema("producer/avro_schemas/location_update.avsc")
ride_completed_schema = load_schema("producer/avro_schemas/ride_completed.avsc")

# Serializer setup per topic
ride_requested_serializer = AvroSerializer(
    schema_registry_client, ride_requested_schema, to_dict=lambda x, _: x
)
ride_started_serializer = AvroSerializer(
    schema_registry_client, ride_started_schema, to_dict=lambda x, _: x
)
location_update_serializer = AvroSerializer(
    schema_registry_client, location_update_schema, to_dict=lambda x, _: x
)
ride_completed_serializer = AvroSerializer(
    schema_registry_client, ride_completed_schema, to_dict=lambda x, _: x
)
