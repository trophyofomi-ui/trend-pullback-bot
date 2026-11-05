import streamlit as st
import ccxt
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import sys
import os
import requests

# Add root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.config import SYMBOLS, TIMEFRAME
from src.indicators import ema, rsi, atr, adx
from src.strategy import check_signal
from src.veto import llm_veto

# --- TELEGRAM SETTINGS ---
TELEGRAM_TOKEN = ""
TELEGRAM_CHAT_ID = ""

def send_telegram_alert(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram error: {e}")

# --- DASHBOARD START ---
st.set_page_config(page_title="AI Trading Bot Dashboard", layout="wide")
st.title("🤖 AI Trend-Pullback Bot Dashboard")

# --- SIDEBAR SETTINGS ---
st.sidebar.header("Bot Settings")
simulate_trade = st.sidebar.checkbox("Simulate Trades (Paper Mode)", value=True)
st.sidebar.write("---")
st.sidebar.write("### Claude Memory")
st.sidebar.write("Claude will remember the last 5 trades to avoid repeating mistakes.")

# Connect to BINANCE
@st.cache_resource
def get_exchange():
    return ccxt.binance({"enableRateLimit": True, "options": {"defaultType": "future"}})

EX = get_exchange()

def fetch_data(symbol):
    binance_symbol = symbol.replace(":USDT", "")
    bars = EX.fetch_ohlcv(binance_symbol, TIMEFRAME, limit=300)
    df = pd.DataFrame(bars, columns=["ts", "open", "high", "low", "close", "volume"])
    df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    
    df["ema20"] = ema(df.close, 20)
    df["ema50"] = ema(df.close, 50)
    df["ema200"] = ema(df.close, 200)
    df["rsi14"] = rsi(df.close, 14)
    df["atr14"] = atr(df, 14)
    df["adx14"] = adx(df, 14)
    df["atr_pct"] = df.atr14 / df.close
    df["atr_pct_med"] = df.atr_pct.rolling(100).median()
    df["regime_long"] = df.close > df.ema200
    df["regime_short"] = df.close < df.ema200
    return df

col1, col2 = st.columns(2)

for i, sym in enumerate(SYMBOLS):
    with (col1 if i == 0 else col2):
        st.header(sym)
        
        if st.button(f"Scan {sym}", key=f"btn_{sym}"):
            st.rerun()
            
        with st.spinner("Fetching live data..."):
            try:
                df = fetch_data(sym)
                current_price = df.iloc[-1]["close"]
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Current Price", f"${current_price:,.2f}")
                m2.metric("RSI (14)", f"{df.iloc[-1].rsi14:.1f}")
                m3.metric("ADX (14)", f"{df.iloc[-1].adx14:.1f}")
                
                sig = check_signal(df, len(df)-1, sym)
                
                if sig:
                    st.warning(f"⚠️ Setup Detected: {sig['side'].upper()}")
                    
                    setup_data = {
                        "side": sig["side"],
                        "rsi14": float(df.iloc[-1].rsi14),
                        "adx14": float(df.iloc[-1].adx14),
                        "ema20": float(df.iloc[-1].ema20),
                        "close": current_price
                    }
                    
                    veto = llm_veto(setup_data)
                    if veto["veto"]:
                        st.error(f"❌ Claude Vetoed: {veto['reason']}")
                    else:
                        st.success(f"✅ Claude Approved: {veto['reason']}")
                        if simulate_trade:
                            st.info(f"📝 Paper Trade Executed: Bought at ${sig['entry']:,.2f}, Stop at ${sig['stop']:,.2f}")
                            send_telegram_alert(f"🚀 TRADE ALERT ({sym})\nSide: {sig['side'].upper()}\nEntry: ${sig['entry']:,.2f}\nStop: ${sig['stop']:,.2f}")
                            
                else:
                    st.info("💤 No setup found. Waiting for pullback...")
                
                fig = go.Figure(data=[go.Candlestick(x=df['ts'],
                                open=df['open'], high=df['high'],
                                low=df['low'], close=df['close'])])
                
                fig.add_trace(go.Scatter(x=df['ts'], y=df['ema20'], line=dict(color='blue', width=1), name='EMA 20'))
                fig.add_trace(go.Scatter(x=df['ts'], y=df['ema50'], line=dict(color='orange', width=1), name='EMA 50'))
                
                fig.update_layout(height=350, margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, width='stretch')
                
            except Exception as e:
                st.error(f"Error: {e}")

st.divider()
st.caption("AI Trend-Pullback Bot v1.0 | Powered by Claude 3.5 Sonnet & Binance")
