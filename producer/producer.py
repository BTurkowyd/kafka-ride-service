from kafka import KafkaProducer
import time
import json

producer = KafkaProducer(
    bootstrap_servers='192.168.178.93:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

topic = 'test-topic-partitioned-2'

for i in range(20):
    event = {'event_id': i, 'message': f'Event {i}'}
    producer.send(topic, value=event)
    print(f'Sent: {event}')
    time.sleep(1)

producer.flush()
producer.close()
