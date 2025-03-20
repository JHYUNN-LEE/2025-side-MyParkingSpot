import json
import redis
from kafka import KafkaConsumer

# Kafka 설정
TOPIC = "parking_status"
BOOTSTRAP_SERVERS = "kafka1:29092,kafka2:29092,kafka3:29092"

# Redis 연결
redis_client = redis.StrictRedis(host="redis", port=6379, db=0, decode_responses=True, charset="utf-8")

# Kafka Consumer 설정
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=BOOTSTRAP_SERVERS.split(","),
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    group_id="parking_consumer_group"
)

print("🚀 Kafka Consumer 시작됨...")

for message in consumer:
    parking_data = message.value
    # 실시간 상태 제공 여부 확인. 만약 실시간 데이터가 아닌 경우, 저장하지 않음 (Frontend에서 표시되지 않음)
    is_realtime = parking_data.get("IS_REALTIME_STATUS_PROVIDED", "N")
    if is_realtime != "Y":
        # print(f"[제외] {parking_name} → 실시간 데이터가 아님")
        continue

    region = parking_data.get("REGION", "알 수 없음")  # 🔥 지역 추가
    region_code = parking_data.get("REGION_CODE", "알 수 없음")  # 🔥 지역 코드 추가
    parking_name = parking_data.get("PARKING_NAME", "알 수 없음")

    redis_key = f"{region}_{region_code}_{parking_name}" # ✅ Redis 키에 지역명 & 코드 포함

    # 주차 가능한 자리 계산 (capacity - occupied_spots). occupied_spots 새 필드 추가. 새 필드가 없으면 기존 필드(`AVAILABLE_SPOTS`) 사용
    capacity = int(parking_data.get("CAPACITY", "0"))
    occupied_spots = int(parking_data.get("OCCUPIED_SPOTS", "0"))
    available_spots = max(0, capacity - occupied_spots) # 음수 방지

    # Redis에서 기존 데이터 조회
    prev_spots = redis_client.get(redis_key)

    if prev_spots is None or prev_spots == '':
        prev_spots = 0
    if int(prev_spots) != int(available_spots):
        # 변경 사항이 있는 경우 Redis 업데이트 후 처리
        redis_client.set(redis_key, available_spots)
        print(f"🔄 [변경 감지] {redis_key} → 주차 가능 공간: {prev_spots} -> {available_spots}")
    else:
        print(f"✅ [변경 없음] {redis_key}: {available_spots} 대 가능")