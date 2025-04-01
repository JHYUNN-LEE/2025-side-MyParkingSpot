from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, when, avg, window, current_timestamp, decode # to_timestamp
from pyspark.sql.types import StructType, StringType

spark = SparkSession.builder \
    .appName("HourlyParkingSummary") \
    .config("spark.sql.legacy.timeParserPolicy", "LEGACY") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

schema = StructType() \
    .add("REGION", StringType()) \
    .add("REGION_CODE", StringType()) \
    .add("PARKING_NAME", StringType()) \
    .add("CAPACITY", StringType()) \
    .add("OCCUPIED_SPOTS", StringType()) \
    .add("IS_REALTIME_STATUS_PROVIDED", StringType())

df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka1:29092,kafka2:29092,kafka3:29092") \
    .option("subscribe", "parking_status") \
    .option("startingOffsets", "latest") \
    .load()

parsed_df = df.selectExpr("CAST(value AS BINARY) as value") \
       .withColumn("json_str", decode(col("value"), "UTF-8")) \
       .withColumn("data", from_json(col("json_str"), schema)) \
       .select("data.*")

# parsed_df = parsed_df.withColumn("CAPACITY", when(col("CAPACITY").rlike("^\d+$"), col("CAPACITY")).otherwise("0").cast("int"))
# parsed_df = parsed_df.withColumn("OCCUPIED_SPOTS", when(col("OCCUPIED_SPOTS").rlike("^\d+$"), col("OCCUPIED_SPOTS")).otherwise("0").cast("int"))
parsed_df = parsed_df.withColumn("CAPACITY", col("CAPACITY").cast("int"))
parsed_df = parsed_df.withColumn("OCCUPIED_SPOTS", col("OCCUPIED_SPOTS").cast("int"))

clean_df = parsed_df.filter(col("IS_REALTIME_STATUS_PROVIDED") == "Y") \
    .na.fill({"CAPACITY": 0, "OCCUPIED_SPOTS": 0}) \
    .withColumn("AVAILABLE_SPOTS", when(
        col("CAPACITY") - col("OCCUPIED_SPOTS") < 0, 0
    ).otherwise(col("CAPACITY") - col("OCCUPIED_SPOTS"))) \
    .withColumn("RECEIVED_AT", current_timestamp()) \
    .withWatermark("RECEIVED_AT", "1 hour")  # 수신 시간 기준 집계
    # .withColumn("LAST_UPDATE", to_timestamp("LAST_UPDATE", "yyyy-MM-dd HH:mm:ss")) \
    # .withWatermark("LAST_UPDATE", "1 hour")

# clean_df 아래에 추가
clean_df.select("REGION", "REGION_CODE", "CAPACITY", "OCCUPIED_SPOTS", "AVAILABLE_SPOTS").writeStream \
    .outputMode("append") \
    .format("console") \
    .option("truncate", False) \
    .start() \
    .awaitTermination()

# 1시간 단위로 집계
agg_df = clean_df.groupBy(
    window(col("RECEIVED_AT"), "1 hour"),
    col("REGION"),
    col("REGION_CODE")
).agg(
    avg("AVAILABLE_SPOTS").alias("AVG_AVAILABLE_SPOTS")
).select(
    col("window.start").alias("hour"),
    col("REGION"),
    col("REGION_CODE"),
    col("AVG_AVAILABLE_SPOTS")
)

# PostgreSQL 저장
def write_to_postgres(batch_df, epoch_id):
    batch_df.write \
        .format("jdbc") \
        .option("url", "jdbc:postgresql://postgres:5432/sidebase") \
        .option("dbtable", "parking.parking_hourly_summary") \
        .option("user", "postgres") \
        .option("password", "postgres.side!") \
        .option("driver", "org.postgresql.Driver") \
        .mode("append") \
        .save()

agg_df.writeStream \
    .outputMode("append") \
    .foreachBatch(write_to_postgres) \
    .start() \
    .awaitTermination()