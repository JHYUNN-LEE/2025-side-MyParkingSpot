from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, when
from pyspark.sql.types import StructType, StringType, IntegerType

spark = SparkSession.builder \
    .appName("KafkaParkingStreaming") \
    .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
    .getOrCreate()

schema = StructType() \
    .add("PARKING_NAME", StringType()) \
    .add("CAPACITY", StringType()) \
    .add("OCCUPIED_SPOTS", StringType()) \
    .add("LAST_UPDATE", StringType()) \
    .add("IS_REALTIME_STATUS_PROVIDED", StringType())

# Kafka에서 스트리밍 데이터 읽기
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka1:29092,kafka2:29092,kafka3:29092") \
    .option("subscribe", "parking_status") \
    .option("startingOffsets", "earliest") \
    .load()

df = df.selectExpr("CAST(value AS STRING)")
df = df.withColumn("value", from_json(col("value"), schema)).select("value.*")

# NULL 값 처리
df = df.na.fill({"OCCUPIED_SPOTS": "0", "IS_REALTIME_STATUS_PROVIDED": "N", "CAPACITY": "0"})

# 데이터 타입 변환
df = df.withColumn("CAPACITY", col("CAPACITY").cast(IntegerType()))
df = df.withColumn("OCCUPIED_SPOTS", col("OCCUPIED_SPOTS").cast(IntegerType()))

# 주차 가능 자리 계산 (available_spots = capacity - occupied_spots)
df = df.withColumn("AVAILABLE_SPOTS", when(col("CAPACITY") - col("OCCUPIED_SPOTS") < 0, 0)
                   .otherwise(col("CAPACITY") - col("OCCUPIED_SPOTS")))

# 실시간 데이터만 필터링
df = df.filter(col("IS_REALTIME_STATUS_PROVIDED") == "Y")

# 콘솔 출력 (테스트용)
query = df.writeStream \
    .outputMode("append") \
    .format("console") \
    .start()

query.awaitTermination()