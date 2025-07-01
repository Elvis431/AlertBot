import time
import pandas as pd
import yfinance as yf
import streamlit as st
import requests

# ============================
# CONFIGURATION
# ============================
TELEGRAM_BOT_TOKEN = "7118083654:AAHnZ9AzA18kRp8FyHcdn8WjC98lrZpOEc8"
TELEGRAM_CHAT_ID = "1714318497"
INTERVAL = "5m"
LOOKBACK = "1d"

SYMBOL_MAP = {
    "BTCUSDT": "BTC-USD",
    "ETHUSDT": "ETH-USD",
    "NIFTY50": "^NSEI",
    "BANKNIFTY": "^NSEBANK"
}

st.set_page_config(page_title="Live Alert Bot", layout="wide")
st.title("📈 Real-time Strategy 1 Alert Bot Dashboard")

# ============================
# CHECK IF MARKET IS OPEN
# ============================
def is_market_open(symbol: str):
    if "NIFTY" in symbol:
        now = pd.Timestamp.now(tz="Asia/Kolkata")
        return now.weekday() < 5 and now.time() >= pd.Timestamp("09:15").time() and now.time() <= pd.Timestamp("15:30").time()
    return True  # Crypto always open

# ============================
# FETCH OHLCV DATA
# ============================
def fetch_data(symbol: str) -> pd.DataFrame:
    try:
        result = yf.download(symbol, period=LOOKBACK, interval=INTERVAL, progress=False)
        if isinstance(result, tuple):
            result = result[0]
        if result is None or result.empty:
            st.warning(f"⚠️ No data for {symbol}")
            return pd.DataFrame()

        # Fix column names (flatten if needed)
        result.columns = [str(col).lower() if isinstance(col, str) else str(col[0]).lower() for col in result.columns]
        result = result.reset_index()

        # Rename time column safely
        if "datetime" in result.columns:
            result.rename(columns={"datetime": "time"}, inplace=True)
        elif "date" in result.columns:
            result.rename(columns={"date": "time"}, inplace=True)
        elif "index" in result.columns:
            result.rename(columns={"index": "time"}, inplace=True)

        # Check and select valid columns
        required_cols = ["time", "open", "high", "low", "close", "volume"]
        if not all(col in result.columns for col in required_cols):
            st.error(f"❌ Data format error for {symbol}. Columns: {result.columns.tolist()}")
            return pd.DataFrame()

        return result[required_cols]
    except Exception as e:
        st.error(f"❌ Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

# ============================
# STRATEGY 1 DETECTION
# ============================
def detect_strategy1(df: pd.DataFrame):
    def _balanced(candle):
        open_, close = candle["open"], candle["close"]
        high, low = candle["high"], candle["low"]
        body = abs(close - open_)
        if body == 0:
            return False
        upper = high - max(open_, close)
        lower = min(open_, close) - low
        return abs(upper - body) / body < 0.2 and abs(lower - body) / body < 0.2

    matches = []
    for i in range(len(df) - 1):
        c1 = df.iloc[i]
        c2 = df.iloc[i + 1]
        color1 = "green" if c1["close"] > c1["open"] else "red"
        color2 = "green" if c2["close"] > c2["open"] else "red"
        if color1 != color2:
            continue
        if _balanced(c1) and _balanced(c2):
            matches.append((c1["time"], c2["time"]))
    return matches

# ============================
# TELEGRAM ALERT
# ============================
def send_telegram_alert(msg: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code != 200:
            st.error(f"Telegram error: {r.text}")
    except Exception as e:
        st.error(f"Telegram failed: {e}")

# ============================
# STREAMLIT DASHBOARD
# ============================
symbols = st.multiselect("Select Symbols", list(SYMBOL_MAP.keys()), default=list(SYMBOL_MAP.keys()))
alerts_enabled = st.toggle("🔔 Alerts ON/OFF", value=True)
run_check = st.button("Run Strategy Check Now")

if run_check:
    for symbol in symbols:
        yf_symbol = SYMBOL_MAP[symbol]
        if not is_market_open(symbol):
            st.info(f"⏱️ Market closed for {symbol}")
            continue

        df = fetch_data(yf_symbol)
        if df.empty:
            continue

        matches = detect_strategy1(df)
        if matches:
            latest = matches[-1]
            msg = f"📘 *Strategy 1 Triggered*\nSymbol: *{symbol}*\nInterval: *{INTERVAL}*\nMatch at: {latest[0]} & {latest[1]}"
            st.success(msg)
            if alerts_enabled:
                send_telegram_alert(msg)
        else:
            st.write(f"✅ No match for {symbol}")
import time
import pandas as pd
import yfinance as yf
import streamlit as st
import requests

# ============================
# CONFIGURATION
# ============================
TELEGRAM_BOT_TOKEN = "7118083654:AAHnZ9AzA18kRp8FyHcdn8WjC98lrZpOEc8"
TELEGRAM_CHAT_ID = "1714318497"
INTERVAL = "5m"
LOOKBACK = "1d"

SYMBOL_MAP = {
    "BTCUSDT": "BTC-USD",
    "ETHUSDT": "ETH-USD",
    "NIFTY50": "^NSEI",
    "BANKNIFTY": "^NSEBANK"
}

st.set_page_config(page_title="Live Alert Bot", layout="wide")
st.title("📈 Real-time Strategy 1 Alert Bot Dashboard")

# ============================
# CHECK IF MARKET IS OPEN
# ============================
def is_market_open(symbol: str):
    if "NIFTY" in symbol:
        now = pd.Timestamp.now(tz="Asia/Kolkata")
        return now.weekday() < 5 and now.time() >= pd.Timestamp("09:15").time() and now.time() <= pd.Timestamp("15:30").time()
    return True  # Crypto always open

# ============================
# FETCH OHLCV DATA
# ============================
def fetch_data(symbol: str) -> pd.DataFrame:
    try:
        result = yf.download(symbol, period=LOOKBACK, interval=INTERVAL, progress=False)
        if isinstance(result, tuple):
            result = result[0]
        if result is None or result.empty:
            st.warning(f"⚠️ No data for {symbol}")
            return pd.DataFrame()

        # Fix column names (flatten if needed)
        result.columns = [str(col).lower() if isinstance(col, str) else str(col[0]).lower() for col in result.columns]
        result = result.reset_index()

        # Rename time column safely
        if "datetime" in result.columns:
            result.rename(columns={"datetime": "time"}, inplace=True)
        elif "date" in result.columns:
            result.rename(columns={"date": "time"}, inplace=True)
        elif "index" in result.columns:
            result.rename(columns={"index": "time"}, inplace=True)

        # Check and select valid columns
        required_cols = ["time", "open", "high", "low", "close", "volume"]
        if not all(col in result.columns for col in required_cols):
            st.error(f"❌ Data format error for {symbol}. Columns: {result.columns.tolist()}")
            return pd.DataFrame()

        return result[required_cols]
    except Exception as e:
        st.error(f"❌ Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

# ============================
# STRATEGY 1 DETECTION
# ============================
def detect_strategy1(df: pd.DataFrame):
    def _balanced(candle):
        open_, close = candle["open"], candle["close"]
        high, low = candle["high"], candle["low"]
        body = abs(close - open_)
        if body == 0:
            return False
        upper = high - max(open_, close)
        lower = min(open_, close) - low
        return abs(upper - body) / body < 0.2 and abs(lower - body) / body < 0.2

    matches = []
    for i in range(len(df) - 1):
        c1 = df.iloc[i]
        c2 = df.iloc[i + 1]
        color1 = "green" if c1["close"] > c1["open"] else "red"
        color2 = "green" if c2["close"] > c2["open"] else "red"
        if color1 != color2:
            continue
        if _balanced(c1) and _balanced(c2):
            matches.append((c1["time"], c2["time"]))
    return matches

# ============================
# TELEGRAM ALERT
# ============================
def send_telegram_alert(msg: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code != 200:
            st.error(f"Telegram error: {r.text}")
    except Exception as e:
        st.error(f"Telegram failed: {e}")

# ============================
# STREAMLIT DASHBOARD
# ============================
symbols = st.multiselect("Select Symbols", list(SYMBOL_MAP.keys()), default=list(SYMBOL_MAP.keys()))
alerts_enabled = st.toggle("🔔 Alerts ON/OFF", value=True)
run_check = st.button("Run Strategy Check Now")

if run_check:
    for symbol in symbols:
        yf_symbol = SYMBOL_MAP[symbol]
        if not is_market_open(symbol):
            st.info(f"⏱️ Market closed for {symbol}")
            continue

        df = fetch_data(yf_symbol)
        if df.empty:
            continue

        matches = detect_strategy1(df)
        if matches:
            latest = matches[-1]
            msg = f"📘 *Strategy 1 Triggered*\nSymbol: *{symbol}*\nInterval: *{INTERVAL}*\nMatch at: {latest[0]} & {latest[1]}"
            st.success(msg)
            if alerts_enabled:
                send_telegram_alert(msg)
        else:
            st.write(f"✅ No match for {symbol}")
