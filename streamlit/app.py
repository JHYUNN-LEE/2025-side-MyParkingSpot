import streamlit as st
import requests
import json
import os
# from dotenv import load_dotenv
import pandas as pd
import psycopg2
import altair as alt

# load_dotenv(".env")

API_URL = os.getenv("API_URL", "http://fastapi:8000") # FastAPI 서버

tab1, tab2 = st.tabs(["실시간 현황", "시간대별 트렌드 분석"])

with tab1:
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

    # seoul_regions에서 redis에 데이터가 있는 지역만 필터링
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
                    st.write(f"📍{selected_region} 지역의 주차장 현황:")
                    for name, available_spots in data.items():
                        st.write(f"**{name}** → 남은 자리: {available_spots} 대")
                else:
                    st.write(f"❌ '{selected_region}' 지역에 대한 데이터가 없습니다.")
            else:
                st.write("❌ 서버 응답 오류")
with tab2:
    st.subheader("⏱️ [전체 지역 평균]시간대별 주차 가능 공간 트렌드 ")

    # PostgreSQL 연결 정보
    PG_HOST = os.getenv("PG_HOST", "postgres")
    PG_PORT = os.getenv("PG_PORT", 5432)
    PG_DB = os.getenv("PG_DB", "sidebase")
    PG_USER = os.getenv("PG_USER", "postgres")
    PG_PWD = os.getenv("PG_PWD", "postgres.side!")

    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            dbname=PG_DB,
            user=PG_USER,
            password=PG_PWD
        )
        query = """
            SELECT hour, region, AVG(avg_available_spots) AS total_avg_available_spots
            FROM parking.parking_hourly_avg
            GROUP BY hour, region
            ORDER BY hour, region ASC
        """
        df = pd.read_sql(query, conn)
        conn.close()

        if df.empty:
            st.warning("❌ 아직 집계된 트렌드 데이터가 없습니다.")
        else:
            df['hour'] = pd.to_datetime(df['hour'])

            chart = alt.Chart(df).mark_line(point=True).encode(
                x=alt.X('hour:T', title='시간대'),
                y=alt.Y('total_avg_available_spots:Q', title='전체 지역 평균 주차 가능 공간'),
                tooltip=['hour', 'total_avg_available_spots']
            ).properties(
                width=700,
                height=400,
                title="⏳ 전체 지역 기준 시간대별 평균 주차 가능 공간"
            )

            st.altair_chart(chart)

    except Exception as e:
        st.error(f"Postgres 연결 또는 쿼리 오류: {e}")

    st.subheader("🗺️ 지역별 주차 가능 트렌드")

    region_options = df['region'].unique()
    selected_regions = st.multiselect("지역을 선택하세요", region_options, default=region_options[:1])

    if selected_regions:
        filtered_df = df[df['region'].isin(selected_regions)]

        chart = alt.Chart(filtered_df).mark_line(point=True).encode(
            x=alt.X('hour:T', title='시간대'),
            y=alt.Y('total_avg_available_spots:Q', title='주차 가능 공간'),
            color='region:N',
            tooltip=['hour', 'region', 'total_avg_available_spots']
        ).properties(
            width=700,
            height=400,
            title="⏱️ 선택 지역별 시간대별 주차 가능 공간"
        )

        st.altair_chart(chart)