# 🚗 실시간 주차장 데이터 처리 시스템 및 대시보드

이 프로젝트는 **Kafka, Spark Streaming, Redis**를 활용하여 **서울시 주차장 API**의 데이터를 실시간으로 처리하는 시스템입니다.  
Streamlit을 활용한 **실시간 대시보드**까지 포함되어 있습니다.


## **프로젝트 개요**
1. **Kafka Producer**  
   - 서울시 공영주차장 API에서 데이터를 가져와 Kafka Topic에 전송
2. **Kafka Consumer & Redis**  
   - Kafka에서 데이터를 소비하여 주차 가능 공간을 계산 후 Redis에 저장
3. **Spark Streaming**  
   - 실시간 데이터 변화를 감지하여 주차장 데이터 분석 (보완 필요)
4. **FastAPI**  
   - Redis 데이터를 조회하는 API 제공
5. **Streamlit 대시보드**  
   - 실시간 주차 가능 공간을 시각화하여 제공
6. **Docker & Docker Compose**  
    - 전체 환경을 컨테이너로 구성하여 손쉽게 배포 가능


## **폴더 구조**
📂 project-root  
│── 📂 fastapi  
│── 📂 streamlit  
│── 📂 kafka  
│── 📂 spark  
│── 📂 producer  
│── 📂 consumer  
│── 📄 docker-compose.yaml  
│── 📄 README.md  


## 기술 스택
| 기술        | 역할 |
|------------|------------------------------------------|
| **Kafka**  | 실시간 데이터 스트리밍 (Producer & Consumer) |
| **Spark**  | 데이터 스트리밍 처리 및 분석 |
| **Redis**  | 실시간 주차 가능 공간 캐싱 |
| **Streamlit** | 실시간 대시보드 (프론트엔드) |
| **Docker** | 컨테이너 기반 서비스 배포 |
| **Docker Compose** | 다중 컨테이너 관리 및 실행 |

## 추가 개발 예정
📌 주차 데이터 기반 혼잡도 분석  
📌 지역별 인기 주차장 랭킹 기능
