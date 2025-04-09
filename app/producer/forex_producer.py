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

async def produce():

	# Initialize Kafka producer
	producer = AIOKafkaProducer(
		bootstrap_servers=KAFKA_BROKER,
		value_serializer=lambda v: json.dumps(v).encode('utf-8')
	)
	await producer.start()
	
	while True:
		try:
			uri = f"wss://ws.finnhub.io?token={API_KEY}" # Create WebSocket connection to connect to server
			async with websockets.connect(uri) as ws:  # Send connection request to server uri
				for symbol in SYMBOLS:
					await ws.send(json.dumps({"type": "subscribe", "symbol": symbol}))
				print("Connected to Finnhub and subscribed")

				async for message in ws: # Use async to prevent bolck the whole program while waiting
					data = json.loads(message)
					if "data" in data:
						for tick in data["data"]:
							tick["source"] = "finnhub"
							await producer.send_and_wait(TOPIC_NAME, tick)
							print("Tick send to kafka broker", tick)
    	except Exception as e:
			print (f"Connection error: {e}, reconnecting...")
			await asyncio.sleep(5)
		finally:
			print("Restarting")
	await producer.stop()

if __name__ == "__main__":
	asyncio.run(produce())
