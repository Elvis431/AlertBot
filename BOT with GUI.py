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
NSE_SYMBOLS = ["NIFTY50", "BANKNIFTY"]

# ========================== UI ==========================
st.set_page_config(page_title="Real-Time Strategy Alert Bot", layout="wide")
st.title("📈 Strategy Alert Bot Dashboard")
st.markdown("Monitors BTC, ETH, NIFTY50, BANKNIFTY for Strategy 1")

st.sidebar.header("⚙️ Bot Settings")
selected_symbols = st.sidebar.multiselect("Select Symbols", list(SYMBOL_MAP.keys()), default=list(SYMBOL_MAP.keys()), key="symbols")
alerts_enabled = st.sidebar.checkbox("Enable Telegram Alerts", value=True, key="alerts")
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

def is_market_open(symbol_key):
    now = datetime.now()
    if symbol_key in NSE_SYMBOLS:
        # NSE is open Mon–Fri, 9:15 AM to 3:30 PM IST
        ist_now = now + timedelta(hours=5, minutes=30)
        if ist_now.weekday() >= 5:  # Saturday or Sunday
            return False
        return ist_now.hour == 9 and ist_now.minute >= 15 or (10 <= ist_now.hour < 15) or (ist_now.hour == 15 and ist_now.minute <= 30)
    return True  # Crypto is 24/7

def is_balanced(candle):
    open_ = float(candle["open"])
    close = float(candle["close"])
    high = float(candle["high"])
    low = float(candle["low"])
    body = abs(close - open_)
    if body == 0:
        return False
    upper = high - max(open_, close)
    lower = min(open_, close) - low
    return upper < 1.5 * body and lower < 1.5 * body

def detect_strategy(df):
    try:
        c1 = df.iloc[-2]
        c2 = df.iloc[-1]
        same_color = ((c1["close"] > c1["open"] and c2["close"] > c2["open"]) or
                      (c1["close"] < c1["open"] and c2["close"] < c2["open"]))
        if not same_color:
            return None
        if is_balanced(c1) and is_balanced(c2):
            return "✅ Strategy 1: Twin Candle Wick–Body Balance Triggered", df.iloc[-1]["time"], df.iloc[-1]["close"]
    except Exception as e:
        st.warning(f"Strategy error: {e}")
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

def plot_chart(df, symbol, strategy_time=None, strategy_price=None):
    fig = go.Figure(data=[go.Candlestick(
        x=df['time'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close']
    )])
    if strategy_time and strategy_price:
        fig.add_trace(go.Scatter(
            x=[strategy_time],
            y=[strategy_price],
            mode='markers+text',
            marker=dict(color='red', size=10, symbol='star'),
            text=["Strategy 1"],
            textposition="top center",
            name="Signal"
        ))
    fig.update_layout(title=f"5-Min Candles: {symbol}", xaxis_rangeslider_visible=False)
    return fig

# ========================== MAIN LOGIC ==========================
if 'last_checked' not in st.session_state:
    st.session_state['last_checked'] = {}

for symbol_key in selected_symbols:
    yf_symbol = SYMBOL_MAP[symbol_key]
    df = fetch_data(yf_symbol)
    if df is not None and len(df) >= 2:
        strategy_output = detect_strategy(df)
        last_alert_time = st.session_state['last_checked'].get(symbol_key, datetime.min)

        col1, col2 = st.columns([2, 1])
        with col1:
            if strategy_output:
                _, s_time, s_price = strategy_output
                fig = plot_chart(df, symbol_key, strategy_time=s_time, strategy_price=s_price)
            else:
                fig = plot_chart(df, symbol_key)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader(f"🔍 Status: {symbol_key}")
            if strategy_output:
                strategy_msg, s_time, _ = strategy_output
                st.success(strategy_msg)

                if alerts_enabled:
                    if is_market_open(symbol_key):
                        if (datetime.now() - last_alert_time).seconds > refresh_rate:
                            send_telegram_alert(strategy_msg, symbol_key)
                            st.session_state['last_checked'][symbol_key] = datetime.now()
                        else:
                            st.info("⏳ Alert throttled by refresh rate.")
                    else:
                        st.info("🕒 Market is closed. Alert suppressed.")
            else:
                st.warning("No strategy signal at this time.")

# ========================== AUTO REFRESH ==========================
st.sidebar.markdown("💡 Bot running in real-time. Leave this tab open.")
st_autorefresh = st.empty()
st_autorefresh.text(f"⏳ Waiting for {refresh_rate} seconds to refresh...")

time.sleep(refresh_rate)
st.rerun()
