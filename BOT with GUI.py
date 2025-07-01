import time
import requests
import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime
import pytz

# ========================
# 🔧 Configuration
# ========================
TELEGRAM_BOT_TOKEN = "7118083654:AAHnZ9AzA18kRp8FyHcdn8WjC98lrZpOEc8"
TELEGRAM_CHAT_ID = "1714318497"
SYMBOLS = {
    "BTCUSDT": "BTC-USD",
    "ETHUSDT": "ETH-USD",
    "NIFTY50": "^NSEI",
    "BANKNIFTY": "^NSEBANK"
}
INTERVAL = "5m"
LOOKBACK = "1d"
REFRESH_SECONDS = 300  # 5 minutes

st.set_page_config(page_title="Strategy 1 Bot", layout="centered")

# ========================
# 🧠 Strategy Logic
# ========================
def fetch_data(ticker: str) -> pd.DataFrame:
    df = yf.download(ticker, period=LOOKBACK, interval=INTERVAL, progress=False)
    if df.empty:
        return df
    df = df.reset_index()
    df.columns = [col.lower() for col in df.columns]
    df.rename(columns={"datetime": "time"}, inplace=True)
    return df[["time", "open", "high", "low", "close", "volume"]]

def _valid_strategy1_pair(c1: pd.Series, c2: pd.Series) -> bool:
    color1 = "green" if c1["close"] > c1["open"] else "red"
    color2 = "green" if c2["close"] > c2["open"] else "red"
    if color1 != color2:
        return False

    def balanced(c):
        open_, close = c["open"], c["close"]
        body = abs(close - open_)
        if body == 0: return False
        upper = c["high"] - max(open_, close)
        lower = min(open_, close) - c["low"]
        return abs(upper - body) / body < 0.2 and abs(lower - body) / body < 0.2

    return balanced(c1) and balanced(c2)

def detect_strategy1(df: pd.DataFrame):
    matches = []
    for i in range(len(df) - 1):
        if _valid_strategy1_pair(df.iloc[i], df.iloc[i + 1]):
            matches.append((df.iloc[i]["time"], df.iloc[i + 1]["time"]))
    return matches

def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        st.error(f"Telegram Error: {e}")

# ========================
# 🌐 Streamlit UI
# ========================
st.title("📊 Real-Time Strategy 1 Bot")
st.markdown("Monitors **BTCUSDT**, **ETHUSDT**, **NIFTY50**, and **BANKNIFTY** for Strategy 1.")

st.sidebar.header("🛠️ Controls")
enabled_symbols = {}
for name in SYMBOLS:
    enabled_symbols[name] = st.sidebar.toggle(f"🟢 Alert for {name}", value=True)

if st.button("🔄 Run Scan Now"):
    now = datetime.now(pytz.timezone("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S')
    st.info(f"Scanning at {now}")
    for symbol, ticker in SYMBOLS.items():
        if not enabled_symbols[symbol]:
            continue

        df = fetch_data(ticker)
        if df.empty:
            st.warning(f"No data for {symbol}")
            continue

        matches = detect_strategy1(df)
        if matches:
            for t1, t2 in matches[-1:]:
                msg = f"📘 *Strategy 1* triggered on *{symbol}*\n🕒 {t1} & {t2}\nTimeframe: *{INTERVAL}*"
                send_telegram(msg)
                st.success(f"✅ Strategy 1 Match on {symbol} — {t2}")
        else:
            st.write(f"❌ No signal on {symbol}")
else:
    st.warning("Press **Run Scan Now** to check manually.")

st.markdown("---")
st.caption("Made with ❤️ | Strategy 1 Detection | Alerts via Telegram")

# Optional: Auto-refresh every 5 mins
st_autorefresh = st.experimental_rerun if "auto" in st.query_params else None
