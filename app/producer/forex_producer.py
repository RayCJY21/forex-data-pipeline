import os
import json
import asyncio
import websockets
import threading
from dotenv import load_dotenv
from kafka import KafkaProducer

load_dotenv()

API_KEY = os.getenv("FINNHUB_API_KEY")
KAFKA_BROKER = os.getenv("KAFKA_BROKER, "kafka:9092") # default docker compose
TOPIC_NAME = os.getenv("KAFKA_TOPIC", "forex_stream")
SYMBOLS = ["OANDA:EUR_USD", "OANDA:USD_JPY", "OANDA:GBP_USD", "OANDA:USD_CAD"]

# Subscribe and Stream Ticks
async def stream_ticks(ws, producer):
    for symbol in SYMBOLS:
        await ws.send(json.dumps({"type": "subscribe", "symbol": symbol}))
    print("Subscribed to symbols.")
    
    async for message in ws:
        data = json.loads(message)
        if "data" in data:
            for tick in data["data"]:
                tick["source"] = "finnhub"
                await producer.send_and_wait(TOPIC_NAME, tick)
                print("Tick sent:", tick)
                
async def produce():
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )
    await producer.start()

    uri = f"wss://ws.finnhub.io?token={API_KEY}"

    while True:
        try:
            async with websockets.connect(uri) as ws:
                print("Connected to Finnhub WebSocket.")
                await stream_ticks(ws, producer)
        except Exception as e:
            print(f"WebSocket error: {e} — retrying in 5s")
            await asyncio.sleep(5)

    await producer.stop()

if __name__ == "__main__":
    asyncio.run(produce())