import os
import json
import time
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from kafka import KafkaProducer

load_dotenv()

API_KEY = os.getenv("FINNHUB_API_KEY")
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
TOPIC_NAME = os.getenv("KAFKA_TOPIC_CANDLE", "forex_candle")

# Initialize Kafka producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Get UNIX timestamps for current and past minute
def get_unix_times():
    now = datetime.utcnow()
    end = int(now.timestamp())
    start = int((now - timedelta(minutes=1)).timestamp())
    return start, end

def fetch_and_send_candles(symbol):
    start, end = get_unix_times()
    url = f"https://finnhub.io/api/v1/forex/candle"
    params = {
        "symbol": symbol,
        "resolution": 1,
        "from": start,
        "to": end,
        "token": API_KEY
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['s'] == 'ok':
            for i in range(len(data['t'])):
                candle = {
                    "symbol": symbol,
                    "timestamp": data['t'][i],
                    "open": data['o'][i],
                    "high": data['h'][i],
                    "low": data['l'][i],
                    "close": data['c'][i],
                    "volume": data['v'][i]
                }
                print("Sending candle:", candle)
                producer.send(TOPIC_NAME, candle)
    else:
        print("Error fetching candle data:", response.text)

def loop_fetch():
    pairs = ["OANDA:EUR_USD", "OANDA:USD_JPY", "OANDA:GBP_USD"]
    while True:
        for symbol in pairs:
            fetch_and_send_candles(symbol)
        time.sleep(60)

if __name__ == "__main__":
    loop_fetch()
