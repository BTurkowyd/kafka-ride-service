from kafka import KafkaConsumer
import json
import threading

def run_consumer(consumer_id):
    consumer = KafkaConsumer(
        'test-topic-partitioned-2',
        bootstrap_servers='localhost:9092',
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='test-group',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    print(f'[Consumer {consumer_id}] Started')
    for message in consumer:
        print(f'[Consumer {consumer_id}] Partition: {message.partition}, Value: {message.value}')

threads = []
for i in range(3):
    t = threading.Thread(target=run_consumer, args=(i,))
    t.start()
    threads.append(t)
