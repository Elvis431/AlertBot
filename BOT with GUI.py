import yfinance as yf
import pandas as pd
import streamlit as st
import time
import plotly.graph_objects as go
import requests
import tempfile
import os

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
    if symbol_input and symbol_input.upper() not in st.session_state.custom_symbols:
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

# Countdown timer display
if "refresh_timer" not in st.session_state:
    st.session_state.refresh_timer = refresh_rate

countdown_placeholder = st.empty()

# Function to update countdown
def countdown(seconds):
    for remaining in range(seconds, 0, -1):
        countdown_placeholder.markdown(f"⏳ **Refreshing in: {remaining} seconds**")
        time.sleep(1)

# Function to fetch data from yfinance
def fetch_data(symbol):
    try:
        df = yf.download(symbol, interval="5m", period="1d", progress=False)

        if not isinstance(df, pd.DataFrame) or df.empty:
            raise ValueError("No data or unexpected format")

        df.reset_index(inplace=True)
        df.columns = [str(col).lower() for col in df.columns]

        if 'datetime' in df.columns:
            df.rename(columns={"datetime": "time"}, inplace=True)
        elif 'date' in df.columns:
            df.rename(columns={"date": "time"}, inplace=True)
        else:
            df.rename(columns={df.columns[0]: "time"}, inplace=True)

        rename_map = {
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close'
        }

        possible_cols = list(df.columns)
        for col in rename_map:
            if col not in df.columns:
                for alt_col in possible_cols:
                    if col in alt_col:
                        df.rename(columns={alt_col: col}, inplace=True)

        required_cols = ['open', 'high', 'low', 'close']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")

        return df
    except Exception as e:
        st.error(f"❌ Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

# Strategy 1 – Twin Candle Wick‑Body Balance

def _valid_strategy1_pair(c1: pd.Series, c2: pd.Series) -> bool:
    color1 = "green" if float(c1["close"]) > float(c1["open"]) else "red"
    color2 = "green" if float(c2["close"]) > float(c2["open"]) else "red"
    if color1 != color2:
        return False

    def _balanced(c: pd.Series) -> bool:
        open_ = float(c["open"])
        close = float(c["close"])
        high = float(c["high"])
        low = float(c["low"])

        body = abs(close - open_)
        if body == 0:
            return False
        upper = high - max(close, open_)
        lower = min(close, open_) - low
        return abs(upper - body) / body < 0.2 and abs(lower - body) / body < 0.2

    return _balanced(c1) and _balanced(c2)

def detect_strategy1(df: pd.DataFrame):
    matches = []
    for i in range(len(df) - 1):
        if _valid_strategy1_pair(df.iloc[i], df.iloc[i + 1]):
            matches.append((i, str(df.iloc[i]["time"]), str(df.iloc[i + 1]["time"])))
    return matches

# Send Telegram alert with optional chart

def send_telegram_alert(message, chart_path=None):
    if not enable_alerts:
        return
    try:
        if chart_path and os.path.exists(chart_path):
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            with open(chart_path, 'rb') as photo:
                requests.post(url, data={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "caption": message
                }, files={"photo": photo})
            os.remove(chart_path)
        else:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})
    except Exception as e:
        st.error(f"❌ Telegram Error: {e}")

# Plot chart with plotly and annotations
def plot_chart(df, symbol, strategy_matches):
    fig = go.Figure(data=[go.Candlestick(
        x=df['time'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name="Candles"
    )])

    for idx, time1, time2 in strategy_matches:
        match_price = df.iloc[idx + 1]['close']
        fig.add_trace(go.Scatter(
            x=[time2],
            y=[match_price],
            mode="markers+text",
            marker=dict(color="red", size=10, symbol="star"),
            text=["Strategy 1"],
            textposition="bottom center",
            name="Strategy 1"
        ))

    fig.update_layout(title=f"{symbol} - 5m Candle Chart", xaxis_title="Time", yaxis_title="Price")
    st.plotly_chart(fig, use_container_width=True)

    if strategy_matches:
        temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        fig.write_image(temp_file.name, format="png", engine="kaleido")
        return temp_file.name

    return None

# Run bot loop per refresh
for symbol in symbols:
    with st.container():
        st.subheader(f"📊 {SYMBOL_MAP.get(symbol, symbol)} ({symbol})")
        df = fetch_data(symbol)

        if not df.empty:
            matches = detect_strategy1(df)
            col1, col2 = st.columns([3, 2])

            with col1:
                chart_path = plot_chart(df, symbol, matches)

            with col2:
                st.write(df.tail(5))

                if matches:
                    st.success(f"✅ Strategy 1 Triggered at {matches[-1][2]}")
                    send_telegram_alert(
                        f"✅ Strategy 1 triggered for {symbol} at {matches[-1][2]}", chart_path
                    )
                else:
                    st.info("ℹ️ No signal detected.")

# Countdown and auto-refresh
countdown(refresh_rate)
st.session_state.refresh_timer = refresh_rate
st.rerun()
