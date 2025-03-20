import requests
from bs4 import BeautifulSoup
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# 현재 파일(parking.py)이 위치한 디렉토리에서 .env 파일 경로 지정
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("API_KEY")
with open("seoul_regions.json", "r", encoding="utf-8") as file:
    seoul_regions = json.load(file)

def get_parking_data(region="여의도"):
    parking_data = []

    for region_code, region_name in seoul_regions.items():
        api_url = f"http://openapi.seoul.go.kr:8088/{api_key}/xml/citydata/1/5/{region_name}/"
        response = requests.get(api_url)

        if response.status_code != 200:
            print(f"❌ API 요청 실패: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, "xml")

        # 지역 정보 추출
        area_name = soup.find("AREA_NM").text if soup.find("AREA_NM") else "정보 없음"
        area_code = soup.find("AREA_CD").text if soup.find("AREA_CD") else "정보 없음"

        # 주차장 정보 파싱
        parking_elements = soup.find_all("PRK_STTS")  # 주차장 정보만 추출

        for prk in parking_elements:
            parking_info = {
                "REGION": area_name,
                "REGION_CODE": area_code,
                "PARKING_NAME": prk.find("PRK_NM").text if prk.find("PRK_NM") else "정보 없음",
                "PARKING_CODE": prk.find("PRK_CD").text if prk.find("PRK_CD") else "정보 없음",
                "TYPE": prk.find("PRK_TYPE").text if prk.find("PRK_TYPE") else "정보 없음",
                "CAPACITY": prk.find("CPCTY").text if prk.find("CPCTY") else "정보 없음",
                "OCCUPIED_SPOTS": prk.find("CUR_PRK_CNT").text if prk.find("CUR_PRK_CNT") else "정보 없음", # 이름 변경
                "LAST_UPDATE": prk.find("CUR_PRK_TIME").text if prk.find("CUR_PRK_TIME") else "정보 없음",
                "IS_REALTIME_STATUS_PROVIDED": prk.find("CUR_PRK_YN").text if prk.find("CUR_PRK_YN") else "정보 없음",
                "PAY_YN": prk.find("PAY_YN").text if prk.find("PAY_YN") else "정보 없음",
                "BASE_RATE": prk.find("RATES").text if prk.find("RATES") else "정보 없음",
                "BASE_TIME": prk.find("TIME_RATES").text if prk.find("TIME_RATES") else "정보 없음",
                "ADD_RATE": prk.find("ADD_RATES").text if prk.find("ADD_RATES") else "정보 없음",
                "ADD_TIME": prk.find("ADD_TIME_RATES").text if prk.find("ADD_TIME_RATES") else "정보 없음",
                "LATITUDE": prk.find("LAT").text if prk.find("LAT") else "정보 없음",
                "LONGITUDE": prk.find("LNG").text if prk.find("LNG") else "정보 없음",
            }
            parking_data.append(parking_info)

        with open("parking_data.json", "w", encoding="utf-8") as file:
            json.dump(parking_data, file, indent=4, ensure_ascii=False)

    return parking_data