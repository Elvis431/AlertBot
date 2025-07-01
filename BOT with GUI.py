import streamlit as st
import pandas as pd
import yfinance as yf
import time
import requests
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ========================== CONFIG ==========================
TELEGRAM_BOT_TOKEN = "7118083654:AAHnZ9AzA18kRp8FyHcdn8WjC98lrZpOEc8"
TELEGRAM_CHAT_ID = "1714318497"
SYMBOL_MAP = {
    "BTCUSDT": "BTC-USD",
    "ETHUSDT": "ETH-USD",
    "NIFTY50": "^NSEI",
    "BANKNIFTY": "^NSEBANK"
}
# ========================== UI ==========================
st.set_page_config(page_title="Real-Time Strategy Alert Bot", layout="wide")
st.title("📈 Strategy Alert Bot Dashboard")
st.markdown("Monitors BTC, ETH, NIFTY50, BANKNIFTY for Strategy 1")

# Sidebar settings
st.sidebar.header("⚙️ Bot Settings")
selected_symbols = st.sidebar.multiselect("Select Symbols", list(SYMBOL_MAP.keys()), default=list(SYMBOL_MAP.keys()), key="symbols")
alerts_enabled = st.sidebar.checkbox("Enable Alerts", value=True, key="alerts")
refresh_rate = st.sidebar.slider("Refresh Interval (seconds)", 30, 300, 60, step=30)

# ========================== STRATEGY LOGIC ==========================
def fetch_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(interval="5m", period="1d")
        df.reset_index(inplace=True)
        df.columns = [str(col).lower() for col in df.columns]
        df.rename(columns={'datetime': 'time'}, inplace=True)
        df = df[['time', 'open', 'high', 'low', 'close', 'volume']]
        return df
    except Exception as e:
        st.error(f"❌ Error fetching data for {symbol}: {e}")
        return None

def detect_strategy(df):
    try:
        latest = df.iloc[-1]
        previous = df.iloc[-2]
        # Strategy 1: Bullish Candle after Bearish
        if previous['close'] < previous['open'] and latest['close'] > latest['open']:
            return "Strategy 1 Triggered: Bullish Reversal"
    except:
        pass
    return None

def send_telegram_alert(message, symbol):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": f"⚠️ Alert for {symbol}\n{message}"
        }
        requests.post(url, data=payload)
    except Exception as e:
        st.error(f"Telegram Error: {e}")

def plot_chart(df, symbol):
    fig = go.Figure(data=[go.Candlestick(
        x=df['time'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close']
    )])
    fig.update_layout(title=f"5-Min Candles: {symbol}", xaxis_rangeslider_visible=False)
    return fig

# ========================== MAIN LOGIC ==========================
if 'last_checked' not in st.session_state:
    st.session_state['last_checked'] = {}

for symbol in selected_symbols:
    yf_symbol = SYMBOL_MAP[symbol]
    df = fetch_data(yf_symbol)
    if df is not None and len(df) >= 2:
        signal = detect_strategy(df)
        last_alert_time = st.session_state['last_checked'].get(symbol, datetime.min)

        col1, col2 = st.columns([2, 1])
        with col1:
            st.plotly_chart(plot_chart(df, symbol), use_container_width=True)

        with col2:
            st.subheader(f"🔍 Status: {symbol}")
            if signal:
                st.success(f"{signal}")
                if alerts_enabled and (datetime.now() - last_alert_time).seconds > refresh_rate:
                    send_telegram_alert(signal, symbol)
                    st.session_state['last_checked'][symbol] = datetime.now()
            else:
                st.warning("No strategy signal at this time.")

st.sidebar.markdown("💡 Bot running in real-time. Leave this tab open.")
st_autorefresh = st.empty()
st_autorefresh.text(f"⏳ Waiting for {refresh_rate} seconds to refresh...")

time.sleep(refresh_rate)
st.rerun()
