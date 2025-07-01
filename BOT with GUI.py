import streamlit as st
import pandas as pd
import yfinance as yf
import datetime
import time
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import requests
import os

# --------------------------- Telegram Configuration ---------------------------
TELEGRAM_BOT_TOKEN = "7118083654:AAHnZ9AzA18kRp8FyHcdn8WjC98lrZpOEc8"
TELEGRAM_CHAT_ID = "1714318497"

# --------------------------- Symbol Mapping ---------------------------
SYMBOL_MAP = {
    "BTCUSDT": "BTC-USD",
    "ETHUSDT": "ETH-USD",
    "NIFTY50": "^NSEI",
    "BANKNIFTY": "^NSEBANK"
}

# --------------------------- Strategy Logic (Bullish Engulfing) ---------------------------
def detect_bullish_engulfing(df):
    df['signal'] = ""
    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]
        if prev['close'] < prev['open'] and curr['close'] > curr['open']:
            if curr['open'] < prev['close'] and curr['close'] > prev['open']:
                df.at[df.index[i], 'signal'] = 'Bullish Engulfing'
    return df

# --------------------------- Fetch Data ---------------------------
def fetch_data(symbol, interval="5m", period="1d"):
    try:
        df = yf.download(tickers=symbol, interval=interval, period=period)
        df = df.reset_index()
        df.columns = [col.lower() for col in df.columns]
        df = df.rename(columns={'datetime': 'time'})
        df = df[['time', 'open', 'high', 'low', 'close', 'volume']]
        return df
    except Exception as e:
        st.error(f"❌ Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

# --------------------------- Plot and Save Chart ---------------------------
def plot_chart(df, symbol):
    fig = go.Figure(data=[go.Candlestick(
        x=df['time'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        increasing_line_color='green',
        decreasing_line_color='red'
    )])
    fig.update_layout(title=f"{symbol} - Last 20 Candles", xaxis_title="Time", yaxis_title="Price")
    file_name = f"{symbol}_chart.png"
    fig.write_image(file_name)
    return file_name

# --------------------------- Send Alert with Chart ---------------------------
def send_telegram_alert(symbol, signal, chart_path):
    try:
        message = f"🚨 *{signal}* Detected on *{symbol}*\nTime: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        with open(chart_path, 'rb') as photo:
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": message,
                "parse_mode": "Markdown"
            }
            files = {"photo": photo}
            requests.post(url, data=payload, files=files)
    except Exception as e:
        st.error(f"❌ Failed to send Telegram alert for {symbol}: {e}")

# --------------------------- Strategy Runner ---------------------------
def run_strategy(symbols, alerts_enabled):
    for symbol in symbols:
        yf_symbol = SYMBOL_MAP[symbol]
        df = fetch_data(yf_symbol)
        if df.empty:
            continue
        df = detect_bullish_engulfing(df)
        latest = df.iloc[-1]
        if latest['signal'] == 'Bullish Engulfing':
            st.success(f"✅ Bullish Engulfing on {symbol}")
            chart_path = plot_chart(df[-20:], symbol)
            if alerts_enabled:
                send_telegram_alert(symbol, "Bullish Engulfing", chart_path)
        else:
            st.info(f"ℹ️ No Signal on {symbol}")

# --------------------------- Streamlit UI ---------------------------
st.set_page_config(page_title="Trading Strategy Alert Dashboard", layout="wide")
st.title("📈 Real-time Trading Strategy Alerts")
st.markdown("Monitor BTC, ETH, Nifty, and BankNifty with Strategy 1 (Bullish Engulfing)")

symbols = st.multiselect("Select Symbols", list(SYMBOL_MAP.keys()), default=list(SYMBOL_MAP.keys()), key="symbol_selector")
alerts_enabled = st.toggle("🔔 Alerts ON/OFF", value=True, key="alert_toggle")

if st.button("Run Strategy Check Now", key="run_button"):
    run_strategy(symbols, alerts_enabled)

# Optional Auto Refresh
st_autorefresh = st.empty()
st_autorefresh.button("🔁 Auto Refresh (every 1 min)", key="auto_refresh_button")

# Run every 60 seconds if enabled (uncomment below for auto mode)
# while True:
#     run_strategy(symbols, alerts_enabled)
#     time.sleep(60)
