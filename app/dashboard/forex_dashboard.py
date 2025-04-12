import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import asyncpg
import asyncio
import ta
from datetime import datetime

# Async database query
async def fetch_data():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/forex")
    candles = await conn.fetch("SELECT * FROM candle_data ORDER BY timestamp DESC LIMIT 200")
    ticks = await conn.fetch("SELECT * FROM tick_data ORDER BY timestamp DESC LIMIT 1")
    await conn.close()
    return candles, ticks

@st.cache_data(ttl=60)
def load_data():
    candles, ticks = asyncio.run(fetch_data())
    df_candle = pd.DataFrame(candles, columns=["id", "symbol", "timestamp", "open", "high", "low", "close", "volume"])
    df_candle["datetime"] = pd.to_datetime(df_candle["timestamp"], unit="s")
    df_tick = pd.DataFrame(ticks, columns=["id", "symbol", "price", "volume", "timestamp", "source"])
    return df_candle, df_tick

def add_indicators(df):
    df["SMA_20"] = ta.trend.sma_indicator(df["close"], window=20)
    df["EMA_20"] = ta.trend.ema_indicator(df["close"], window=20)
    return df

# Page layout
st.set_page_config(layout="wide")
st.title("📊 Real-Time Forex Dashboard")

# Sidebar
st.sidebar.header("Settings")
symbol = st.sidebar.selectbox("Currency Pair", ["OANDA:EUR_USD", "OANDA:USD_JPY", "OANDA:GBP_USD"])
chart_type = st.sidebar.selectbox("Chart Type", ["Candlestick", "Line"])
indicators = st.sidebar.multiselect("Indicators", ["SMA 20", "EMA 20"])

# Load and filter data
df_candle, df_tick = load_data()
df_candle = df_candle[df_candle["symbol"] == symbol]
df_candle = df_candle.sort_values("datetime")

df_candle = add_indicators(df_candle)

# Show metrics
if not df_candle.empty:
    last_row = df_candle.iloc[-1]
    first_row = df_candle.iloc[0]
    change = last_row["close"] - first_row["close"]
    pct_change = (change / first_row["close"]) * 100
    st.metric(f"{symbol} Last Price", f"{last_row['close']:.5f}", f"{change:.5f} ({pct_change:.2f}%)")

# Price chart
fig = go.Figure()

if chart_type == "Candlestick":
    fig.add_trace(go.Candlestick(
        x=df_candle["datetime"],
        open=df_candle["open"],
        high=df_candle["high"],
        low=df_candle["low"],
        close=df_candle["close"]
    ))
else:
    fig.add_trace(go.Scatter(x=df_candle["datetime"], y=df_candle["close"], name="Price"))

if "SMA 20" in indicators:
    fig.add_trace(go.Scatter(x=df_candle["datetime"], y=df_candle["SMA_20"], name="SMA 20"))

if "EMA 20" in indicators:
    fig.add_trace(go.Scatter(x=df_candle["datetime"], y=df_candle["EMA_20"], name="EMA 20"))

fig.update_layout(title=f"{symbol} Price Chart", height=600)
st.plotly_chart(fig, use_container_width=True)

# Historical table
st.subheader("Candle Data")
st.dataframe(df_candle[["datetime", "open", "high", "low", "close", "volume"]])
