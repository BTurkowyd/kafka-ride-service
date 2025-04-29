#!/bin/bash

docker exec kafka-training-kafka-1 \
  kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --replication-factor 1 \
  --partitions 3 \
  --topic test-topic-partitioned-2
