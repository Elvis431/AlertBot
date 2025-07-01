import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import time
import requests
import plotly.graph_objects as go

# --- TELEGRAM CONFIG ---
TELEGRAM_BOT_TOKEN = "7118083654:AAHnZ9AzA18kRp8FyHcdn8WjC98lrZpOEc8"
TELEGRAM_CHAT_ID = "1714318497"

# --- SYMBOL MAPPING ---
SYMBOL_MAP = {
    "BTCUSDT": "BTC-USD",
    "ETHUSDT": "ETH-USD",
    "NIFTY50": "^NSEI",
    "BANKNIFTY": "^NSEBANK"
}

# --- Streamlit UI ---
st.set_page_config(page_title="Trading Alert Bot", layout="wide")
st.title("📊 Real-time Trading Strategy Alerts")

# User controls
symbols = st.multiselect("Select Symbols", list(SYMBOL_MAP.keys()), default=list(SYMBOL_MAP.keys()), key="symbol_select")
alert_enabled = st.checkbox("🔔 Enable Alerts", value=True, key="alert_toggle")
refresh_interval = st.slider("⏱️ Refresh Interval (seconds)", 30, 300, 60)

# --- Strategy 1: Bullish Engulfing Pattern ---
def strategy_1(df):
    if len(df) < 2:
        return False
    prev = df.iloc[-2]
    curr = df.iloc[-1]
    return prev['Close'] < prev['Open'] and curr['Close'] > curr['Open'] and curr['Close'] > prev['Open'] and curr['Open'] < prev['Close']

# --- Fetch data from yfinance ---
def fetch_data(symbol):
    try:
        ticker = SYMBOL_MAP[symbol]
        df = yf.download(ticker, interval='5m', period='1d')
        df.reset_index(inplace=True)
        df.rename(columns=str.capitalize, inplace=True)
        df = df[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']]
        df.rename(columns={"Datetime": "Time"}, inplace=True)
        return df
    except Exception as e:
        st.error(f"❌ Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

# --- Send Telegram alert ---
def send_telegram_alert(symbol, message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": f"📢 [{symbol}] Alert:\n{message}"}
        requests.post(url, data=payload)
    except Exception as e:
        st.error(f"❌ Error sending Telegram message: {e}")

# --- Plot Chart ---
def plot_chart(df, symbol):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df["Time"],
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name=symbol
    ))
    fig.update_layout(title=f"{symbol} - 5m Candlestick", xaxis_rangeslider_visible=False)
    return fig

# --- Main Monitoring Loop ---
def monitor():
    for symbol in symbols:
        df = fetch_data(symbol)
        if df.empty:
            continue

        st.subheader(f"📈 {symbol}")
        st.plotly_chart(plot_chart(df, symbol), use_container_width=True)

        if alert_enabled:
            try:
                if strategy_1(df):
                    send_telegram_alert(symbol, "✅ Strategy 1 triggered: Bullish Engulfing Pattern")
                    st.success(f"{symbol}: Strategy 1 Triggered ✅")
                else:
                    st.info(f"{symbol}: No alert 🚫")
            except Exception as e:
                st.error(f"❌ Error evaluating strategy for {symbol}: {e}")

# --- Streamlit Auto-refresh ---
placeholder = st.empty()
while True:
    with placeholder.container():
        monitor()
    time.sleep(refresh_interval)
