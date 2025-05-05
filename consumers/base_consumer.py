from kafka import KafkaConsumer
import json
import os
from dotenv import load_dotenv

load_dotenv()

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "192.168.178.93:9092")

def start_consumer(topic_name: str, group_id: str):
    consumer = KafkaConsumer(
        topic_name,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id=group_id,
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )

    print(f"[Consumer: {group_id}] Listening to topic: {topic_name}")

    for message in consumer:
        print(f"[{group_id}] Topic: {message.topic} | Partition: {message.partition} | Value: {message.value}")