# Bitnami Spark 이미지 사용
FROM bitnami/spark:3.5.5-debian-12-r0

# 작업 디렉토리 설정
WORKDIR /opt/bitnami/spark

# 필요한 패키지 설치 및 Kafka 관련 JAR 다운로드
USER root
RUN apt-get update && \
    apt-get install -y wget && \
    mkdir -p /opt/bitnami/spark/jars && \
    wget https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.5.5/spark-sql-kafka-0-10_2.12-3.5.5.jar -P /opt/bitnami/spark/jars && \
    wget https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.5.5/spark-token-provider-kafka-0-10_2.12-3.5.5.jar -P /opt/bitnami/spark/jars && \
    wget https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.5.1/kafka-clients-3.5.1.jar -P /opt/bitnami/spark/jars && \
    wget https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar -P /opt/bitnami/spark/jars && \
    apt-get clean
# 비루트 사용자로 변경
USER 1001

# Spark Master 실행
CMD ["spark-class", "org.apache.spark.deploy.master.Master"]
