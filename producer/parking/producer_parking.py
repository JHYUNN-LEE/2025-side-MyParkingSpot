import os
import time
import json
from kafka import KafkaProducer
from parking import get_parking_data 

# Kafka Producer 설정
producer = KafkaProducer(
    bootstrap_servers="kafka1:29092,kafka2:29092,kafka3:29092",
    value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8")
)

TOPIC = "parking_status"

def fetch_and_send_data():
    print("🔄 주차장 데이터 수집 시작...")

    while True:
        # ✅ 크롤링 실행하여 데이터 가져오기
        parking_data = get_parking_data()

        if parking_data:
            for record in parking_data:
                producer.send(TOPIC, record)
            producer.flush()
            print(f"✅ {len(parking_data)}건의 데이터 Kafka로 전송 완료!")

        # ⏳ 30초마다 데이터 수집 (실시간 처리)
        time.sleep(30)

fetch_and_send_data()