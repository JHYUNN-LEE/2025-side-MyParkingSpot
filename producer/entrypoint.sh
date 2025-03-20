#!/bin/sh
set -e

# Kafka 준비 상태 확인
echo "Waiting for Kafka to be ready..."
/usr/local/bin/dockerize -wait tcp://kafka1:29092 -timeout 60s

echo "Kafka is ready! Running producer..."
python producer.py
