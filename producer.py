from kafka import KafkaProducer
import time
import json

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

topic_name = 'test-topic'

for i in range(100):
    event = {'event_id': i, 'message': f'Event number {i}'}
    producer.send(topic_name, value=event)
    print(f'Sent: {event}')
    time.sleep(0.05)

producer.flush()
producer.close()
