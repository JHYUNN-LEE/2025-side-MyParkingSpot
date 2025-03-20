import streamlit as st
import requests
import json
import os

# FastAPI 서버 주소
API_URL = os.getenv("API_URL", "http://fastapi:8000")

st.title("🚗 실시간 주차장 현황 대시보드")

# JSON 파일에서 지역 리스트 불러오기
base_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(base_dir, "seoul_regions.json")
with open(json_path, "r", encoding="utf-8") as file:
    seoul_regions = json.load(file)

# fastAPI에서 사용 가능한 POI 코드 목록 가져오기
available_response = requests.get(f"{API_URL}/available_regions")
if available_response.status_code == 200:
    available_poi_codes = available_response.json()
else:
    available_poi_codes = []
    st.error("사용 가능한 지역 데이터를 가져오지 못했습니다.")

# seoul_regions에서 redis에 데이터가 있는 지역만 필터링 (예: {"여의도": "POI072", ...})
filtered_regions = {region: code for region, code in seoul_regions.items() if code in available_poi_codes}
if not filtered_regions:
    st.warning("현재 실시간 데이터가 있는 지역이 없습니다.")
else:
    # 사용자 입력: 드롭다운에서 지역 선택
    selected_region = st.selectbox("지역을 선택하세요", list(filtered_regions.keys()))

    if st.button("검색"):
        # 선택한 지역명으로부터 코드 조회
        selected_code = filtered_regions[selected_region]
        
        response = requests.get(f"{API_URL}/parking", params={"keyword": selected_code})

        if response.status_code == 200:
            data = response.json()
            if data:
                st.write(f"📍{selected_region} 지역의 주차장 상태:")
                for name, available_spots in data.items():
                    st.write(f"**{name}** → 남은 자리: {available_spots} 대")
            else:
                st.write(f"❌ '{selected_region}' 지역에 대한 데이터가 없습니다.")
        else:
            st.write("❌ 서버 응답 오류")