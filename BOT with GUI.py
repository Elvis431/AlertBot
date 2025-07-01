import yfinance as yf
import pandas as pd
import streamlit as st
import time
import plotly.graph_objects as go
import requests

# Telegram configuration
TELEGRAM_BOT_TOKEN = "7118083654:AAHnZ9AzA18kRp8FyHcdn8WjC98lrZpOEc8"
TELEGRAM_CHAT_ID = "1714318497"

# Symbol map for display names
SYMBOL_MAP = {
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
    "^NSEI": "Nifty50",
    "^NSEBANK": "BankNifty"
}

# Load symbols from session state
if "custom_symbols" not in st.session_state:
    st.session_state.custom_symbols = list(SYMBOL_MAP.keys())

# Add title
st.set_page_config(page_title="Live Trading Bot Dashboard", layout="wide")
st.title("📈 Real-Time Strategy Alert Bot Dashboard")

# Sidebar for adding/removing symbols
st.sidebar.header("Symbol Controls")

symbol_input = st.sidebar.text_input("Add a symbol (e.g., TATAMOTORS.NS, AAPL, MATIC-USD)")
if st.sidebar.button("Add Symbol"):
    if symbol_input and symbol_input not in st.session_state.custom_symbols:
        st.session_state.custom_symbols.append(symbol_input.upper())
        st.success(f"Added {symbol_input.upper()} to watchlist")

remove_symbol = st.sidebar.selectbox("Remove Symbol", options=st.session_state.custom_symbols)
if st.sidebar.button("Remove Selected Symbol"):
    if remove_symbol in st.session_state.custom_symbols:
        st.session_state.custom_symbols.remove(remove_symbol)
        st.success(f"Removed {remove_symbol} from watchlist")

# Refresh rate
refresh_rate = st.sidebar.slider("Refresh Interval (seconds)", 30, 300, 60, step=30)

# Symbol selection
symbols = st.multiselect("Select Symbols to Monitor", st.session_state.custom_symbols, default=st.session_state.custom_symbols)

# Alert toggle
enable_alerts = st.checkbox("Enable Telegram Alerts", value=True)

# Function to fetch data from yfinance
def fetch_data(symbol):
    try:
        df = yf.download(symbol, interval="5m", period="1d")
        df.reset_index(inplace=True)
        df.columns = [col.lower() for col in df.columns]
        df.rename(columns={"datetime": "time"}, inplace=True)
        return df
    except Exception as e:
        st.error(f"❌ Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

# Strategy 1: Bullish Engulfing pattern (basic example)
def check_strategy_1(df):
    if len(df) < 2:
        return False
    prev, curr = df.iloc[-2], df.iloc[-1]
    return prev['close'] < prev['open'] and curr['close'] > curr['open'] and curr['close'] > prev['open'] and curr['open'] < prev['close']

# Send Telegram alert with optional chart
def send_telegram_alert(message):
    if not enable_alerts:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})
    except Exception as e:
        st.error(f"❌ Telegram Error: {e}")

# Plot chart with plotly
def plot_chart(df, symbol):
    fig = go.Figure(data=[go.Candlestick(
        x=df['time'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close']
    )])
    fig.update_layout(title=f"{symbol} - 5m Candle Chart", xaxis_title="Time", yaxis_title="Price")
    st.plotly_chart(fig, use_container_width=True)

# Run bot loop per refresh
for symbol in symbols:
    with st.container():
        st.subheader(f"📊 {SYMBOL_MAP.get(symbol, symbol)} ({symbol})")
        df = fetch_data(symbol)

        if not df.empty:
            col1, col2 = st.columns([3, 2])

            with col1:
                plot_chart(df, symbol)

            with col2:
                st.write(df.tail(5))

                if check_strategy_1(df):
                    st.success("✅ Strategy 1 Triggered!")
                    send_telegram_alert(f"✅ Strategy 1 triggered for {symbol}")
                else:
                    st.info("ℹ️ No signal detected.")

# Auto refresh every x seconds
st.experimental_rerun() if st.session_state.get("last_refresh", 0) + refresh_rate < time.time() else st.session_state.update({"last_refresh": time.time()})
