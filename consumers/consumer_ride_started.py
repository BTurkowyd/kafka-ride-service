import json
import uuid

import psycopg2
import psycopg2.extras
from kafka import KafkaConsumer
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
psycopg2.extras.register_uuid()

# Kafka & DB config
KAFKA_TOPIC = "uber.ride_started"
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

consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=BOOTSTRAP_SERVERS,
    group_id='ride_started_consumer_group',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    enable_auto_commit=True
)

print("[INFO] ride_started consumer is listening...")

for message in consumer:
    data = message.value
    ride_id = uuid.UUID(data['ride_id'])
    driver_id = data['driver_id']
    timestamp = datetime.fromisoformat(data['timestamp'])
    pickup_lat, pickup_lon = data['location']

    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE rides
                    SET
                        driver_id = %s,
                        pickup_time = %s,
                        pickup_lat = %s,
                        pickup_lon = %s,
                        status = 'in_progress'
                    WHERE ride_id = %s;
                """, (driver_id, timestamp, pickup_lat, pickup_lon, ride_id))
        print(f"Updated ride_started for ride_id {ride_id}")
    except Exception as e:
        print(f"Error updating ride_started: {e}")
    finally:
        conn.close()