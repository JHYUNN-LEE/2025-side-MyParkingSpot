import redis

# ✅ Redis 연결 (decode_responses=True로 한글 정상 출력)
redis_client = redis.StrictRedis(host="redis", port=6379, db=0, decode_responses=True, charset="utf-8")

# ✅ Redis에 저장된 모든 키 가져오기
keys = redis_client.keys("*")

print("📌 Redis 저장 데이터 목록")
for key in keys:
    value = redis_client.get(key)
    print(f"{key}: {value}")
