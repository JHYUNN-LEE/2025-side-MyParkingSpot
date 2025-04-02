from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, when, avg, window, decode, from_utc_timestamp
from pyspark.sql.types import StructType, StringType
import os
from dotenv import load_dotenv

load_dotenv()

bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVER")

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
    .option("kafka.bootstrap.servers", bootstrap_servers) \
    .option("subscribe", "parking_status") \
    .option("startingOffsets", "latest") \
    .load()

parsed_df = df.selectExpr("CAST(value AS BINARY) as value", "timestamp") \
    .withColumn("json_str", decode(col("value"), "UTF-8")) \
    .withColumn("data", from_json(col("json_str"), schema)) \
    .select("data.*", "timestamp") \
    .withColumn("CAPACITY", col("CAPACITY").cast("int")) \
    .withColumn("OCCUPIED_SPOTS", col("OCCUPIED_SPOTS").cast("int"))

clean_df = parsed_df.filter(col("IS_REALTIME_STATUS_PROVIDED") == "Y") \
    .na.fill({"CAPACITY": 0, "OCCUPIED_SPOTS": 0}) \
    .withColumn("AVAILABLE_SPOTS", when(
        col("CAPACITY") - col("OCCUPIED_SPOTS") < 0, 0
    ).otherwise(col("CAPACITY") - col("OCCUPIED_SPOTS"))) \
    .withColumnRenamed("timestamp", "RECEIVED_AT") \
    .withWatermark("RECEIVED_AT", "1 minute") 

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
agg_df = agg_df.withColumn("hour", from_utc_timestamp(col("hour"), "Asia/Seoul"))

def write_to_postgres(batch_df, epoch_id):
    batch_df.write \
        .format("jdbc") \
        .option("url", "jdbc:postgresql://postgres:5432/sidebase") \
        .option("dbtable", "parking.parking_hourly_avg") \
        .option("user", "postgres") \
        .option("password", "postgres.side!") \
        .option("driver", "org.postgresql.Driver") \
        .mode("append") \
        .save()

agg_df.writeStream \
    .format("console") \
    .outputMode("update") \
    .option("truncate", False) \
    .start()

agg_df.writeStream \
    .outputMode("update") \
    .foreachBatch(write_to_postgres) \
    .start() \
    .awaitTermination()