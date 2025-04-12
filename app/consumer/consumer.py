import os
import json
import asyncio
import asyncpg
from dotenv import load_dotenv
from aiokafka import AIOKafkaConsumer

load_dotenv # Loads environment variables from .env file(for DB and Kafka).

DB_URL = os.getenv("POSTGRES_URL", "postgresql://postgres:postgres@postgres:5432/forex")
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
TOPICS = ["forex_stream", "forex_candle"]

async def consume():
    # Connect to Postgres
    conn = await asyncpg.connect(DB_URL)

    # Create tables if they don't exist
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS tick_data (
            id SERIAL PRIMARY KEY,
            symbol TEXT,
            price FLOAT,
            volume FLOAT,
            timestamp BIGINT,
            source TEXT
        );
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS candle_data (
            id SERIAL PRIMARY KEY,
            symbol TEXT,
            timestamp BIGINT,
            open FLOAT,
            high FLOAT,
            low FLOAT,
            close FLOAT,
            volume FLOAT
        );
    """)

    # Setup Kafka consumer
    consumer = AIOKafkaConsumer(
        *TOPICS,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset="latest"
    )
    await consumer.start()

    try:
        async for msg in consumer:
            if msg.topic == "forex_stream":
                await conn.execute("""
                    INSERT INTO tick_data(symbol, price, volume, timestamp, source)
                    VALUES($1, $2, $3, $4, $5)
                """, msg.value["s"], msg.value["p"], msg.value["v"], msg.value["t"], msg.value.get("source", ""))
            elif msg.topic == "forex_candle":
                await conn.execute("""
                    INSERT INTO candle_data(symbol, timestamp, open, high, low, close, volume)
                    VALUES($1, $2, $3, $4, $5, $6, $7)
                """, msg.value["symbol"], msg.value["timestamp"], msg.value["open"],
                     msg.value["high"], msg.value["low"], msg.value["close"], msg.value["volume"])
    finally:
        await consumer.stop()
        await conn.close()

if __name__ == "__main__":
    asyncio.run(consume())
