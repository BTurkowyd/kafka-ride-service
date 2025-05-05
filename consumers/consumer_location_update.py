import json
import uuid
import psycopg2
import psycopg2.extras
from kafka import KafkaConsumer
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
psycopg2.extras.register_uuid()

# Kafka and DB config
KAFKA_TOPIC = "uber.location_update"
BOOTSTRAP_SERVERS = "192.168.178.93:9092"

DB_CONFIG = {
    'dbname': os.getenv("POSTGRES_DB"),
    'user': os.getenv("POSTGRES_USER"),
    'password': os.getenv("POSTGRES_PASSWORD"),
    'host': "192.168.178.93",
    'port': 5432
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# Kafka consumer
consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=BOOTSTRAP_SERVERS,
    group_id='location_update_consumer_group',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    enable_auto_commit=True
)

print("[INFO] location_update consumer is listening...")

for message in consumer:
    data = message.value
    try:
        ride_id = uuid.UUID(data['ride_id'])
        timestamp = datetime.fromisoformat(data['timestamp'])
        lat, lon = data['location']

        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO ride_locations (ride_id, timestamp, lat, lon)
                    VALUES (%s, %s, %s, %s);
                """, (ride_id, timestamp, lat, lon))
        print(f"[INSERTED] location_update for ride_id {ride_id} at {lat}, {lon}")

    except Exception as e:
        print(f"[ERROR] Failed to insert location_update: {e}")
    finally:
        if 'conn' in locals():
            conn.close()