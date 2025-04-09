# Forex Data Engineering Pipeline

This project builds a full data pipeline using Kafka, PostgreSQL, FastAPI, Streamlit, and Quelt to process and visualize Forex data in real-time.

## Stack
- EC2 (host)
- Kafka (streaming)
- Python (data flow)
- PostgreSQL (storage)
- FastAPI (backend)
- Streamlit (frontend)
- Quelt (ML)

## Structure
.
├── .env
├── .git/
├── .gitignore
├── README.md
├── app/
│   └── producer/
│       └── forex_producer.py
├── command.txt
├── data/
├── db/
├── docker/
│   ├── Dockerfile.producer
│   └── docker-compose.yml
├── env/
├── requirements.txt
└── scripts/


## ✅ Step 2: Async WebSocket Producer

- Uses `websockets` and `aiokafka` with `asyncio`
- Streams live Forex trade ticks from Finnhub to Kafka topic `forex_stream`
- Handles reconnects and runs continuously
- Dockerized as `forex_producer` service