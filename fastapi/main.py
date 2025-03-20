from fastapi import FastAPI, Query
import redis
import json
import os

app = FastAPI()

# ✅ Redis 연결
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True, charset="utf-8")

@app.get("/parking")
def get_parking_status(keyword: str = Query("여의도", description="검색할 지역을 입력하세요")):
    """ Redis에 저장된 모든 주차장 데이터를 반환하는 API """
    # keys = redis_client.keys("*") # 저장된 모든 키 조회
    keys = redis_client.keys(f"*_{keyword}_*")
    parking_data = {}

    for key in keys:
        parking_data[key] = redis_client.get(key)

    return parking_data

@app.get("/available_regions")
def available_regions():
    """Redis에 저장된 데이터의 POI 코드 목록 반환"""
    keys = redis_client.keys("*")
    available_poi_codes = set()
    for key in keys:
        # 예: "여의도_POI072_여의도한강5주차장(성모병원앞)"에서 두번째 요소가 POI 코드임
        parts = key.split('_')
        if len(parts) >= 2:
            available_poi_codes.add(parts[1])
    return list(available_poi_codes)

