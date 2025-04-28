from kafka import KafkaProducer
import time
import json

producer = KafkaProducer(
    bootstrap_servers='192.168.178.93:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

topic_name = 'test-topic'

for i in range(3600):
    # print current time with seconds accuracy
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(f'Producing message: {current_time}')
    producer.send(topic_name, value=current_time)
    time.sleep(1)  # Sleep for 1 second between messages

producer.flush()
producer.close()
